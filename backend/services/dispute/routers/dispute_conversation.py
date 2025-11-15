"""
Multi-turn dispute resolution conversation endpoint.
"""
import logging
import re
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas import (
    DisputeAnalysisRequest,
    DisputeAnalysisResponse,
    EvidenceRequest,
    DisputeDecision
)
from services.claude_service import ClaudeService
from services.session_manager import get_session_manager
from dependencies import verify_api_key, get_claude_config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dispute",
    tags=["Dispute Resolution"]
)


def parse_agent_response(response_text: str, step: int) -> tuple[str, dict]:
    """
    Parse agent response to determine if it's requesting evidence or making a decision.
    
    Returns:
        (status, data) where status is 'needs_evidence', 'completed', or 'analyzing'
    """
    # Check for evidence requests
    if "REQUEST_EVIDENCE:USER_PROMPT" in response_text:
        return ("needs_evidence", {
            "evidence_type": "user_prompt",
            "reason": "Need to verify user's original authorization and intent",
            "fields": ["original_prompt", "authorized_budget", "product_specifications", "user_authorization"]
        })
    
    if "REQUEST_EVIDENCE:AGENT_DECISION" in response_text:
        return ("needs_evidence", {
            "evidence_type": "agent_decision",
            "reason": "Need to verify agent's decision-making process and compliance",
            "fields": ["selection_rationale", "product_details", "budget_compliance", "approval_steps"]
        })
    
    # Check for final decision
    decision_pattern = r"DECISION:\s*(APPROVE_REFUND|DENY_REFUND)\s*\|\s*CONFIDENCE:\s*([\d.]+)\s*\|\s*JUSTIFICATION:\s*(.+)"
    match = re.search(decision_pattern, response_text, re.DOTALL | re.IGNORECASE)
    
    if match:
        decision_type = match.group(1).upper()
        confidence = float(match.group(2))
        justification = match.group(3).strip()
        
        return ("completed", {
            "decision": decision_type,
            "confidence": confidence,
            "justification": justification
        })
    
    # Still analyzing
    return ("analyzing", {"message": response_text})


@router.post("/analyze", response_model=DisputeAnalysisResponse)
async def analyze_dispute_conversation(
    request: DisputeAnalysisRequest,
    api_key: Annotated[str, Depends(verify_api_key)],
    config: Annotated[dict, Depends(get_claude_config)]
) -> DisputeAnalysisResponse:
    """
    Multi-turn dispute analysis with evidence collection.
    
    This endpoint supports a conversational flow:
    1. Initial request with dispute description
    2. Agent may request additional evidence (max 2 requests)
    3. Follow-up requests provide evidence using session_id
    4. Agent makes final decision with certainty %
    
    Example initial request:
    ```json
    {
        "dispute_description": "Customer claims item not received",
        "transaction_id": "TXN-123",
        "amount": 99.99
    }
    ```
    
    Example follow-up with evidence:
    ```json
    {
        "dispute_description": "Providing requested evidence",
        "transaction_id": "TXN-123",
        "session_id": "previous-session-id",
        "additional_evidence": {
            "type": "user_prompt",
            "data": {
                "original_prompt": "Buy me headphones under $100",
                "authorized_budget": 100.00,
                ...
            }
        }
    }
    ```
    """
    session_manager = get_session_manager()
    
    try:
        # Check if this is a continuation of existing session
        if request.session_id:
            session = session_manager.get_session(request.session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {request.session_id} not found or expired"
                )
            
            if session.step >= 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum 2 follow-ups reached. Decision must be made."
                )
            
            session.increment_step()
            logger.info(f"Continuing session: {session.session_id}, step {session.step}")
            
            # Format additional evidence if provided
            if request.additional_evidence:
                evidence_type = request.additional_evidence.get("type")
                evidence_data = request.additional_evidence.get("data", {})
                
                # Format evidence as a response to the agent's request
                evidence_text = f"\n{evidence_type.upper()} EVIDENCE:\n"
                for key, value in evidence_data.items():
                    evidence_text += f"- {key}: {value}\n"
                
                prompt = f"{evidence_text}\nNow make your final decision with certainty %."
                session.add_evidence(evidence_type)
            else:
                prompt = request.dispute_description
        else:
            # New session
            session = session_manager.create_session(request.transaction_id or "unknown")
            session.increment_step()
            logger.info(f"New dispute analysis session: {session.session_id}, step {session.step}")
            
            # Check if we can get shipment evidence automatically
            shipment_evidence_text = ""
            if request.transaction_id:
                from tools.shipment_evidence import get_shipment_evidence_tool
                tool = get_shipment_evidence_tool()
                result = tool.check_delivery_status(request.transaction_id)
                if result["found"]:
                    shipment_evidence_text = f"\n\n📦 SHIPMENT EVIDENCE (already checked):\n{result['summary']}"
                    session.add_evidence("shipment_evidence")
                    logger.info(f"Auto-loaded shipment evidence for {request.transaction_id}")
            
            # Format initial prompt
            prompt = f"""DISPUTE CASE:
Transaction: {request.transaction_id or 'Not provided'}
Amount: ${request.amount or 'Not provided'}
Claim: {request.dispute_description}{shipment_evidence_text}

Make your decision with certainty %. If certainty < 70%, request additional evidence (max 2 requests)."""
        
        # Store in conversation history
        session.add_to_history("user", prompt)
        
        # Initialize Claude service
        claude_service = ClaudeService(
            max_turns=config.get("max_turns", 5),
            allowed_tools=config.get("allowed_tools", ["Read"])
        )
        
        # Get analysis with full conversation history
        analysis = await claude_service.analyze_dispute(
            dispute_description=prompt,
            transaction_id=request.transaction_id,
            amount=request.amount,
            conversation_history=session.get_history()
        )
        
        session.add_to_history("assistant", analysis)
        
        # Parse response
        status_type, data = parse_agent_response(analysis, session.step)
        
        # Build response based on status
        if status_type == "needs_evidence":
            logger.info(f"Session {session.session_id}: Requesting {data['evidence_type']} evidence")
            return DisputeAnalysisResponse(
                status="needs_evidence",
                session_id=session.session_id,
                transaction_id=request.transaction_id,
                evidence_requested=EvidenceRequest(**data),
                message=f"Additional evidence required: {data['evidence_type']}. Please provide this evidence in your next request using the session_id.",
                step=session.step
            )
        
        elif status_type == "completed":
            logger.info(f"Session {session.session_id}: Decision made - {data['decision']}")
            
            # Extract evidence types from session
            evidence_reviewed = session.evidence_collected.copy()
            if request.transaction_id:
                evidence_reviewed.append("dispute_description")
            
            # Clean up session
            session_manager.delete_session(session.session_id)
            
            return DisputeAnalysisResponse(
                status="completed",
                session_id=None,  # Session is complete
                transaction_id=request.transaction_id,
                decision=DisputeDecision(
                    decision=data["decision"],
                    confidence=data["confidence"],
                    justification=data["justification"],
                    evidence_reviewed=evidence_reviewed
                ),
                message=f"Decision: {data['decision']}",
                step=session.step
            )
        
        else:  # analyzing
            # Agent is still thinking, force a decision if at step 3
            if session.step >= 3:
                logger.warning(f"Session {session.session_id}: Max follow-ups reached, forcing decision")
                return DisputeAnalysisResponse(
                    status="completed",
                    session_id=None,
                    transaction_id=request.transaction_id,
                    decision=DisputeDecision(
                        decision="DENY_REFUND",
                        confidence=0.5,
                        justification="Insufficient evidence after 2 follow-ups. Default DENY to prevent fraud.",
                        evidence_reviewed=session.evidence_collected
                    ),
                    message="Maximum follow-ups reached. Default decision applied.",
                    step=session.step
                )
            
            # Continue analysis in next step
            return DisputeAnalysisResponse(
                status="analyzing",
                session_id=session.session_id,
                transaction_id=request.transaction_id,
                message=data["message"],
                step=session.step
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in dispute analysis: {str(e)}", exc_info=True)
        # Clean up session on error
        if request.session_id:
            session_manager.delete_session(request.session_id)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze dispute: {str(e)}"
        )


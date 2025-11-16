"""
Multi-turn dispute resolution conversation endpoint.
"""

import logging
import re
from typing import Annotated, Tuple, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas import (
    DisputeAnalysisRequest,
    DisputeAnalysisResponse,
    EvidenceRequest,
    DisputeDecision,
)
from services.claude_service import ClaudeService
from services.session_manager import get_session_manager, DisputeSession
from services.payment_service import send_refund_to_address
from dependencies import verify_api_key
from config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dispute", tags=["Dispute Resolution"])


def parse_agent_response(response_text: str, step: int) -> Tuple[str, dict]:
    """
    Parse agent response to determine if it's requesting evidence or making a decision.

    Returns:
        (status, data) where status is 'needs_evidence', 'completed', or 'analyzing'
    """
    # Check for evidence requests
    if "REQUEST_EVIDENCE:USER_PROMPT" in response_text:
        return (
            "needs_evidence",
            {
                "evidence_type": "user_prompt",
                "reason": "Need to verify user's original authorization and intent",
                "fields": [
                    "original_prompt",
                    "authorized_budget",
                    "product_specifications",
                    "user_authorization",
                ],
            },
        )

    if "REQUEST_EVIDENCE:AGENT_DECISION" in response_text:
        return (
            "needs_evidence",
            {
                "evidence_type": "agent_decision",
                "reason": "Need to verify agent's decision-making process and compliance",
                "fields": [
                    "selection_rationale",
                    "product_details",
                    "budget_compliance",
                    "approval_steps",
                ],
            },
        )

    # Check for structured decision format
    decision_pattern = r"DECISION:\s*(APPROVE_REFUND|DENY_REFUND)\s*\|\s*CONFIDENCE:\s*([\d.]+)\s*\|\s*JUSTIFICATION:\s*(.+)"
    match = re.search(decision_pattern, response_text, re.DOTALL | re.IGNORECASE)

    if match:
        decision_type = match.group(1).upper()
        confidence = float(match.group(2))
        justification = match.group(3).strip()

        return (
            "completed",
            {
                "decision": decision_type,
                "confidence": confidence,
                "justification": justification,
            },
        )

    # Check for natural language approval/denial patterns
    response_upper = response_text.upper()

    # Extract confidence/certainty percentage
    confidence_match = re.search(r"(?:CERTAINTY|CONFIDENCE).*?(\d+)%", response_text, re.IGNORECASE)
    confidence = float(confidence_match.group(1)) / 100 if confidence_match else 0.75

    # Check for approval keywords
    approval_keywords = ["APPROVED", "REFUND AUTHORIZED", "AUTHORIZE REFUND", "APPROVE REFUND"]
    denial_keywords = ["DENIED", "DENY REFUND", "REJECT"]

    is_approval = any(keyword in response_upper for keyword in approval_keywords)
    is_denial = any(keyword in response_upper for keyword in denial_keywords)

    if is_approval or is_denial:
        decision_type = "APPROVE_REFUND" if is_approval else "DENY_REFUND"
        return (
            "completed",
            {
                "decision": decision_type,
                "confidence": confidence,
                "justification": response_text[:500],  # First 500 chars as justification
            },
        )

    # Still analyzing
    return ("analyzing", {"message": response_text})


def _get_shipment_evidence(transaction_id: str) -> Optional[str]:
    """Get shipment evidence if available for transaction."""
    if not transaction_id:
        return None

    try:
        from tools.shipment_evidence import get_shipment_evidence_tool

        tool = get_shipment_evidence_tool()
        result = tool.check_delivery_status(transaction_id)

        if result["found"]:
            logger.info(f"Auto-loaded shipment evidence for {transaction_id}")
            return f"\n\n📦 SHIPMENT EVIDENCE (already checked):\n{result['summary']}"
    except Exception as e:
        logger.warning(f"Failed to load shipment evidence: {e}")

    return None


def _format_evidence_prompt(evidence_type: str, evidence_data: dict) -> str:
    """Format evidence data into a prompt."""
    evidence_text = f"\n{evidence_type.upper()} EVIDENCE:\n"
    for key, value in evidence_data.items():
        evidence_text += f"- {key}: {value}\n"
    return f"{evidence_text}\nNow make your final decision with certainty %."


def _format_initial_prompt(
    request: DisputeAnalysisRequest, shipment_evidence: Optional[str]
) -> str:
    """Format the initial dispute prompt."""
    shipment_text = shipment_evidence or ""
    return f"""DISPUTE CASE:
Transaction: {request.transaction_id or "Not provided"}
Amount: ${request.amount or "Not provided"}
Claim: {request.dispute_description}{shipment_text}

Make your decision with certainty %. If certainty < 70%, request additional evidence (max 2 requests)."""


def _build_needs_evidence_response(
    session: DisputeSession, request: DisputeAnalysisRequest, data: dict
) -> DisputeAnalysisResponse:
    """Build response when agent needs more evidence."""
    logger.info(
        f"Session {session.session_id}: Requesting {data['evidence_type']} evidence"
    )
    return DisputeAnalysisResponse(
        status="needs_evidence",
        session_id=session.session_id,
        transaction_id=request.transaction_id,
        evidence_requested=EvidenceRequest(**data),
        decision=None,
        message=f"Additional evidence required: {data['evidence_type']}. Please provide this evidence in your next request using the session_id.",
        step=session.step,
    )


async def _build_completed_response(
    session: DisputeSession,
    request: DisputeAnalysisRequest,
    data: dict,
    session_manager,
) -> DisputeAnalysisResponse:
    """Build response when agent has made a decision."""
    logger.info(f"Session {session.session_id}: Decision made - {data['decision']}")

    payment_result = None

    should_process_refund = (
        data["decision"] == "APPROVE_REFUND" and
        session.step < 3 and
        request.amount and
        request.recipient_address and
        request.transaction_id
    )

    if should_process_refund:
        try:
            logger.info(f"Processing automatic refund for session {session.session_id}")
            settings = get_settings()
            payment_result = await send_refund_to_address(
                address=request.recipient_address,  # type: ignore
                amount=request.amount,  # type: ignore
                transaction_id=request.transaction_id,  # type: ignore
                settings=settings
            )
            logger.info(f"Refund processed successfully: {payment_result}")
        except Exception as e:
            logger.error(f"Failed to process refund: {str(e)}", exc_info=True)

    evidence_reviewed = session.evidence_collected.copy()
    if request.transaction_id:
        evidence_reviewed.append("dispute_description")

    session_manager.delete_session(session.session_id)

    message = f"Decision: {data['decision']}"
    if payment_result:
        message += f" - Refund sent successfully"

    return DisputeAnalysisResponse(
        status="completed",
        session_id=None,
        transaction_id=request.transaction_id,
        evidence_requested=None,
        decision=DisputeDecision(
            decision=data["decision"],
            confidence=data["confidence"],
            justification=data["justification"],
            evidence_reviewed=evidence_reviewed,
        ),
        message=message,
        step=session.step
    )


def _build_default_decision_response(
    session: DisputeSession, request: DisputeAnalysisRequest
) -> DisputeAnalysisResponse:
    """Build default denial response when max steps reached."""
    logger.warning(
        f"Session {session.session_id}: Max follow-ups reached, forcing decision"
    )
    return DisputeAnalysisResponse(
        status="completed",
        session_id=None,
        transaction_id=request.transaction_id,
        evidence_requested=None,
        decision=DisputeDecision(
            decision="DENY_REFUND",
            confidence=0.5,
            justification="Insufficient evidence after 2 follow-ups. Default DENY to prevent fraud.",
            evidence_reviewed=session.evidence_collected,
        ),
        message="Maximum follow-ups reached. Default decision applied.",
        step=session.step,
    )


@router.post("/analyze", response_model=DisputeAnalysisResponse)
async def analyze_dispute_conversation(
    request: DisputeAnalysisRequest, api_key: Annotated[str, Depends(verify_api_key)]
) -> DisputeAnalysisResponse:
    """
    Multi-turn dispute analysis with evidence collection.

    Flow:
    1. Initial request with dispute description
    2. Agent may request additional evidence (max 2 requests)
    3. Follow-up requests provide evidence using session_id
    4. Agent makes final decision with certainty %
    """
    session_manager = get_session_manager()

    try:
        # Handle existing or new session
        if request.session_id:
            session = session_manager.get_session(request.session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {request.session_id} not found or expired",
                )

            if session.step >= 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum 2 follow-ups reached. Decision must be made.",
                )

            session.increment_step()
            logger.info(
                f"Continuing session: {session.session_id}, step {session.step}"
            )

            # Format evidence if provided
            if request.additional_evidence:
                evidence_type = request.additional_evidence.get("type", "unknown")
                evidence_data = request.additional_evidence.get("data", {})
                prompt = _format_evidence_prompt(evidence_type, evidence_data)
                session.add_evidence(evidence_type)
            else:
                prompt = request.dispute_description
        else:
            # Create new session
            session = session_manager.create_session(
                request.transaction_id or "unknown"
            )
            session.increment_step()
            logger.info(
                f"New dispute analysis session: {session.session_id}, step {session.step}"
            )

            # Check for shipment evidence
            shipment_evidence = _get_shipment_evidence(request.transaction_id or "")
            if shipment_evidence:
                session.add_evidence("shipment_evidence")


            prompt = _format_initial_prompt(request, shipment_evidence)

        # Get Claude analysis
        claude_service = ClaudeService()

        # Convert images to dict format if provided (only for new sessions)
        images_dict = None
        history_to_use = None

        if request.images and not request.session_id:
            # New session with images - don't use history yet, build message with images
            images_dict = [
                {"data": img.data, "mediaType": img.mediaType} for img in request.images
            ]
            logger.info(f"Processing {len(images_dict)} image(s) with dispute")
            session.add_evidence("images")
        else:
            # Store in conversation history and use it (for continuing sessions or new without images)
            session.add_to_history("user", prompt)
            history_to_use = session.get_history()

        analysis = await claude_service.analyze_dispute(
            dispute_description=prompt,
            transaction_id=request.transaction_id or "",
            amount=request.amount or 0.0,
            conversation_history=session.get_history()
        )

        # Now store the message in history if it wasn't already (new session with images)
        if images_dict:
            session.add_to_history("user", prompt)

        session.add_to_history("assistant", analysis)

        # Parse and route response
        status_type, data = parse_agent_response(analysis, session.step)

        if status_type == "needs_evidence":
            return _build_needs_evidence_response(session, request, data)


        elif status_type == "completed":
            return await _build_completed_response(session, request, data, session_manager)
        
        else:  # analyzing
            # Check if message contains strong approval signal (for backward compatibility)
            message_upper = data["message"].upper()
            has_approval = any(
                keyword in message_upper
                for keyword in ["APPROVED", "REFUND AUTHORIZED", "AUTHORIZE REFUND"]
            )

            # Extract confidence from message
            confidence_match = re.search(r"(?:CERTAINTY|CONFIDENCE).*?(\d+)%", data["message"], re.IGNORECASE)
            confidence = float(confidence_match.group(1)) / 100 if confidence_match else 0.0

            # If high confidence approval detected in analyzing message, process as refund
            if has_approval and confidence >= 0.70 and session.step < 3 and request.amount and request.recipient_address and request.transaction_id:
                logger.info(f"Detected high-confidence approval in analyzing message (confidence: {confidence})")
                try:
                    settings = get_settings()
                    payment_result = await send_refund_to_address(
                        address=request.recipient_address,  # type: ignore
                        amount=request.amount,  # type: ignore
                        transaction_id=request.transaction_id,  # type: ignore
                        settings=settings
                    )
                    logger.info(f"Refund processed from analyzing state: {payment_result}")

                    # Return as analyzing but note refund was processed
                    return DisputeAnalysisResponse(
                        status="analyzing",
                        session_id=session.session_id,
                        transaction_id=request.transaction_id,
                        evidence_requested=None,
                        decision=None,
                        message=f"{data['message']}\n\n✅ Refund of ${request.amount} automatically processed to {request.recipient_address}",
                        step=session.step,
                    )
                except Exception as e:
                    logger.error(f"Failed to process refund from analyzing state: {str(e)}", exc_info=True)

            if session.step >= 3:
                return _build_default_decision_response(session, request)

            return DisputeAnalysisResponse(
                status="analyzing",
                session_id=session.session_id,
                transaction_id=request.transaction_id,
                evidence_requested=None,
                decision=None,
                message=data["message"],
                step=session.step,
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
            detail=f"Failed to analyze dispute: {str(e)}",
        )

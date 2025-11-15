"""
API routes for Claude Agent SDK endpoints.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import DisputeAnalysisRequest, DisputeAnalysisResponse
from services.claude_service import ClaudeService
from dependencies import verify_api_key, get_claude_config


router = APIRouter(
    prefix="/claude",
    tags=["Claude Agent"]
)


@router.post("/analyze-dispute", response_model=DisputeAnalysisResponse)
async def analyze_dispute(
    request: DisputeAnalysisRequest,
    api_key: Annotated[str, Depends(verify_api_key)],
    config: Annotated[dict, Depends(get_claude_config)]
) -> DisputeAnalysisResponse:
    """
    Analyze a dispute using Claude Agent SDK.
    
    This endpoint uses Claude Agent SDK with custom MCP tools to analyze
    disputes and provide intelligent recommendations.
    
    Args:
        request: Dispute analysis request with description and optional details
        api_key: Verified Anthropic API key (injected)
        config: Claude configuration (injected)
        
    Returns:
        DisputeAnalysisResponse: Analysis results from Claude
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        # Initialize Claude service with config
        claude_service = ClaudeService(
            max_turns=config.get("max_turns", 5),
            allowed_tools=config.get("allowed_tools", ["Read"])
        )
        
        # Perform analysis
        analysis = await claude_service.analyze_dispute(
            dispute_description=request.dispute_description,
            transaction_id=request.transaction_id,
            amount=request.amount
        )
        
        return DisputeAnalysisResponse(
            analysis=analysis,
            transaction_id=request.transaction_id,
            status="completed"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze dispute: {str(e)}"
        )


@router.post("/query")
async def query_claude(
    prompt: str,
    api_key: Annotated[str, Depends(verify_api_key)],
    config: Annotated[dict, Depends(get_claude_config)]
) -> dict:
    """
    Send a simple query to Claude Agent.
    
    This is a basic endpoint to test Claude Agent SDK integration
    without custom tools.
    
    Args:
        prompt: The prompt to send to Claude
        api_key: Verified Anthropic API key (injected)
        config: Claude configuration (injected)
        
    Returns:
        dict: Response from Claude
        
    Raises:
        HTTPException: If query fails
    """
    try:
        claude_service = ClaudeService(
            max_turns=1,
            allowed_tools=[]
        )
        
        response = await claude_service.simple_query(prompt)
        
        return {
            "prompt": prompt,
            "response": response,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query Claude: {str(e)}"
        )


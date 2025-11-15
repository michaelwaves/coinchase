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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 Received dispute analysis request")
        logger.info(f"Transaction ID: {request.transaction_id}")
        logger.info(f"Amount: {request.amount}")
        logger.info(f"Description length: {len(request.dispute_description)} chars")
        logger.info(f"Config: {config}")
        
        # Initialize Claude service with config
        logger.info("Initializing Claude service")
        claude_service = ClaudeService(
            max_turns=config.get("max_turns", 5),
            allowed_tools=config.get("allowed_tools", ["Read"])
        )
        logger.info("Claude service initialized")
        
        # Perform analysis
        logger.info("Calling claude_service.analyze_dispute")
        analysis = await claude_service.analyze_dispute(
            dispute_description=request.dispute_description,
            transaction_id=request.transaction_id,
            amount=request.amount
        )
        logger.info(f"Analysis completed, length: {len(analysis)} chars")
        
        response = DisputeAnalysisResponse(
            analysis=analysis,
            transaction_id=request.transaction_id,
            status="completed"
        )
        logger.info("✅ Returning successful response")
        return response
        
    except Exception as e:
        logger.error("❌ Exception in analyze_dispute endpoint")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error("Full traceback:", exc_info=True)
        
        # Try to extract more details from the exception
        import traceback
        tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        logger.error(f"Detailed traceback:\n{tb_str}")
        
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


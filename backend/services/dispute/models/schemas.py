"""
Pydantic models for request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class DisputeAnalysisRequest(BaseModel):
    """Request model for dispute analysis."""
    
    dispute_description: str = Field(
        ...,
        description="Description of the dispute to analyze",
        min_length=10,
        max_length=5000
    )
    transaction_id: Optional[str] = Field(
        None,
        description="Optional transaction ID associated with the dispute"
    )
    amount: Optional[float] = Field(
        None,
        description="Disputed amount",
        ge=0
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID for multi-turn conversation"
    )
    additional_evidence: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional evidence provided in response to agent request"
    )


class EvidenceRequest(BaseModel):
    """Model for evidence requested by agent."""
    
    evidence_type: str = Field(..., description="Type of evidence requested")
    reason: str = Field(..., description="Why this evidence is needed")
    fields: List[str] = Field(..., description="Specific fields requested")


class DisputeDecision(BaseModel):
    """Model for final dispute decision."""
    
    decision: str = Field(..., description="APPROVE_REFUND or DENY_REFUND")
    confidence: float = Field(..., description="Confidence level 0-1", ge=0, le=1)
    justification: str = Field(..., description="Detailed justification for decision")
    evidence_reviewed: List[str] = Field(..., description="Types of evidence reviewed")


class DisputeAnalysisResponse(BaseModel):
    """Response model for dispute analysis."""
    
    status: str = Field(..., description="Status: needs_evidence, completed, or error")
    session_id: Optional[str] = Field(None, description="Session ID for continuing conversation")
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID")
    
    # For needs_evidence status
    evidence_requested: Optional[EvidenceRequest] = Field(None, description="Evidence being requested")
    
    # For completed status
    decision: Optional[DisputeDecision] = Field(None, description="Final decision on dispute")
    
    # General
    message: str = Field(..., description="Message to display")
    step: int = Field(default=1, description="Current step in the process (1-3)")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(default="healthy")
    service: str
    version: str

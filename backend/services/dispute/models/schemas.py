"""
Pydantic models for request/response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional


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


class DisputeAnalysisResponse(BaseModel):
    """Response model for dispute analysis."""
    
    analysis: str = Field(..., description="Claude's analysis of the dispute")
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID")
    status: str = Field(default="completed", description="Status of the analysis")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(default="healthy")
    service: str
    version: str


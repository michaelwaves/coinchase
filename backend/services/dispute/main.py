"""
Main FastAPI application for Dispute Service.
"""
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated

from config import Settings, get_settings
from models.schemas import HealthResponse
from routers import claude

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Set specific loggers to DEBUG for more detail
logging.getLogger('services.claude_service').setLevel(logging.DEBUG)
logging.getLogger('tools.shipment_evidence').setLevel(logging.DEBUG)
logging.getLogger('routers.claude').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.info("🚀 Starting Dispute Service application")

# Initialize FastAPI app
app = FastAPI(
    title="Dispute Service",
    description="AI-powered dispute analysis service using Claude Agent SDK",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
logger.info("FastAPI app initialized")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(claude.router)
logger.info("Routers registered successfully")


@app.get("/", response_model=HealthResponse)
async def root(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """
    Root endpoint - Health check.
    
    Returns:
        HealthResponse: Service health status
    """
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version
    )


@app.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)]
) -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Service health status
    """
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ping")
async def ping():
    logger.info("Ping endpoint called")
    return {"status": "pong"}


@router.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {
        "status": "healthy",
        "service": "URL Shortener"
    }


@router.get("/health/ready")
async def readiness_check():
    logger.info("Readiness check endpoint called")
    return {
        "ready": True
    }
import logging

from fastapi import APIRouter


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/ping")
async def ping() -> str:
    logger.debug("Ping endpoint called")
    return "pong"


@router.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy", "service": "URL Shortener"}

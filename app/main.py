import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes import health, links


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down application")


app = FastAPI(
    title="URL Shortener", description="URL Shortener Service", version="1.0.0", lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])

app.include_router(links.router, prefix="/api", tags=["links"])


@app.get("/", tags=["root"])
async def root():
    logger.info("Root endpoint called")
    return {"message": "Welcome to URL Shortener", "version": "1.0.0", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Uvicorn server")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

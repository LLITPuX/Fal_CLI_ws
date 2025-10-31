"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting Gemini Text Structurer API")
    logger.info(f"Gemini CLI: {settings.gemini_cli}")
    logger.info(f"Gemini Model: {settings.gemini_model}")
    logger.info(f"Output Directory: {settings.default_output_dir}")
    yield
    # Shutdown
    logger.info("Shutting down Gemini Text Structurer API")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(router, tags=["gemini"])

# Root endpoint
@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint with API info.

    Returns:
        API information
    """
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
    }


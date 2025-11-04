"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.api.falkordb_routes import router as falkordb_router
from app.api.template_routes import router as template_router
from app.core.config import settings
from app.db.falkordb.client import close_falkordb_client, init_falkordb_client
from app.services.template_loader import load_default_templates

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
    
    # Initialize FalkorDB
    try:
        client = await init_falkordb_client()
        logger.info(
            f"FalkorDB initialized: {settings.falkordb_host}:"
            f"{settings.falkordb_port}/{settings.falkordb_graph_name}"
        )
        
        # Load default templates
        await load_default_templates(client)
    except Exception as e:
        logger.error(f"Failed to initialize FalkorDB: {e}", exc_info=True)
        logger.warning("Continuing without FalkorDB support")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Gemini Text Structurer API")
    await close_falkordb_client()
    logger.info("FalkorDB connection closed")


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
app.include_router(falkordb_router, prefix="/api")
app.include_router(template_router, prefix="/api")

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


"""FastAPI application entrypoint."""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.agents.clerk.repository import MessageRepository
from app.agents.cursor.repository import CursorRepository
from app.agents.cursor.nodes import cursor_record_node
from app.agents.graph import init_chat_workflow
from app.agents.subconscious.repository import SubconsciousRepository
from app.api import router
from app.api.chat_routes import router as chat_router
from app.api.cursor_routes import router as cursor_router
from app.api.falkordb_routes import router as falkordb_router
from app.api.template_routes import router as template_router
from app.core.config import settings
from app.db.falkordb.client import close_falkordb_client, init_falkordb_client, get_falkordb_client
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
        
        # Initialize LangGraph workflow for chat agents
        clerk_repo = MessageRepository(client)
        subconscious_repo = SubconsciousRepository(client)
        init_chat_workflow(clerk_repo, subconscious_repo)
        logger.info("🤖 Multi-agent chat system (Phase 2: Clerk + Subconscious) initialized")
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

# Auto-Recording Middleware (Phase 2 - Simplified)
# Note: Full implementation with request/response capture requires more complex logic
@app.middleware("http")
async def cursor_recording_middleware(request: Request, call_next):
    """
    Simplified auto-recording middleware for Cursor Agent.
    
    Phase 2: Basic logging only
    Phase 3: Will extract request/response data and call cursor_record_node()
    
    Only processes API routes (not static files).
    Gracefully handles errors to never fail main request.
    """
    # Skip non-API routes
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
    
    # Skip cursor's own endpoints to avoid recursion
    if request.url.path.startswith("/api/cursor/"):
        return await call_next(request)
    
    start_time = time.time()
    
    # Process request normally
    response = await call_next(request)
    
    # Log the interaction (Phase 2 - simplified)
    if settings.cursor_auto_record:
        try:
            execution_time = (time.time() - start_time) * 1000
            logger.info(
                f"📝 Cursor: API call logged: "
                f"{request.method} {request.url.path} "
                f"({execution_time:.2f}ms)"
            )
            
            # Phase 3 TODO: Extract request/response data and call cursor_record_node()
            # For now, just logging the activity
            
        except Exception as e:
            # CRITICAL: Don't fail main request!
            logger.error(f"📝 Cursor: Recording middleware error: {e}")
    
    return response

# Include routers
app.include_router(router, tags=["gemini"])
app.include_router(falkordb_router, prefix="/api")
app.include_router(template_router, prefix="/api")
app.include_router(chat_router, prefix="/api")  # Cybersich chat system
app.include_router(cursor_router)  # Cursor development agent (includes /api prefix)

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


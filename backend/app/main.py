"""FastAPI application entrypoint."""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.agents.clerk.repository import MessageRepository
from app.agents.cursor.repository import CursorRepository
from app.agents.cursor.nodes import cursor_record_node
from app.agents.graph import init_chat_workflow
from app.agents.subconscious.repository import SubconsciousRepository
from app.api import router
from app.api.archive_routes import router as archive_router
from app.api.chat_routes import router as chat_router
from app.api.cursor_routes import router as cursor_router
from app.api.falkordb_routes import router as falkordb_router
from app.api.template_routes import router as template_router
from app.core.config import settings
from app.db.falkordb.client import close_falkordb_client, init_falkordb_client, get_falkordb_client
from app.services.template_loader import load_default_templates
from app.services.document_type_loader import load_default_document_types

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def _auto_load_rules_if_needed(client):
    """Auto-load rules into Knowledge Base if it doesn't exist.
    
    Args:
        client: FalkorDB client instance (for main graph)
    """
    try:
        # Create separate client for cursor_memory graph
        from app.db.falkordb.client import FalkorDBClient
        
        cursor_client = FalkorDBClient(
            host=settings.falkordb_host,
            port=settings.falkordb_port,
            graph_name="cursor_memory",
            max_query_time=60
        )
        
        try:
            await cursor_client.connect()
        except Exception as e:
            logger.error(f"Failed to connect to cursor_memory graph: {e}")
            return
        
        try:
            # Check if Knowledge Base exists and has documents
            kb_id = "cursor_rules_v3"
            cypher = """
            MATCH (kb:KnowledgeBase {id: $kb_id})
            OPTIONAL MATCH (kb)<-[:IN_BASE]-(d:Document)
            RETURN kb, count(d) as doc_count
            """
            results, _ = await cursor_client.query(cypher, {"kb_id": kb_id})
            
            if len(results) > 0:
                doc_count = results[0].get("doc_count", 0)
                if doc_count > 0:
                    logger.info(f"📚 Knowledge Base already exists with {doc_count} documents. Skipping auto-load.")
                    return
                else:
                    logger.info("📚 Knowledge Base exists but has no documents. Will load rules.")
            
            logger.info("📚 Knowledge Base is empty. Auto-loading rules...")
            
            # Check if manifest exists
            manifest_path = Path("/app/scripts/rules_manifest.json")
            logger.debug(f"Checking manifest at: {manifest_path}")
            
            if not manifest_path.exists():
                # Try alternative path (for local development)
                manifest_path = Path("backend/scripts/rules_manifest.json")
                logger.debug(f"Trying alternative path: {manifest_path}")
                if not manifest_path.exists():
                    logger.warning(
                        f"⚠️  Manifest not found at /app/scripts/rules_manifest.json or {manifest_path}. "
                        "Run validate_rules.py first to generate manifest."
                    )
                    return
            
            logger.info(f"📄 Found manifest at: {manifest_path}")
            
            # Load manifest
            try:
                manifest_content = manifest_path.read_text(encoding="utf-8")
                manifest = json.loads(manifest_content)
                logger.debug(f"Manifest loaded: {len(manifest)} entries")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse manifest JSON: {e}")
                return
            except Exception as e:
                logger.error(f"Failed to load manifest: {e}", exc_info=True)
                return
            
            if not manifest:
                logger.warning("⚠️  Manifest is empty. No rules to load.")
                return
            
            logger.info(f"📚 Found {len(manifest)} files to load")
            
            # Import loader class (need to add scripts to path)
            scripts_path = Path("/app/scripts")
            if not scripts_path.exists():
                scripts_path = Path("backend/scripts")
            
            logger.debug(f"Scripts path: {scripts_path}, exists: {scripts_path.exists()}")
            
            if scripts_path.exists():
                sys.path.insert(0, str(scripts_path))
            
            try:
                logger.info("📦 Importing KnowledgeBaseLoader...")
                from load_rules_to_kb import KnowledgeBaseLoader
                
                # Create loader instance
                loader = KnowledgeBaseLoader()
                
                # Use cursor_memory client
                loader.client = cursor_client
                
                logger.info("🚀 Starting rules loading...")
                # Load all rules (without force_reload to avoid clearing if something exists)
                success = await loader.load_all(force_reload=False)
                
                if success:
                    logger.info("✅ Rules loaded successfully!")
                else:
                    logger.warning("⚠️  Some rules failed to load. Check logs above.")
                    if loader.stats.get("errors"):
                        for error in loader.stats["errors"][:5]:  # Show first 5 errors
                            logger.error(f"  - {error}")
                    
            except ImportError as e:
                logger.error(f"Failed to import KnowledgeBaseLoader: {e}", exc_info=True)
                logger.warning("⚠️  Skipping auto-load. Install required dependencies.")
            except Exception as e:
                logger.error(f"Unexpected error during rules loading: {e}", exc_info=True)
            finally:
                # Remove from path
                if str(scripts_path) in sys.path:
                    sys.path.remove(str(scripts_path))
        finally:
            # Disconnect cursor_memory client
            try:
                await cursor_client.disconnect()
            except Exception:
                pass
                
    except Exception as e:
        logger.error(f"Failed to auto-load rules: {e}", exc_info=True)
        # Don't fail startup if auto-load fails
        logger.warning("⚠️  Continuing startup without auto-loaded rules.")


async def _auto_index_codebase_if_needed(client):
    """Auto-index codebase into Knowledge Base if not already indexed.
    
    Args:
        client: FalkorDB client instance (for main graph)
    """
    try:
        # Create separate client for cursor_memory graph
        from app.db.falkordb.client import FalkorDBClient
        
        cursor_client = FalkorDBClient(
            host=settings.falkordb_host,
            port=settings.falkordb_port,
            graph_name="cursor_memory",
            max_query_time=60
        )
        
        try:
            await cursor_client.connect()
        except Exception as e:
            logger.error(f"Failed to connect to cursor_memory graph: {e}")
            return
        
        try:
            # Check if Knowledge Base exists
            kb_id = "cursor_rules_v3"
            cypher = """
            MATCH (kb:KnowledgeBase {id: $kb_id})
            RETURN kb
            """
            results, _ = await cursor_client.query(cypher, {"kb_id": kb_id})
            
            if len(results) == 0:
                logger.info("📚 Knowledge Base not found. Skipping codebase indexing (load rules first).")
                return
            
            # Check if code already indexed
            cypher = """
            MATCH (kb:KnowledgeBase {id: $kb_id})<-[:IN_BASE]-(cf:CodeFile)
            RETURN count(cf) as file_count
            """
            results, _ = await cursor_client.query(cypher, {"kb_id": kb_id})
            file_count = results[0].get("file_count", 0) if results else 0
            
            if file_count > 0:
                logger.info(f"💻 Codebase already indexed ({file_count} files). Skipping auto-index.")
                return
            
            logger.info("💻 Codebase not indexed. Auto-indexing Python files...")
            
            # Import indexer class (need to add scripts to path)
            scripts_path = Path("/app/scripts")
            if not scripts_path.exists():
                scripts_path = Path("backend/scripts")
            
            logger.debug(f"Scripts path: {scripts_path}, exists: {scripts_path.exists()}")
            
            if scripts_path.exists():
                sys.path.insert(0, str(scripts_path))
            
            try:
                logger.info("📦 Importing CodebaseIndexer...")
                from index_codebase import CodebaseIndexer
                
                # Create indexer instance
                codebase_path = "/app/app"  # Container path
                if not Path(codebase_path).exists():
                    codebase_path = "backend/app"  # Local path
                
                indexer = CodebaseIndexer(codebase_path=codebase_path)
                
                # Use cursor_memory client
                indexer.client = cursor_client
                
                logger.info("🚀 Starting codebase indexing...")
                # Index all files (without force_reload to avoid clearing if something exists)
                success = await indexer.index_all(force_reload=False)
                
                if success:
                    logger.info(f"✅ Codebase indexed successfully! ({indexer.stats['files_indexed']} files, {indexer.stats['functions_indexed']} functions)")
                else:
                    logger.warning("⚠️  Some files failed to index. Check logs above.")
                    if indexer.stats.get("errors"):
                        for error in indexer.stats["errors"][:5]:  # Show first 5 errors
                            logger.error(f"  - {error}")
                    
            except ImportError as e:
                logger.error(f"Failed to import CodebaseIndexer: {e}", exc_info=True)
                logger.warning("⚠️  Skipping auto-index. Install required dependencies.")
            except Exception as e:
                logger.error(f"Unexpected error during codebase indexing: {e}", exc_info=True)
            finally:
                # Remove from path
                if str(scripts_path) in sys.path:
                    sys.path.remove(str(scripts_path))
        finally:
            # Disconnect cursor_memory client
            try:
                await cursor_client.disconnect()
            except Exception:
                pass
                
    except Exception as e:
        logger.error(f"Failed to auto-index codebase: {e}", exc_info=True)
        # Don't fail startup if auto-index fails
        logger.warning("⚠️  Continuing startup without auto-indexed codebase.")


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
        
        # Auto-load rules if Knowledge Base is empty (async, non-blocking)
        # Run in background to avoid blocking startup
        # DISABLED: Auto-load rules
        # asyncio.create_task(_auto_load_rules_if_needed(client))
        
        # Auto-index codebase if not already indexed (async, non-blocking)
        # DISABLED: Auto-index codebase
        # asyncio.create_task(_auto_index_codebase_if_needed(client))
        
        # Load default templates
        await load_default_templates(client)
        
        # Initialize default document types
        await load_default_document_types(client)
        
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
app.include_router(archive_router, prefix="/api")  # Document archiver system
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


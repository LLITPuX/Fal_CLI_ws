"""API routes for Cursor Agent - development session management."""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.agents.cursor.repository import CursorRepository
from app.agents.cursor.schemas import (
    EndSessionRequest,
    SessionHistoryResponse,
    SessionListResponse,
    SessionResponse,
    StartSessionRequest,
)
from app.db.falkordb.client import FalkorDBClient, get_falkordb_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cursor", tags=["cursor"])


def get_cursor_repository(
    client: FalkorDBClient = Depends(get_falkordb_client),
) -> CursorRepository:
    """Get CursorRepository instance."""
    return CursorRepository(client)


@router.post("/session/start", response_model=SessionResponse)
async def start_session(
    request: StartSessionRequest,
    repository: CursorRepository = Depends(get_cursor_repository),
):
    """
    Start new development session.
    
    Creates new DevelopmentSession in cursor_memory graph.
    """
    try:
        # Check if already active session
        active = await repository.get_active_session()
        if active:
            logger.warning(f"Session already active: {active['id']}")
            raise HTTPException(
                status_code=400,
                detail=f"Session already active: {active['id']}. End it first or use existing."
            )
        
        # Create new session
        session_id = await repository.create_session(
            mode=request.mode,
            git_branch=request.git_branch,
            git_commit=request.git_commit,
            project_path=request.project_path,
        )
        
        logger.info(f"✅ Cursor: Started session {session_id}")
        
        return SessionResponse(
            session_id=session_id,
            status="active",
            backup_file=None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start session: {str(e)}"
        )


@router.post("/session/end", response_model=SessionResponse)
async def end_session(
    request: EndSessionRequest,
    repository: CursorRepository = Depends(get_cursor_repository),
):
    """
    End development session and trigger backup.
    
    Marks session as completed and exports to JSON if requested.
    """
    try:
        # End session
        await repository.end_session(request.session_id)
        
        backup_file = None
        
        # Backup to JSON
        if request.backup_to_git:
            backup_file = await backup_session_to_json(
                request.session_id,
                repository
            )
        
        logger.info(f"✅ Cursor: Ended session {request.session_id}")
        
        return SessionResponse(
            session_id=request.session_id,
            status="completed",
            backup_file=str(backup_file) if backup_file else None,
        )
        
    except Exception as e:
        logger.error(f"Failed to end session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to end session: {str(e)}"
        )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    limit: int = 10,
    status: str | None = None,
    repository: CursorRepository = Depends(get_cursor_repository),
):
    """
    List development sessions.
    
    Query params:
        - limit: Max sessions to return (default 10)
        - status: Filter by status (active/completed/interrupted)
    """
    try:
        sessions = await repository.get_sessions(status=status, limit=limit)
        
        logger.info(f"✅ Cursor: Retrieved {len(sessions)} sessions")
        
        return SessionListResponse(
            sessions=sessions,
            total=len(sessions),
        )
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/session/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    limit: int = 50,
    repository: CursorRepository = Depends(get_cursor_repository),
):
    """
    Get query/response history for session.
    
    Path params:
        - session_id: Session ID
    Query params:
        - limit: Max items to return (default 50)
    """
    try:
        history = await repository.get_session_history(session_id, limit)
        
        logger.info(
            f"✅ Cursor: Retrieved {len(history)} history items "
            f"for session {session_id}"
        )
        
        return SessionHistoryResponse(
            session_id=session_id,
            history=history,
            total_items=len(history),
        )
        
    except Exception as e:
        logger.error(f"Failed to get session history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session history: {str(e)}"
        )


@router.get("/health")
async def cursor_health_check(
    repository: CursorRepository = Depends(get_cursor_repository),
):
    """Health check for Cursor Agent."""
    try:
        healthy = await repository.health_check()
        
        if healthy:
            return {"status": "healthy", "graph": "cursor_memory"}
        else:
            raise HTTPException(
                status_code=503,
                detail="Cursor Agent unhealthy - cannot access cursor_memory graph"
            )
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )


# Helper functions

async def backup_session_to_json(
    session_id: str,
    repository: CursorRepository,
) -> Path | None:
    """
    Export session to JSON file for git tracking.
    
    Args:
        session_id: Session ID to backup
        repository: CursorRepository instance
        
    Returns:
        Path to backup file or None if failed
    """
    try:
        # Get session with full history
        cypher = """
        MATCH (s:DevelopmentSession {id: $session_id})
        MATCH (s)<-[:IN_SESSION]-(q:UserQuery)
        MATCH (q)<-[:ANSWERS]-(r:AssistantResponse)
        RETURN s, collect({query: q, response: r}) as interactions
        """
        
        results, _ = await repository.client.query(cypher, {"session_id": session_id})
        
        if not results:
            logger.warning(f"Session {session_id} not found for backup")
            return None
        
        session_data = {
            "session": results[0]["s"],
            "interactions": results[0]["interactions"],
            "exported_at": Path(__file__).stat().st_mtime,
        }
        
        # Write to file
        backup_dir = Path("backups/cursor_memory/exports/sessions")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_file = backup_dir / f"{session_id}.json"
        backup_file.write_text(
            json.dumps(session_data, indent=2, ensure_ascii=False, default=str)
        )
        
        logger.info(f"📝 Cursor: Session backed up to {backup_file}")
        
        return backup_file
        
    except Exception as e:
        logger.error(f"Failed to backup session: {e}", exc_info=True)
        return None


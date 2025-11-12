"""Cursor Agent node functions for recording development sessions."""

import logging
import time

from app.agents.cursor.repository import CursorRepository

logger = logging.getLogger(__name__)


async def cursor_record_node(
    state: dict,
    repository: CursorRepository,
) -> dict:
    """
    Record development interaction to cursor_memory graph.
    
    Called automatically after each request/response cycle in Cursor.
    
    Args:
        state: Current state with query/response data
        repository: CursorRepository instance
        
    Returns:
        Updated state with recording results
        
    State Schema:
        Input:
            - user_query: str (required)
            - assistant_response: str (required)
            - mode: str (agent/ask/plan)
            - intent: str | None
            - tools_used: list[str]
            - files_modified: list[str]
            - success: bool
            - git_branch: str | None
            - git_commit: str | None
            - project_path: str
            
        Output:
            - cursor_recorded: bool
            - cursor_query_id: str | None
            - cursor_response_id: str | None
            - cursor_session_id: str | None
            - error: str | None
    """
    logger.info("📝 Cursor: Recording development interaction...")
    start_time = time.time()
    
    try:
        # 1. Get or create active session
        session = await repository.get_active_session()
        
        if not session:
            # Auto-create session
            logger.info("📝 Cursor: No active session, creating new one...")
            session_id = await repository.create_session(
                mode=state.get("mode", "agent"),
                git_branch=state.get("git_branch"),
                git_commit=state.get("git_commit"),
                project_path=state.get("project_path", ""),
            )
        else:
            session_id = session["id"]
            logger.info(f"📝 Cursor: Using existing session {session_id}")
        
        # 2. Record user query
        query_id = await repository.create_user_query(
            content=state["user_query"],
            session_id=session_id,
            mode=state.get("mode", "agent"),
            intent=state.get("intent"),
            mentioned_files=state.get("mentioned_files", []),
        )
        
        # 3. Record assistant response
        response_id = await repository.create_assistant_response(
            content=state["assistant_response"],
            query_id=query_id,
            tools_used=state.get("tools_used", []),
            files_modified=state.get("files_modified", []),
            files_created=state.get("files_created", []),
            files_deleted=state.get("files_deleted", []),
            success=state.get("success", True),
            execution_time_ms=(time.time() - start_time) * 1000,
        )
        
        # 4. Update state
        state["cursor_recorded"] = True
        state["cursor_query_id"] = query_id
        state["cursor_response_id"] = response_id
        state["cursor_session_id"] = session_id
        state["error"] = None
        
        logger.info(
            f"📝 Cursor: Successfully recorded interaction "
            f"(session={session_id}, query={query_id}, response={response_id})"
        )
        
    except Exception as e:
        logger.error(f"📝 Cursor: Failed to record: {e}", exc_info=True)
        
        # CRITICAL: Don't fail main request!
        state["cursor_recorded"] = False
        state["cursor_query_id"] = None
        state["cursor_response_id"] = None
        state["error"] = f"Cursor recording failed: {str(e)}"
    
    return state


async def create_sequence_link(
    repository: CursorRepository,
    previous_query_id: str,
    current_query_id: str,
    time_delta_seconds: int,
) -> None:
    """
    Create FOLLOWED_BY relationship between sequential queries.
    
    Optional: Can be used to track question sequences.
    
    Args:
        repository: CursorRepository instance
        previous_query_id: Previous query ID
        current_query_id: Current query ID
        time_delta_seconds: Time between queries
    """
    cypher = """
    MATCH (prev:UserQuery {id: $prev_id})
    MATCH (curr:UserQuery {id: $curr_id})
    CREATE (curr)-[:FOLLOWED_BY {
      time_delta_seconds: $time_delta
    }]->(prev)
    """
    
    params = {
        "prev_id": previous_query_id,
        "curr_id": current_query_id,
        "time_delta": time_delta_seconds,
    }
    
    try:
        await repository.client.query(cypher, params)
        logger.debug(f"📝 Cursor: Created sequence link {current_query_id} → {previous_query_id}")
    except Exception as e:
        logger.warning(f"Failed to create sequence link: {e}")


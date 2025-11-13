"""Repository for Cursor Agent - cursor_memory graph operations."""

import logging
from typing import Any

from app.agents.cursor.schemas import (
    AssistantResponse,
    DevelopmentSession,
    UserQuery,
)
from app.core.exceptions import DatabaseError
from app.db.falkordb.client import FalkorDBClient

logger = logging.getLogger(__name__)


class CursorRepository:
    """Repository for cursor_memory graph operations."""

    def __init__(self, client: FalkorDBClient):
        """Initialize repository with FalkorDB client.
        
        Args:
            client: FalkorDB client instance
        """
        self.client = client
        self.graph_name = "cursor_memory"
        
        # Switch to cursor_memory graph
        try:
            self._graph = self.client._client.select_graph(self.graph_name)
        except Exception as e:
            logger.error(f"Failed to select graph {self.graph_name}: {e}")
            raise DatabaseError(f"Cannot access {self.graph_name}: {e}")

    async def create_session(
        self,
        mode: str,
        git_branch: str | None = None,
        git_commit: str | None = None,
        project_path: str = "",
    ) -> str:
        """Create new development session.
        
        Args:
            mode: Cursor mode (agent/ask/plan)
            git_branch: Current git branch
            git_commit: Current git commit hash
            project_path: Workspace path
            
        Returns:
            Session ID
        """
        session = DevelopmentSession(
            mode=mode,
            git_branch=git_branch,
            git_commit=git_commit,
            project_path=project_path,
        )
        
        cypher = """
        CREATE (s:DevelopmentSession {
          id: $id,
          started_at: $started_at,
          ended_at: NULL,
          total_queries: 0,
          total_responses: 0,
          mode: $mode,
          git_branch: $git_branch,
          git_commit: $git_commit,
          project_path: $project_path,
          status: 'active'
        })
        RETURN s.id as id
        """
        
        params = {
            "id": session.id,
            "started_at": session.started_at.isoformat(),
            "mode": session.mode,
            "git_branch": session.git_branch,
            "git_commit": session.git_commit,
            "project_path": session.project_path,
        }
        
        try:
            results, exec_time = await self.client.query(cypher, params)
            logger.info(
                f"📝 Cursor: Session created {session.id} "
                f"(mode={mode}, branch={git_branch}, {exec_time:.2f}ms)"
            )
            return session.id
        except Exception as e:
            logger.error(f"Failed to create session: {e}", exc_info=True)
            raise DatabaseError(f"Session creation failed: {e}")

    async def create_user_query(
        self,
        content: str,
        session_id: str,
        mode: str,
        intent: str | None = None,
        mentioned_files: list[str] | None = None,
    ) -> str:
        """Record user query.
        
        Args:
            content: Query text
            session_id: Development session ID
            mode: Cursor mode
            intent: Query intent (bug_fix/feature/question/refactor/docs)
            mentioned_files: Files mentioned in query
            
        Returns:
            Query ID
        """
        query = UserQuery(
            content=content,
            session_id=session_id,
            mode=mode,
            intent=intent,
            mentioned_files=mentioned_files or [],
        )
        
        cypher = """
        MATCH (s:DevelopmentSession {id: $session_id})
        CREATE (q:UserQuery {
          id: $id,
          content: $content,
          timestamp: $timestamp,
          session_id: $session_id,
          mode: $mode,
          intent: $intent,
          content_length: $content_length,
          has_code: $has_code,
          mentioned_files: $mentioned_files
        })
        CREATE (q)-[:IN_SESSION]->(s)
        SET s.total_queries = s.total_queries + 1
        RETURN q.id as id
        """
        
        params = {
            "id": query.id,
            "content": query.content,
            "timestamp": query.timestamp.isoformat(),
            "session_id": query.session_id,
            "mode": query.mode,
            "intent": query.intent,
            "content_length": query.content_length,
            "has_code": query.has_code,
            "mentioned_files": str(query.mentioned_files),  # Convert to string
        }
        
        try:
            results, exec_time = await self.client.query(cypher, params)
            logger.info(
                f"📝 Cursor: Query recorded {query.id} "
                f"(length={query.content_length}, {exec_time:.2f}ms)"
            )
            return query.id
        except Exception as e:
            logger.error(f"Failed to create query: {e}", exc_info=True)
            raise DatabaseError(f"Query creation failed: {e}")

    async def create_assistant_response(
        self,
        content: str,
        query_id: str,
        tools_used: list[str] | None = None,
        files_modified: list[str] | None = None,
        files_created: list[str] | None = None,
        files_deleted: list[str] | None = None,
        success: bool = True,
        execution_time_ms: float = 0.0,
    ) -> str:
        """Record assistant response.
        
        Args:
            content: Response text
            query_id: User query ID
            tools_used: List of tools used
            files_modified: List of modified files
            files_created: List of created files
            files_deleted: List of deleted files
            success: Whether response was successful
            execution_time_ms: Execution time in milliseconds
            
        Returns:
            Response ID
        """
        response = AssistantResponse(
            content=content,
            query_id=query_id,
            tools_used=tools_used or [],
            files_modified=files_modified or [],
            files_created=files_created or [],
            files_deleted=files_deleted or [],
            success=success,
            execution_time_ms=execution_time_ms,
        )
        
        cypher = """
        MATCH (q:UserQuery {id: $query_id})
        MATCH (s:DevelopmentSession {id: q.session_id})
        CREATE (r:AssistantResponse {
          id: $id,
          content: $content,
          timestamp: $timestamp,
          query_id: $query_id,
          tools_used: $tools_used,
          files_modified: $files_modified,
          files_created: $files_created,
          files_deleted: $files_deleted,
          success: $success,
          execution_time_ms: $execution_time_ms,
          content_length: $content_length,
          has_code_examples: $has_code_examples,
          error_occurred: $error_occurred
        })
        CREATE (r)-[:ANSWERS]->(q)
        SET s.total_responses = s.total_responses + 1
        RETURN r.id as id
        """
        
        params = {
            "id": response.id,
            "content": response.content,
            "timestamp": response.timestamp.isoformat(),
            "query_id": response.query_id,
            "tools_used": str(response.tools_used),
            "files_modified": str(response.files_modified),
            "files_created": str(response.files_created),
            "files_deleted": str(response.files_deleted),
            "success": response.success,
            "execution_time_ms": response.execution_time_ms,
            "content_length": response.content_length,
            "has_code_examples": response.has_code_examples,
            "error_occurred": response.error_occurred,
        }
        
        try:
            results, exec_time = await self.client.query(cypher, params)
            logger.info(
                f"📝 Cursor: Response recorded {response.id} "
                f"(success={success}, tools={len(response.tools_used)}, {exec_time:.2f}ms)"
            )
            return response.id
        except Exception as e:
            logger.error(f"Failed to create response: {e}", exc_info=True)
            raise DatabaseError(f"Response creation failed: {e}")

    async def end_session(self, session_id: str) -> None:
        """Mark session as completed.
        
        Args:
            session_id: Session ID to end
        """
        cypher = """
        MATCH (s:DevelopmentSession {id: $session_id})
        SET s.ended_at = $ended_at,
            s.status = 'completed'
        RETURN s
        """
        
        params = {
            "session_id": session_id,
            "ended_at": DevelopmentSession().started_at.isoformat(),
        }
        
        try:
            results, exec_time = await self.client.query(cypher, params)
            if not results:
                logger.warning(f"Session {session_id} not found")
            else:
                logger.info(f"📝 Cursor: Session ended {session_id} ({exec_time:.2f}ms)")
        except Exception as e:
            logger.error(f"Failed to end session: {e}", exc_info=True)
            raise DatabaseError(f"Session end failed: {e}")

    async def get_active_session(self) -> dict[str, Any] | None:
        """Get currently active session.
        
        Returns:
            Session dict or None if no active session
        """
        cypher = """
        MATCH (s:DevelopmentSession {status: 'active'})
        RETURN s
        ORDER BY s.started_at DESC
        LIMIT 1
        """
        
        try:
            results, exec_time = await self.client.query(cypher, {})
            if results:
                logger.debug(f"📝 Cursor: Found active session ({exec_time:.2f}ms)")
                return results[0]["s"]["properties"]
            return None
        except Exception as e:
            logger.error(f"Failed to get active session: {e}", exc_info=True)
            return None

    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get query/response history for session.
        
        Args:
            session_id: Session ID
            limit: Max items to return
            
        Returns:
            List of query-response pairs
        """
        cypher = """
        MATCH (s:DevelopmentSession {id: $session_id})
        MATCH (s)<-[:IN_SESSION]-(q:UserQuery)
        MATCH (q)<-[:ANSWERS]-(r:AssistantResponse)
        RETURN q, r
        ORDER BY q.timestamp DESC
        LIMIT $limit
        """
        
        params = {"session_id": session_id, "limit": limit}
        
        try:
            results, exec_time = await self.client.query(cypher, params)
            logger.info(
                f"📝 Cursor: Retrieved {len(results)} history items "
                f"for session {session_id} ({exec_time:.2f}ms)"
            )
            
            history = []
            for item in results:
                history.append({
                    "query": item["q"]["properties"] if isinstance(item["q"], dict) else item["q"],
                    "response": item["r"]["properties"] if isinstance(item["r"], dict) else item["r"],
                })
            
            return history
        except Exception as e:
            logger.error(f"Failed to get session history: {e}", exc_info=True)
            raise DatabaseError(f"History retrieval failed: {e}")

    async def get_sessions(
        self,
        status: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get list of sessions.
        
        Args:
            status: Filter by status (active/completed/interrupted)
            limit: Max sessions to return
            
        Returns:
            List of sessions
        """
        if status:
            cypher = """
            MATCH (s:DevelopmentSession {status: $status})
            RETURN s
            ORDER BY s.started_at DESC
            LIMIT $limit
            """
            params = {"status": status, "limit": limit}
        else:
            cypher = """
            MATCH (s:DevelopmentSession)
            RETURN s
            ORDER BY s.started_at DESC
            LIMIT $limit
            """
            params = {"limit": limit}
        
        try:
            results, exec_time = await self.client.query(cypher, params)
            logger.info(
                f"📝 Cursor: Retrieved {len(results)} sessions "
                f"(status={status}, {exec_time:.2f}ms)"
            )
            
            sessions = []
            for item in results:
                session = item["s"]
                if isinstance(session, dict) and "properties" in session:
                    sessions.append(session["properties"])
                else:
                    sessions.append(session)
            
            return sessions
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}", exc_info=True)
            raise DatabaseError(f"Sessions retrieval failed: {e}")

    async def health_check(self) -> bool:
        """Check if cursor_memory graph is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            cypher = "MATCH (n) RETURN count(n) as count LIMIT 1"
            results, _ = await self.client.query(cypher, {})
            return True
        except Exception:
            return False



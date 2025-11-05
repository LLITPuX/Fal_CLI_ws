"""Repository for Message and ChatSession persistence in FalkorDB."""

import logging
from datetime import datetime
from typing import Any

from app.agents.clerk.schemas import ChatMessage, ChatSession
from app.core.exceptions import DatabaseError
from app.db.falkordb.client import FalkorDBClient

logger = logging.getLogger(__name__)


class MessageRepository:
    """Handles FalkorDB operations for messages and chat sessions."""

    def __init__(self, client: FalkorDBClient):
        """Initialize repository with FalkorDB client.

        Args:
            client: Connected FalkorDB client instance
        """
        self.client = client

    async def create_session(self, session: ChatSession) -> str:
        """Create a new chat session in FalkorDB.

        Args:
            session: ChatSession object to create

        Returns:
            Session ID

        Raises:
            DatabaseError: If creation fails
        """
        cypher = """
        CREATE (s:ChatSession {
            id: $id,
            created_at: $created_at,
            user_id: $user_id,
            title: $title,
            status: $status,
            metadata: $metadata
        })
        RETURN s.id as id
        """

        params = {
            "id": session.id,
            "created_at": session.created_at.isoformat(),
            "user_id": session.user_id,
            "title": session.title,
            "status": session.status,
            "metadata": str(session.metadata),  # FalkorDB doesn't support nested dicts
        }

        try:
            results, _ = await self.client.query(cypher, params)
            logger.info(f"📝 Created chat session: {session.id}")
            return results[0]["id"] if results else session.id
        except Exception as e:
            logger.error(f"Failed to create session: {e}", exc_info=True)
            raise DatabaseError(f"Session creation failed: {str(e)}")

    async def get_session(self, session_id: str) -> ChatSession | None:
        """Retrieve a chat session by ID.

        Args:
            session_id: Session identifier

        Returns:
            ChatSession object or None if not found
        """
        cypher = """
        MATCH (s:ChatSession {id: $session_id})
        RETURN s.id as id, s.created_at as created_at, s.user_id as user_id,
               s.title as title, s.status as status, s.metadata as metadata
        """

        try:
            results, _ = await self.client.query(cypher, {"session_id": session_id})
            if not results:
                return None

            row = results[0]
            return ChatSession(
                id=row["id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                user_id=row.get("user_id"),
                title=row.get("title"),
                status=row.get("status", "active"),
                metadata={},
            )
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    async def create_message(self, message: ChatMessage) -> str:
        """Record a message to FalkorDB (Clerk's main job).

        Args:
            message: ChatMessage object to record

        Returns:
            Message ID

        Raises:
            DatabaseError: If recording fails
        """
        cypher = """
        MATCH (s:ChatSession {id: $session_id})
        CREATE (m:Message {
            id: $id,
            content: $content,
            role: $role,
            timestamp: $timestamp,
            status: $status,
            metadata: $metadata
        })
        CREATE (m)-[:IN_SESSION]->(s)
        RETURN m.id as id
        """

        params = {
            "id": message.id,
            "content": message.content,
            "role": message.role,
            "timestamp": message.timestamp.isoformat(),
            "session_id": message.session_id,
            "status": message.status,
            "metadata": str(message.metadata),
        }

        try:
            results, exec_time = await self.client.query(cypher, params)
            logger.info(
                f"📝 Писарь записав повідомлення: {message.id} "
                f"(role={message.role}, session={message.session_id}, {exec_time:.2f}ms)"
            )
            return results[0]["id"] if results else message.id
        except Exception as e:
            logger.error(f"Failed to create message: {e}", exc_info=True)
            raise DatabaseError(f"Message creation failed: {str(e)}")

    async def get_message(self, message_id: str) -> ChatMessage | None:
        """Retrieve a message by ID.

        Args:
            message_id: Message identifier

        Returns:
            ChatMessage object or None if not found
        """
        cypher = """
        MATCH (m:Message {id: $message_id})-[:IN_SESSION]->(s:ChatSession)
        RETURN m.id as id, m.content as content, m.role as role,
               m.timestamp as timestamp, s.id as session_id,
               m.status as status, m.metadata as metadata
        """

        try:
            results, _ = await self.client.query(cypher, {"message_id": message_id})
            if not results:
                return None

            row = results[0]
            return ChatMessage(
                id=row["id"],
                content=row["content"],
                role=row["role"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                session_id=row["session_id"],
                status=row.get("status", "recorded"),
                metadata={},
            )
        except Exception as e:
            logger.error(f"Failed to get message {message_id}: {e}")
            return None

    async def get_session_messages(
        self, session_id: str, limit: int = 50, offset: int = 0
    ) -> list[ChatMessage]:
        """Retrieve messages for a chat session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of ChatMessage objects ordered by timestamp
        """
        cypher = """
        MATCH (m:Message)-[:IN_SESSION]->(s:ChatSession {id: $session_id})
        RETURN m.id as id, m.content as content, m.role as role,
               m.timestamp as timestamp, s.id as session_id,
               m.status as status, m.metadata as metadata
        ORDER BY m.timestamp ASC
        SKIP $offset
        LIMIT $limit
        """

        params = {"session_id": session_id, "limit": limit, "offset": offset}

        try:
            results, exec_time = await self.client.query(cypher, params)
            
            messages = [
                ChatMessage(
                    id=row["id"],
                    content=row["content"],
                    role=row["role"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    session_id=row["session_id"],
                    status=row.get("status", "recorded"),
                    metadata={},
                )
                for row in results
            ]
            
            logger.info(
                f"Retrieved {len(messages)} messages for session {session_id} "
                f"({exec_time:.2f}ms)"
            )
            return messages
        except Exception as e:
            logger.error(f"Failed to get session messages: {e}", exc_info=True)
            raise DatabaseError(f"Failed to retrieve messages: {str(e)}")

    async def update_message_status(
        self, message_id: str, status: str
    ) -> bool:
        """Update message status.

        Args:
            message_id: Message identifier
            status: New status value

        Returns:
            True if updated successfully
        """
        cypher = """
        MATCH (m:Message {id: $message_id})
        SET m.status = $status
        RETURN m.id as id
        """

        try:
            results, _ = await self.client.query(
                cypher, {"message_id": message_id, "status": status}
            )
            return len(results) > 0
        except Exception as e:
            logger.error(f"Failed to update message status: {e}")
            return False


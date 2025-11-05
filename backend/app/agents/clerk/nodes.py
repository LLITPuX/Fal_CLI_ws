"""LangGraph nodes for Clerk Agent."""

import logging
from datetime import datetime

from app.agents.clerk.repository import MessageRepository
from app.agents.clerk.schemas import ChatMessage

logger = logging.getLogger(__name__)


async def clerk_record_node(state: dict, repository: MessageRepository) -> dict:
    """Clerk node: Records message to FalkorDB without any processing.

    This is the "Писарь" (Scribe) - his only job is to faithfully record
    every message (both user and assistant) into the knowledge graph.

    Args:
        state: Current graph state with message data
        repository: MessageRepository instance for DB operations

    Returns:
        Updated state with recording results
    """
    logger.info("📝 Писарь: Починаю запис повідомлення...")

    try:
        # Create message object
        message = ChatMessage(
            content=state["message_content"],
            role=state["message_role"],
            session_id=state["session_id"],
            timestamp=datetime.now(),
            status="recorded",
            metadata=state.get("metadata", {}),
        )

        # Record to FalkorDB
        message_id = await repository.create_message(message)

        # Update state
        state["message_id"] = message_id
        state["recorded"] = True
        state["error"] = None

        logger.info(
            f"📝 Писарь успішно записав: {message_id} "
            f"(role={message.role}, content_length={len(message.content)})"
        )

    except Exception as e:
        logger.error(f"📝 Писарь: Помилка запису: {e}", exc_info=True)
        state["recorded"] = False
        state["error"] = f"Recording failed: {str(e)}"

    return state


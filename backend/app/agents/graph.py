"""LangGraph workflow for multi-agent chat system."""

import logging
from typing import Annotated

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.agents.clerk.nodes import clerk_record_node
from app.agents.clerk.repository import MessageRepository
from app.agents.state import ChatState

logger = logging.getLogger(__name__)


def create_chat_workflow(repository: MessageRepository) -> StateGraph:
    """Create the multi-agent chat workflow.

    Current flow (Phase 1 - MVP):
        Entry → Clerk (record message) → END

    Future flow:
        Entry → Clerk → Subconscious → Orchestrator → END

    Args:
        repository: MessageRepository for database operations

    Returns:
        Compiled LangGraph workflow
    """
    logger.info("🔧 Creating chat workflow (Clerk MVP)...")

    # Define the workflow graph
    workflow = StateGraph(ChatState)

    # Add Clerk node (Писарь)
    async def clerk_node_wrapper(state: ChatState) -> ChatState:
        """Wrapper to inject repository into node."""
        state_dict = state.model_dump()
        updated_state = await clerk_record_node(state_dict, repository)
        return ChatState(**updated_state)

    workflow.add_node("clerk", clerk_node_wrapper)

    # Define flow: Entry → Clerk → End
    workflow.set_entry_point("clerk")
    workflow.add_edge("clerk", END)

    # Compile the workflow
    compiled = workflow.compile()
    logger.info("✅ Chat workflow compiled successfully")

    return compiled


# Global workflow instance (will be initialized in main.py)
chat_workflow: StateGraph | None = None


def init_chat_workflow(repository: MessageRepository) -> None:
    """Initialize global chat workflow instance.

    Args:
        repository: MessageRepository instance
    """
    global chat_workflow
    chat_workflow = create_chat_workflow(repository)
    logger.info("🚀 Chat workflow initialized")


def get_chat_workflow() -> StateGraph:
    """Get initialized chat workflow.

    Returns:
        Chat workflow instance

    Raises:
        RuntimeError: If workflow not initialized
    """
    if chat_workflow is None:
        raise RuntimeError("Chat workflow not initialized. Call init_chat_workflow first.")
    return chat_workflow


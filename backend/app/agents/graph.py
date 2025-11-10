"""LangGraph workflow for multi-agent chat system."""

import logging
from typing import Annotated

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.agents.clerk.nodes import clerk_record_node
from app.agents.clerk.repository import MessageRepository
from app.agents.state import ChatState
from app.agents.subconscious.nodes import subconscious_analyze_node
from app.agents.subconscious.repository import SubconsciousRepository

logger = logging.getLogger(__name__)


def create_chat_workflow(
    clerk_repo: MessageRepository,
    subconscious_repo: SubconsciousRepository,
) -> StateGraph:
    """Create the multi-agent chat workflow.

    Current flow (Phase 2):
        Entry → Clerk (record message) → Subconscious (analyze) → END

    Future flow (Phase 3):
        Entry → Clerk → Subconscious → Orchestrator → END

    Args:
        clerk_repo: MessageRepository for Clerk operations
        subconscious_repo: SubconsciousRepository for Subconscious operations

    Returns:
        Compiled LangGraph workflow
    """
    logger.info("🔧 Creating chat workflow (Phase 2: Clerk + Subconscious)...")

    # Define the workflow graph
    workflow = StateGraph(ChatState)

    # Add Clerk node (Писарь)
    async def clerk_node_wrapper(state: ChatState) -> ChatState:
        """Wrapper to inject repository into Clerk node."""
        state_dict = state.model_dump()
        updated_state = await clerk_record_node(state_dict, clerk_repo)
        return ChatState(**updated_state)

    # Add Subconscious node (Підсвідомість)
    async def subconscious_node_wrapper(state: ChatState) -> ChatState:
        """Wrapper to inject repository into Subconscious node."""
        state_dict = state.model_dump()
        
        # Skip if not recorded
        if not state_dict.get("recorded"):
            logger.warning("⚠️ Skipping Subconscious (message not recorded)")
            return state
        
        # Run analysis
        updated_state = await subconscious_analyze_node(
            state_dict,
            repository=subconscious_repo,
        )
        return ChatState(**updated_state)

    workflow.add_node("clerk", clerk_node_wrapper)
    workflow.add_node("subconscious", subconscious_node_wrapper)

    # Define flow: Entry → Clerk → Subconscious → End
    workflow.set_entry_point("clerk")
    workflow.add_edge("clerk", "subconscious")
    workflow.add_edge("subconscious", END)

    # Compile the workflow
    compiled = workflow.compile()
    logger.info("✅ Chat workflow compiled successfully (Clerk + Subconscious)")

    return compiled


# Global workflow instance (will be initialized in main.py)
chat_workflow: StateGraph | None = None


def init_chat_workflow(
    clerk_repo: MessageRepository,
    subconscious_repo: SubconsciousRepository,
) -> None:
    """Initialize global chat workflow instance.

    Args:
        clerk_repo: MessageRepository instance
        subconscious_repo: SubconsciousRepository instance
    """
    global chat_workflow
    chat_workflow = create_chat_workflow(clerk_repo, subconscious_repo)
    logger.info("🚀 Chat workflow initialized (Phase 2: Clerk + Subconscious)")


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


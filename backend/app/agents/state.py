"""Shared state schemas for LangGraph workflow."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatState(BaseModel):
    """State that flows through the multi-agent system.

    This state is passed between agents:
    - Clerk (Писарь) → records message
    - Subconscious (Підсвідомість) → analyzes context (future)
    - Orchestrator (Оркестратор) → decides action (future)
    """

    # === Input (from API) ===
    message_content: str
    message_role: Literal["user", "assistant", "system"]
    session_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    # === Clerk outputs ===
    message_id: str | None = None
    recorded: bool = False

    # === Subconscious outputs (future) ===
    context: dict[str, Any] = Field(default_factory=dict)
    related_messages: list[str] = Field(default_factory=list)
    semantic_similarity: float = 0.0

    # === Orchestrator outputs (future) ===
    action: Literal["respond", "ask_clarification", "search", "none"] = "respond"
    response: str | None = None

    # === Error handling ===
    error: str | None = None

    class Config:
        arbitrary_types_allowed = True


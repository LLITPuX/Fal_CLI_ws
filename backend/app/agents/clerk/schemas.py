"""Pydantic schemas for Clerk Agent."""

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ChatSession(BaseModel):
    """Chat session model."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    created_at: datetime = Field(default_factory=datetime.now)
    user_id: str | None = None
    title: str | None = None
    status: Literal["active", "archived"] = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    """Chat message model for both user and assistant messages."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    content: str
    role: Literal["user", "assistant", "system"]
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str
    status: Literal["recorded", "analyzed", "responded"] = "recorded"
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123",
                "content": "Розкажи про козацьку історію",
                "role": "user",
                "timestamp": "2025-11-05T12:00:00",
                "session_id": "session_xyz",
                "status": "recorded",
                "metadata": {},
            }
        }


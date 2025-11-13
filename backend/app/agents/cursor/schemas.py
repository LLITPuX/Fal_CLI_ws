"""Pydantic schemas for Cursor Agent (Development memory)."""

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class DevelopmentSession(BaseModel):
    """Development session model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: datetime | None = None
    total_queries: int = 0
    total_responses: int = 0
    mode: Literal["agent", "ask", "plan"] = "agent"
    git_branch: str | None = None
    git_commit: str | None = None
    project_path: str = ""
    status: Literal["active", "completed", "interrupted"] = "active"


class UserQuery(BaseModel):
    """User query model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str
    mode: Literal["agent", "ask", "plan"] = "agent"
    intent: str | None = None  # "bug_fix", "feature", "question", "refactor", "docs"
    
    # Metadata
    content_length: int = 0
    has_code: bool = False
    mentioned_files: list[str] = Field(default_factory=list)
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.content_length == 0:
            self.content_length = len(self.content)
        if not self.has_code:
            self.has_code = "```" in self.content


class AssistantResponse(BaseModel):
    """Assistant response model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    query_id: str
    
    # Tools & Actions
    tools_used: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    files_created: list[str] = Field(default_factory=list)
    files_deleted: list[str] = Field(default_factory=list)
    
    # Outcome
    success: bool = True
    execution_time_ms: float = 0.0
    
    # Metadata
    content_length: int = 0
    has_code_examples: bool = False
    error_occurred: bool = False
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.content_length == 0:
            self.content_length = len(self.content)
        if not self.has_code_examples:
            self.has_code_examples = "```" in self.content
        if not self.error_occurred:
            self.error_occurred = not self.success


# API Request/Response models

class StartSessionRequest(BaseModel):
    """Request to start new development session."""
    
    mode: Literal["agent", "ask", "plan"] = "agent"
    git_branch: str | None = None
    git_commit: str | None = None
    project_path: str = ""


class EndSessionRequest(BaseModel):
    """Request to end development session."""
    
    session_id: str
    backup_to_git: bool = True


class SessionResponse(BaseModel):
    """Response with session info."""
    
    session_id: str
    status: str
    backup_file: str | None = None


class SessionHistoryItem(BaseModel):
    """Single query-response pair."""
    
    query: UserQuery
    response: AssistantResponse


class SessionHistoryResponse(BaseModel):
    """Session history response."""
    
    session_id: str
    history: list[SessionHistoryItem]
    total_items: int


class SessionListResponse(BaseModel):
    """List of sessions."""
    
    sessions: list[DevelopmentSession]
    total: int




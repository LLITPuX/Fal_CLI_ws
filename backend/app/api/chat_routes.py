"""Chat API routes for Cybersich multi-agent system."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.agents.clerk.repository import MessageRepository
from app.agents.clerk.schemas import ChatSession
from app.agents.graph import get_chat_workflow
from app.agents.state import ChatState
from app.db.falkordb.client import FalkorDBClient, get_falkordb_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# === Request/Response Models ===


class SendMessageRequest(BaseModel):
    """Request to send a message in chat."""

    content: str = Field(..., min_length=1, max_length=10000)
    session_id: str = Field(..., description="Chat session identifier")
    role: str = Field(default="user", pattern="^(user|assistant|system)$")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Розкажи про історію козацтва",
                "session_id": "abc123xyz",
                "role": "user",
            }
        }


class ChatMessageResponse(BaseModel):
    """Response after sending a message."""

    message_id: str
    session_id: str
    status: str
    recorded: bool
    error: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_abc123",
                "session_id": "abc123xyz",
                "status": "recorded",
                "recorded": True,
                "error": None,
            }
        }


class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""

    user_id: str | None = None
    title: str | None = None

    class Config:
        json_schema_extra = {
            "example": {"user_id": "user_123", "title": "Розмова про козаків"}
        }


class SessionResponse(BaseModel):
    """Response with session information."""

    session_id: str
    created_at: str
    user_id: str | None
    title: str | None
    status: str


class MessageHistoryResponse(BaseModel):
    """Response with message history."""

    session_id: str
    messages: list[dict]
    total: int


# === Dependencies ===


def get_message_repository(
    client: Annotated[FalkorDBClient, Depends(get_falkordb_client)]
) -> MessageRepository:
    """Dependency to get MessageRepository.

    Args:
        client: FalkorDB client from dependency injection

    Returns:
        MessageRepository instance
    """
    return MessageRepository(client)


MessageRepositoryDep = Annotated[MessageRepository, Depends(get_message_repository)]


# === Endpoints ===


@router.post("/session", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    repository: MessageRepositoryDep,
):
    """Create a new chat session.

    Args:
        request: Session creation request
        repository: Message repository

    Returns:
        Created session information
    """
    session = ChatSession(
        user_id=request.user_id,
        title=request.title,
        status="active",
    )

    try:
        session_id = await repository.create_session(session)
        logger.info(f"✨ Created new chat session: {session_id}")

        return SessionResponse(
            session_id=session_id,
            created_at=session.created_at.isoformat(),
            user_id=session.user_id,
            title=session.title,
            status=session.status,
        )
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: SendMessageRequest,
    repository: MessageRepositoryDep,
):
    """Send a message in chat (triggers Clerk agent).

    Flow:
    1. Clerk (Писарь) records message to FalkorDB
    2. (Future) Subconscious analyzes context
    3. (Future) Orchestrator decides action

    Args:
        request: Message to send
        repository: Message repository

    Returns:
        Message recording result
    """
    logger.info(
        f"📨 Received message for session {request.session_id}: "
        f"{request.content[:50]}{'...' if len(request.content) > 50 else ''}"
    )

    # Check if session exists
    session = await repository.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {request.session_id} not found. Create it first.",
        )

    # Create initial state
    initial_state = ChatState(
        message_content=request.content,
        message_role=request.role,  # type: ignore
        session_id=request.session_id,
        metadata={},
    )

    try:
        # Run through LangGraph workflow (Clerk agent)
        workflow = get_chat_workflow()
        final_state = await workflow.ainvoke(initial_state)

        if final_state.error:
            logger.error(f"Workflow error: {final_state.error}")
            raise HTTPException(status_code=500, detail=final_state.error)

        return ChatMessageResponse(
            message_id=final_state.message_id or "unknown",
            session_id=request.session_id,
            status="recorded" if final_state.recorded else "failed",
            recorded=final_state.recorded,
            error=final_state.error,
        )

    except Exception as e:
        logger.error(f"Failed to process message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to process message: {str(e)}"
        )


@router.get("/session/{session_id}/history", response_model=MessageHistoryResponse)
async def get_session_history(
    session_id: str,
    repository: MessageRepositoryDep,
    limit: int = 50,
    offset: int = 0,
):
    """Get message history for a session.

    Args:
        session_id: Session identifier
        repository: Message repository
        limit: Maximum messages to return
        offset: Number of messages to skip

    Returns:
        Message history
    """
    logger.info(f"📜 Fetching history for session {session_id} (limit={limit}, offset={offset})")

    try:
        messages = await repository.get_session_messages(session_id, limit, offset)

        return MessageHistoryResponse(
            session_id=session_id,
            messages=[
                {
                    "id": msg.id,
                    "content": msg.content,
                    "role": msg.role,
                    "timestamp": msg.timestamp.isoformat(),
                    "status": msg.status,
                }
                for msg in messages
            ],
            total=len(messages),
        )
    except Exception as e:
        logger.error(f"Failed to get history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve history: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session_info(
    session_id: str,
    repository: MessageRepositoryDep,
):
    """Get information about a chat session.

    Args:
        session_id: Session identifier
        repository: Message repository

    Returns:
        Session information
    """
    session = await repository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return SessionResponse(
        session_id=session.id,
        created_at=session.created_at.isoformat(),
        user_id=session.user_id,
        title=session.title,
        status=session.status,
    )


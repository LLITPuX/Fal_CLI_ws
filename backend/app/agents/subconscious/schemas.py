"""Pydantic schemas for Subconscious Agent."""

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """Semantic chunk of text with embedding.
    
    Represents a portion of a message that was split using semantic boundaries
    (paragraphs, sentences, etc.) rather than fixed-size chunks.
    """

    id: str = Field(default_factory=lambda: uuid4().hex)
    content: str
    position: int  # Position in original message
    char_start: int
    char_end: int
    chunk_type: Literal["paragraph", "sentence", "code", "heading"] = "paragraph"

    # Temporal fields (Graphiti pattern)
    created_at: datetime = Field(default_factory=datetime.now)
    valid_at: datetime = Field(default_factory=datetime.now)
    invalid_at: datetime | None = None

    # Embeddings
    embedding: list[float] | None = None  # 1536-dim vector (OpenAI text-embedding-3-small)
    embedding_model: str = "text-embedding-3-small"
    embedding_created_at: datetime | None = None

    # Reference to parent message
    message_id: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "chunk_abc123",
                "content": "Docker is a containerization platform...",
                "position": 0,
                "char_start": 0,
                "char_end": 150,
                "chunk_type": "paragraph",
                "created_at": "2025-11-10T12:00:00",
                "valid_at": "2025-11-10T12:00:00",
                "invalid_at": None,
                "embedding": [0.1, 0.2],  # Truncated for example
                "embedding_model": "text-embedding-3-small",
                "message_id": "msg_xyz",
            }
        }


class ExtractedEntity(BaseModel):
    """Entity extracted from text by OpenAI.
    
    Temporary model used during extraction process before saving to graph.
    """

    name: str  # Original text
    type: Literal["PERSON", "ORG", "LOCATION", "TECH", "CONCEPT", "EVENT"]
    confidence: float  # 0.0-1.0
    context: str  # Surrounding text for disambiguation


class Entity(BaseModel):
    """Named entity in the knowledge graph.
    
    Represents people, organizations, technologies, concepts, etc.
    mentioned in messages.
    """

    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str  # Original form
    canonical_name: str  # Normalized (lowercase, trimmed)
    type: Literal["PERSON", "ORG", "LOCATION", "TECH", "CONCEPT", "EVENT"]

    # Temporal fields
    first_seen: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)
    valid_at: datetime = Field(default_factory=datetime.now)
    invalid_at: datetime | None = None

    # Embeddings
    embedding: list[float] | None = None
    embedding_model: str = "text-embedding-3-small"

    # Metadata
    mention_count: int = 1
    confidence: float = 1.0  # Average confidence from extractions

    class Config:
        json_schema_extra = {
            "example": {
                "id": "entity_abc",
                "name": "Docker",
                "canonical_name": "docker",
                "type": "TECH",
                "first_seen": "2025-11-10T12:00:00",
                "last_seen": "2025-11-10T12:00:00",
                "mention_count": 5,
                "confidence": 0.95,
            }
        }


class SimilarChunk(BaseModel):
    """Chunk with similarity score (search result)."""

    chunk: Chunk
    similarity: float  # Cosine similarity (0.0-1.0)


class ContextAnalysis(BaseModel):
    """Complete context analysis result passed to Orchestrator.
    
    Contains all information Subconscious gathered: recent history,
    semantic matches, entities, topics, and temporal insights.
    """

    # 1. Recent temporal context
    recent_messages: list[dict[str, Any]] = Field(default_factory=list)

    # 2. Semantic matches
    similar_chunks: list[dict[str, Any]] = Field(default_factory=list)
    similar_messages: list[dict[str, Any]] = Field(default_factory=list)

    # 3. Entities
    mentioned_entities: list[dict[str, Any]] = Field(default_factory=list)
    related_entities: list[dict[str, Any]] = Field(default_factory=list)
    entity_context: dict[str, list[str]] = Field(default_factory=dict)

    # 4. Graph insights
    topics: list[str] = Field(default_factory=list)
    is_new_topic: bool = False
    conversation_continuity: float = 0.0  # 0.0-1.0

    # 5. Temporal insights
    time_span_days: int = 0
    oldest_relevant_message: datetime | None = None

    # 6. Metadata
    total_chunks_analyzed: int = 0
    total_entities_extracted: int = 0
    processing_time_ms: float = 0.0
    confidence: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "recent_messages": [],
                "similar_chunks": [],
                "mentioned_entities": [
                    {
                        "name": "Docker",
                        "type": "TECH",
                        "confidence": 0.95,
                    }
                ],
                "topics": ["docker", "kubernetes", "containerization"],
                "conversation_continuity": 0.82,
                "time_span_days": 7,
                "total_chunks_analyzed": 5,
                "total_entities_extracted": 3,
                "processing_time_ms": 450.0,
                "confidence": 0.85,
            }
        }


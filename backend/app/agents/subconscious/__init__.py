"""Subconscious Agent (Підсвідомість) - Phase 2.

Responsible for:
- Semantic text chunking
- Entity extraction
- Vector embeddings generation
- Similarity search in temporal graph
- Context building for Orchestrator
"""

from app.agents.subconscious.nodes import subconscious_analyze_node
from app.agents.subconscious.schemas import (
    Chunk,
    ContextAnalysis,
    Entity,
    ExtractedEntity,
    SimilarChunk,
)

__all__ = [
    "subconscious_analyze_node",
    "Chunk",
    "Entity",
    "ExtractedEntity",
    "SimilarChunk",
    "ContextAnalysis",
]


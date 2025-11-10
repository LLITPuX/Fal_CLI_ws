"""Context formatting for Orchestrator."""

import logging
from datetime import datetime

from app.agents.clerk.schemas import ChatMessage
from app.agents.subconscious.repository import SubconsciousRepository
from app.agents.subconscious.schemas import Chunk, ContextAnalysis, Entity, SimilarChunk
from app.core.config import settings

logger = logging.getLogger(__name__)


class ContextFormatter:
    """Build rich context from chunks, entities, and graph data."""

    def __init__(self, repository: SubconsciousRepository):
        """Initialize context formatter.
        
        Args:
            repository: Subconscious repository for queries
        """
        self.repository = repository

    async def build_context(
        self,
        message: ChatMessage,
        chunks: list[Chunk],
        entities: list[Entity],
        similar_chunks: list[SimilarChunk],
    ) -> ContextAnalysis:
        """Build complete context analysis.
        
        Args:
            message: Current message
            chunks: Chunks from current message
            entities: Entities extracted from current message
            similar_chunks: Similar chunks found in history
            
        Returns:
            Complete context analysis for Orchestrator
        """
        logger.info("📋 Building context for Orchestrator...")

        context = ContextAnalysis()

        # 1. Recent messages (temporal query, NO session filter)
        context.recent_messages = await self._get_recent_messages(
            reference_time=message.timestamp,
        )

        # 2. Semantic matches
        context.similar_chunks = [self._chunk_to_dict(sc) for sc in similar_chunks]
        context.similar_messages = await self._get_messages_for_chunks(similar_chunks)

        # 3. Entities
        context.mentioned_entities = [self._entity_to_dict(e) for e in entities]
        # TODO: related_entities можна додати пізніше (entity similarity)

        # 4. Topics (extract from entities)
        context.topics = self._extract_topics(entities)
        context.is_new_topic = self._detect_new_topic(
            context.topics,
            context.recent_messages,
        )

        # 5. Conversation continuity (based on similarity scores)
        context.conversation_continuity = self._calculate_continuity(similar_chunks)

        # 6. Temporal insights
        if context.similar_messages:
            timestamps = [
                datetime.fromisoformat(m["timestamp"])
                for m in context.similar_messages
            ]
            oldest = min(timestamps)
            context.oldest_relevant_message = oldest
            context.time_span_days = (message.timestamp - oldest).days

        # 7. Metadata
        context.total_chunks_analyzed = len(chunks)
        context.total_entities_extracted = len(entities)
        context.confidence = self._calculate_confidence(similar_chunks, entities)

        logger.info(
            f"📋 Context built: {len(context.recent_messages)} recent, "
            f"{len(context.similar_chunks)} similar, "
            f"{len(context.mentioned_entities)} entities, "
            f"continuity={context.conversation_continuity:.2f}"
        )

        return context

    async def _get_recent_messages(
        self,
        reference_time: datetime,
    ) -> list[dict]:
        """Get recent messages using temporal query.
        
        Args:
            reference_time: Reference point
            
        Returns:
            List of message dicts
        """
        messages = await self.repository.get_recent_messages(
            reference_time=reference_time,
            limit=settings.subconscious_recent_messages_limit,
        )

        return [
            {
                "id": m.id,
                "content": m.content[:200] + "..." if len(m.content) > 200 else m.content,  # Truncate for context
                "role": m.role,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in messages
        ]

    async def _get_messages_for_chunks(
        self,
        similar_chunks: list[SimilarChunk],
    ) -> list[dict]:
        """Get messages that contain similar chunks.
        
        Args:
            similar_chunks: Similar chunks found
            
        Returns:
            Unique messages (deduplicated)
        """
        # Extract unique message IDs
        message_ids = list({sc.chunk.message_id for sc in similar_chunks if sc.chunk.message_id})

        if not message_ids:
            return []

        # For now, return basic info
        # TODO: можна оптимізувати з одним запитом до БД
        messages = []
        for msg_id in message_ids[:5]:  # Limit to top 5 messages
            # Get chunks for this message to reconstruct content
            chunks = await self.repository.get_chunks_for_message(msg_id)
            if chunks:
                content = " ".join(c.content for c in chunks)
                messages.append({
                    "id": msg_id,
                    "content": content[:200] + "..." if len(content) > 200 else content,
                    "timestamp": chunks[0].created_at.isoformat(),
                })

        return messages

    def _extract_topics(self, entities: list[Entity]) -> list[str]:
        """Extract topics from entities.
        
        Prioritizes TECH and CONCEPT entities.
        
        Args:
            entities: Extracted entities
            
        Returns:
            List of topic strings
        """
        topics = []

        # TECH entities are primary topics
        tech_entities = [e for e in entities if e.type == "TECH"]
        topics.extend([e.canonical_name for e in tech_entities[:5]])

        # CONCEPT entities are secondary
        concept_entities = [e for e in entities if e.type == "CONCEPT"]
        topics.extend([e.canonical_name for e in concept_entities[:3]])

        # Remove duplicates while preserving order
        seen = set()
        unique_topics = []
        for topic in topics:
            if topic not in seen:
                seen.add(topic)
                unique_topics.append(topic)

        return unique_topics

    def _detect_new_topic(
        self,
        current_topics: list[str],
        recent_messages: list[dict],
    ) -> bool:
        """Detect if current message introduces new topic.
        
        Simple heuristic: if no topics overlap with recent messages, it's new.
        
        Args:
            current_topics: Topics from current message
            recent_messages: Recent message history
            
        Returns:
            True if new topic detected
        """
        if not current_topics:
            return False

        # Extract words from recent messages
        recent_text = " ".join(
            m.get("content", "").lower()
            for m in recent_messages[:3]  # Last 3 messages
        )

        # Check if any current topic appears in recent text
        for topic in current_topics:
            if topic.lower() in recent_text:
                return False  # Topic found in recent history

        # No topics found = new topic
        return True

    def _calculate_continuity(
        self,
        similar_chunks: list[SimilarChunk],
    ) -> float:
        """Calculate conversation continuity score.
        
        High continuity = many similar chunks with high similarity
        Low continuity = no similar chunks (new topic)
        
        Args:
            similar_chunks: Similar chunks found
            
        Returns:
            Continuity score (0.0-1.0)
        """
        if not similar_chunks:
            return 0.0

        # Weighted average of top similarities
        # Top chunks have more weight
        weights = [1.0, 0.8, 0.6, 0.4, 0.2]
        
        weighted_sum = sum(
            sc.similarity * weights[min(i, len(weights) - 1)]
            for i, sc in enumerate(similar_chunks[:5])
        )
        
        weight_sum = sum(weights[:min(len(similar_chunks), 5)])
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0

    def _calculate_confidence(
        self,
        similar_chunks: list[SimilarChunk],
        entities: list[Entity],
    ) -> float:
        """Calculate overall confidence in context quality.
        
        Factors:
        - Number and similarity of matches
        - Entity extraction confidence
        - Data completeness
        
        Args:
            similar_chunks: Similar chunks
            entities: Extracted entities
            
        Returns:
            Confidence score (0.0-1.0)
        """
        scores = []

        # Similarity confidence
        if similar_chunks:
            avg_similarity = sum(sc.similarity for sc in similar_chunks) / len(similar_chunks)
            scores.append(avg_similarity)
        else:
            scores.append(0.5)  # Neutral if no matches

        # Entity confidence
        if entities:
            avg_entity_conf = sum(e.confidence for e in entities) / len(entities)
            scores.append(avg_entity_conf)
        else:
            scores.append(0.5)  # Neutral if no entities

        # Average
        return sum(scores) / len(scores) if scores else 0.5

    def _chunk_to_dict(self, similar_chunk: SimilarChunk) -> dict:
        """Convert SimilarChunk to dict for JSON serialization.
        
        Args:
            similar_chunk: SimilarChunk object
            
        Returns:
            Dictionary representation
        """
        chunk = similar_chunk.chunk
        return {
            "id": chunk.id,
            "content": chunk.content,
            "similarity": similar_chunk.similarity,
            "chunk_type": chunk.chunk_type,
            "message_id": chunk.message_id,
            "created_at": chunk.created_at.isoformat(),
        }

    def _entity_to_dict(self, entity: Entity) -> dict:
        """Convert Entity to dict for JSON serialization.
        
        Args:
            entity: Entity object
            
        Returns:
            Dictionary representation
        """
        return {
            "id": entity.id,
            "name": entity.name,
            "canonical_name": entity.canonical_name,
            "type": entity.type,
            "confidence": entity.confidence,
            "mention_count": entity.mention_count,
        }


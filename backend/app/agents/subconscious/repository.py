"""Repository for Subconscious persistence in FalkorDB."""

import logging
from datetime import datetime

from app.agents.clerk.schemas import ChatMessage
from app.agents.subconscious.schemas import Chunk, Entity, SimilarChunk
from app.core.exceptions import DatabaseError
from app.db.falkordb.client import FalkorDBClient

logger = logging.getLogger(__name__)


class SubconsciousRepository:
    """Handles FalkorDB operations for chunks, entities, and relationships."""

    def __init__(self, client: FalkorDBClient):
        """Initialize repository with FalkorDB client.
        
        Args:
            client: Connected FalkorDB client instance
        """
        self.client = client

    # ===== CHUNK OPERATIONS =====

    async def create_chunk(self, chunk: Chunk) -> str:
        """Create chunk node and link to message.
        
        Args:
            chunk: Chunk object to create
            
        Returns:
            Chunk ID
            
        Raises:
            DatabaseError: If creation fails
        """
        cypher = """
        MATCH (m:Message {id: $message_id})
        CREATE (c:Chunk {
            id: $id,
            content: $content,
            position: $position,
            char_start: $char_start,
            char_end: $char_end,
            chunk_type: $chunk_type,
            created_at: $created_at,
            valid_at: $valid_at,
            invalid_at: $invalid_at,
            embedding: $embedding,
            embedding_model: $embedding_model,
            embedding_created_at: $embedding_created_at
        })
        CREATE (c)-[:PART_OF {position: $position}]->(m)
        RETURN c.id as id
        """

        params = {
            "id": chunk.id,
            "message_id": chunk.message_id,
            "content": chunk.content,
            "position": chunk.position,
            "char_start": chunk.char_start,
            "char_end": chunk.char_end,
            "chunk_type": chunk.chunk_type,
            "created_at": chunk.created_at.isoformat(),
            "valid_at": chunk.valid_at.isoformat(),
            "invalid_at": chunk.invalid_at.isoformat() if chunk.invalid_at else None,
            "embedding": chunk.embedding or [],
            "embedding_model": chunk.embedding_model,
            "embedding_created_at": chunk.embedding_created_at.isoformat() if chunk.embedding_created_at else None,
        }

        try:
            results, exec_time = await self.client.query(cypher, params)
            logger.debug(f"Created chunk: {chunk.id} ({exec_time:.2f}ms)")
            return results[0]["id"] if results else chunk.id
        except Exception as e:
            logger.error(f"Failed to create chunk: {e}", exc_info=True)
            raise DatabaseError(f"Chunk creation failed: {str(e)}")

    async def create_chunks_batch(self, chunks: list[Chunk]) -> int:
        """Create multiple chunks efficiently.
        
        Args:
            chunks: List of chunks to create
            
        Returns:
            Number of chunks created
        """
        if not chunks:
            return 0

        count = 0
        for chunk in chunks:
            try:
                await self.create_chunk(chunk)
                count += 1
            except DatabaseError as e:
                logger.error(f"Failed to create chunk {chunk.id}: {e}")
                continue

        logger.info(f"💾 Created {count}/{len(chunks)} chunks")
        return count

    async def get_chunks_for_message(self, message_id: str) -> list[Chunk]:
        """Get all chunks for a message.
        
        Args:
            message_id: Message ID
            
        Returns:
            List of chunks ordered by position
        """
        cypher = """
        MATCH (c:Chunk)-[:PART_OF]->(m:Message {id: $message_id})
        RETURN c.id as id, c.content as content, c.position as position,
               c.char_start as char_start, c.char_end as char_end,
               c.chunk_type as chunk_type, c.created_at as created_at,
               c.valid_at as valid_at, c.invalid_at as invalid_at,
               c.embedding as embedding, c.embedding_model as embedding_model,
               c.embedding_created_at as embedding_created_at
        ORDER BY c.position ASC
        """

        try:
            results, _ = await self.client.query(cypher, {"message_id": message_id})
            chunks = []
            for row in results:
                chunk = Chunk(
                    id=row["id"],
                    content=row["content"],
                    position=row["position"],
                    char_start=row["char_start"],
                    char_end=row["char_end"],
                    chunk_type=row.get("chunk_type", "paragraph"),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    valid_at=datetime.fromisoformat(row["valid_at"]),
                    invalid_at=datetime.fromisoformat(row["invalid_at"]) if row.get("invalid_at") else None,
                    embedding=row.get("embedding"),
                    embedding_model=row.get("embedding_model", "text-embedding-3-small"),
                    embedding_created_at=datetime.fromisoformat(row["embedding_created_at"]) if row.get("embedding_created_at") else None,
                    message_id=message_id,
                )
                chunks.append(chunk)
            return chunks
        except Exception as e:
            logger.error(f"Failed to get chunks for message: {e}")
            return []

    async def get_all_chunks_with_embeddings(self) -> list[Chunk]:
        """Get all chunks that have embeddings (for similarity search).
        
        Returns:
            List of chunks with embeddings
        """
        cypher = """
        MATCH (c:Chunk)-[:PART_OF]->(m:Message)
        WHERE c.embedding IS NOT NULL AND size(c.embedding) > 0
        RETURN c.id as id, c.content as content, c.position as position,
               c.char_start as char_start, c.char_end as char_end,
               c.chunk_type as chunk_type, c.created_at as created_at,
               c.valid_at as valid_at, c.invalid_at as invalid_at,
               c.embedding as embedding, c.embedding_model as embedding_model,
               c.embedding_created_at as embedding_created_at,
               m.id as message_id
        ORDER BY c.created_at DESC
        """

        try:
            results, exec_time = await self.client.query(cypher, {})
            chunks = []
            for row in results:
                chunk = Chunk(
                    id=row["id"],
                    content=row["content"],
                    position=row["position"],
                    char_start=row["char_start"],
                    char_end=row["char_end"],
                    chunk_type=row.get("chunk_type", "paragraph"),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    valid_at=datetime.fromisoformat(row["valid_at"]),
                    invalid_at=datetime.fromisoformat(row["invalid_at"]) if row.get("invalid_at") else None,
                    embedding=row.get("embedding"),
                    embedding_model=row.get("embedding_model", "text-embedding-3-small"),
                    embedding_created_at=datetime.fromisoformat(row["embedding_created_at"]) if row.get("embedding_created_at") else None,
                    message_id=row["message_id"],
                )
                chunks.append(chunk)

            logger.info(
                f"Retrieved {len(chunks)} chunks with embeddings ({exec_time:.2f}ms)"
            )
            return chunks
        except Exception as e:
            logger.error(f"Failed to get chunks: {e}", exc_info=True)
            raise DatabaseError(f"Failed to retrieve chunks: {str(e)}")

    # ===== ENTITY OPERATIONS =====

    async def create_or_update_entity(self, entity: Entity) -> str:
        """Create entity or update if exists (by canonical_name + type).
        
        Args:
            entity: Entity object
            
        Returns:
            Entity ID
        """
        cypher = """
        MERGE (e:Entity {canonical_name: $canonical_name, type: $type})
        ON CREATE SET
            e.id = $id,
            e.name = $name,
            e.first_seen = $now,
            e.last_seen = $now,
            e.valid_at = $valid_at,
            e.invalid_at = $invalid_at,
            e.embedding = $embedding,
            e.embedding_model = $embedding_model,
            e.mention_count = 1,
            e.confidence = $confidence
        ON MATCH SET
            e.last_seen = $now,
            e.mention_count = e.mention_count + 1,
            e.confidence = (e.confidence + $confidence) / 2
        RETURN e.id as id
        """

        now = datetime.now().isoformat()
        params = {
            "id": entity.id,
            "name": entity.name,
            "canonical_name": entity.canonical_name,
            "type": entity.type,
            "now": now,
            "valid_at": entity.valid_at.isoformat(),
            "invalid_at": entity.invalid_at.isoformat() if entity.invalid_at else None,
            "embedding": entity.embedding or [],
            "embedding_model": entity.embedding_model,
            "confidence": entity.confidence,
        }

        try:
            results, _ = await self.client.query(cypher, params)
            entity_id = results[0]["id"] if results else entity.id
            logger.debug(f"Created/updated entity: {entity.canonical_name}")
            return entity_id
        except Exception as e:
            logger.error(f"Failed to create/update entity: {e}", exc_info=True)
            raise DatabaseError(f"Entity operation failed: {str(e)}")

    async def create_entities_batch(self, entities: list[Entity]) -> int:
        """Create/update multiple entities.
        
        Args:
            entities: List of entities
            
        Returns:
            Number processed
        """
        if not entities:
            return 0

        count = 0
        for entity in entities:
            try:
                await self.create_or_update_entity(entity)
                count += 1
            except DatabaseError as e:
                logger.error(f"Failed to process entity {entity.name}: {e}")
                continue

        logger.info(f"💾 Processed {count}/{len(entities)} entities")
        return count

    # ===== RELATIONSHIP OPERATIONS =====

    async def create_similarity_edge(
        self,
        chunk1_id: str,
        chunk2_id: str,
        similarity: float,
    ) -> None:
        """Create SIMILAR_TO relationship between chunks.
        
        Args:
            chunk1_id: First chunk ID
            chunk2_id: Second chunk ID
            similarity: Similarity score
        """
        cypher = """
        MATCH (c1:Chunk {id: $chunk1_id})
        MATCH (c2:Chunk {id: $chunk2_id})
        MERGE (c1)-[r:SIMILAR_TO]->(c2)
        SET r.similarity = $similarity,
            r.created_at = $created_at,
            r.algorithm = 'cosine'
        """

        params = {
            "chunk1_id": chunk1_id,
            "chunk2_id": chunk2_id,
            "similarity": similarity,
            "created_at": datetime.now().isoformat(),
        }

        try:
            await self.client.query(cypher, params)
        except Exception as e:
            logger.warning(f"Failed to create similarity edge: {e}")

    async def create_similarity_edges_batch(
        self,
        similar_chunks: list[SimilarChunk],
        source_chunk_id: str,
    ) -> int:
        """Create similarity edges for a chunk.
        
        Args:
            similar_chunks: List of similar chunks with scores
            source_chunk_id: Source chunk ID
            
        Returns:
            Number of edges created
        """
        count = 0
        for sc in similar_chunks:
            try:
                await self.create_similarity_edge(
                    chunk1_id=source_chunk_id,
                    chunk2_id=sc.chunk.id,
                    similarity=sc.similarity,
                )
                count += 1
            except Exception:
                continue

        return count

    async def link_chunk_to_entity(
        self,
        chunk_id: str,
        entity_id: str,
        position: int = 0,
        context: str = "",
        confidence: float = 1.0,
    ) -> None:
        """Create MENTIONS relationship between chunk and entity.
        
        Args:
            chunk_id: Chunk ID
            entity_id: Entity ID
            position: Position in chunk
            context: Surrounding text
            confidence: Confidence score
        """
        cypher = """
        MATCH (c:Chunk {id: $chunk_id})
        MATCH (e:Entity {id: $entity_id})
        MERGE (c)-[r:MENTIONS]->(e)
        SET r.position = $position,
            r.context = $context,
            r.confidence = $confidence
        """

        params = {
            "chunk_id": chunk_id,
            "entity_id": entity_id,
            "position": position,
            "context": context,
            "confidence": confidence,
        }

        try:
            await self.client.query(cypher, params)
        except Exception as e:
            logger.warning(f"Failed to link chunk to entity: {e}")

    async def link_message_to_entity(
        self,
        message_id: str,
        entity_id: str,
        mention_count: int = 1,
        salience: float = 0.5,
    ) -> None:
        """Create DISCUSSES relationship between message and entity.
        
        Args:
            message_id: Message ID
            entity_id: Entity ID
            mention_count: How many times mentioned
            salience: Importance (0.0-1.0)
        """
        cypher = """
        MATCH (m:Message {id: $message_id})
        MATCH (e:Entity {id: $entity_id})
        MERGE (m)-[r:DISCUSSES]->(e)
        SET r.mention_count = $mention_count,
            r.salience = $salience,
            r.created_at = $created_at
        """

        params = {
            "message_id": message_id,
            "entity_id": entity_id,
            "mention_count": mention_count,
            "salience": salience,
            "created_at": datetime.now().isoformat(),
        }

        try:
            await self.client.query(cypher, params)
        except Exception as e:
            logger.warning(f"Failed to link message to entity: {e}")

    # ===== QUERY OPERATIONS =====

    async def get_recent_messages(
        self,
        reference_time: datetime | None = None,
        limit: int = 10,
    ) -> list[ChatMessage]:
        """Get recent messages using temporal query (NO session filter).
        
        Args:
            reference_time: Reference point in time (default: now)
            limit: Maximum messages
            
        Returns:
            List of recent messages
        """
        if reference_time is None:
            reference_time = datetime.now()

        cypher = """
        MATCH (m:Message)
        WHERE m.timestamp < $reference_time
          AND m.valid_at <= $reference_time
          AND (m.invalid_at IS NULL OR m.invalid_at > $reference_time)
        RETURN m
        ORDER BY m.timestamp DESC
        LIMIT $limit
        """

        params = {
            "reference_time": reference_time.isoformat(),
            "limit": limit,
        }

        try:
            results, _ = await self.client.query(cypher, params)
            messages = []
            for r in results:
                row = r["m"]
                messages.append(ChatMessage(
                    id=row["id"],
                    content=row["content"],
                    role=row["role"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    session_id=row.get("session_id", ""),
                    status=row.get("status", "recorded"),
                    metadata={},
                ))
            return messages
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []



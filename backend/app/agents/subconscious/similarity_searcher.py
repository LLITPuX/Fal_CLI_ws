"""Similarity search using cosine distance.

Uses in-memory computation with NumPy/scikit-learn for now.
Can be upgraded to Redis VSS or Qdrant for better performance at scale.
"""

import logging
from datetime import datetime, timedelta

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.agents.subconscious.schemas import Chunk, SimilarChunk

logger = logging.getLogger(__name__)


class SimilaritySearcher:
    """Find similar chunks using cosine similarity.
    
    Current implementation: in-memory computation (good for <10K chunks)
    Future: Redis Stack VSS or Qdrant for >10K chunks
    """

    def __init__(
        self,
        threshold: float = 0.7,
        time_window_days: int | None = None,
    ):
        """Initialize similarity searcher.
        
        Args:
            threshold: Minimum similarity score (0.0-1.0)
            time_window_days: Only search chunks from last N days (None = all time)
        """
        self.threshold = threshold
        self.time_window_days = time_window_days
        
        logger.info(
            f"🔍 Similarity searcher initialized "
            f"(threshold={threshold}, time_window={time_window_days})"
        )

    async def find_similar_chunks(
        self,
        query_embedding: list[float],
        candidate_chunks: list[Chunk],
        top_k: int = 10,
        exclude_message_id: str | None = None,
    ) -> list[SimilarChunk]:
        """Find most similar chunks to query.
        
        Args:
            query_embedding: Vector to compare against
            candidate_chunks: Chunks to search through
            top_k: Maximum number of results
            exclude_message_id: Don't include chunks from this message
            
        Returns:
            List of similar chunks with scores, sorted by similarity (desc)
        """
        if not candidate_chunks:
            logger.warning("No candidate chunks provided")
            return []
        
        # Filter by time window if specified
        if self.time_window_days:
            cutoff = datetime.now() - timedelta(days=self.time_window_days)
            candidate_chunks = [
                c for c in candidate_chunks
                if c.created_at >= cutoff
            ]
            logger.debug(
                f"Filtered to {len(candidate_chunks)} chunks within {self.time_window_days} days"
            )
        
        # Filter out chunks without embeddings
        chunks_with_embeddings = [
            c for c in candidate_chunks
            if c.embedding is not None
        ]
        
        if not chunks_with_embeddings:
            logger.warning("No chunks with embeddings found")
            return []
        
        # Exclude chunks from same message (self-similarity)
        if exclude_message_id:
            chunks_with_embeddings = [
                c for c in chunks_with_embeddings
                if c.message_id != exclude_message_id
            ]
        
        logger.info(
            f"🔍 Searching {len(chunks_with_embeddings)} chunks "
            f"for top-{top_k} similar..."
        )
        
        # Convert to numpy arrays
        query_vector = np.array([query_embedding])
        chunk_vectors = np.array([c.embedding for c in chunks_with_embeddings])
        
        # Compute cosine similarity
        similarities = cosine_similarity(query_vector, chunk_vectors)[0]
        
        # Filter by threshold
        mask = similarities >= self.threshold
        filtered_indices = np.where(mask)[0]
        
        if len(filtered_indices) == 0:
            logger.info(f"No chunks above threshold {self.threshold}")
            return []
        
        filtered_similarities = similarities[filtered_indices]
        
        # Get top-K
        if len(filtered_indices) > top_k:
            # Sort and take top-K
            top_indices = filtered_similarities.argsort()[-top_k:][::-1]
            result_indices = filtered_indices[top_indices]
            result_similarities = filtered_similarities[top_indices]
        else:
            # All filtered results
            sorted_order = filtered_similarities.argsort()[::-1]
            result_indices = filtered_indices[sorted_order]
            result_similarities = filtered_similarities[sorted_order]
        
        # Build result list
        results = []
        for idx, similarity in zip(result_indices, result_similarities):
            chunk = chunks_with_embeddings[idx]
            results.append(
                SimilarChunk(
                    chunk=chunk,
                    similarity=float(similarity),
                )
            )
        
        logger.info(
            f"✅ Found {len(results)} similar chunks "
            f"(avg similarity: {np.mean(result_similarities):.3f})"
        )
        
        return results

    async def find_similar_for_multiple(
        self,
        chunks: list[Chunk],
        candidate_chunks: list[Chunk],
        top_k_per_chunk: int = 5,
        max_total: int = 10,
        exclude_message_id: str | None = None,
    ) -> list[SimilarChunk]:
        """Find similar chunks for multiple query chunks.
        
        Useful when you have multiple chunks from a message and want to find
        all related chunks, then deduplicate and rank.
        
        Args:
            chunks: Query chunks
            candidate_chunks: Chunks to search
            top_k_per_chunk: How many similar chunks per query
            max_total: Maximum total results after deduplication
            exclude_message_id: Don't include chunks from this message
            
        Returns:
            Deduplicated and ranked list of similar chunks
        """
        if not chunks:
            return []
        
        logger.info(
            f"🔍 Finding similar chunks for {len(chunks)} query chunks..."
        )
        
        # Find similar for each chunk
        all_similar: dict[str, SimilarChunk] = {}  # chunk_id -> best SimilarChunk
        
        for chunk in chunks:
            if chunk.embedding is None:
                continue
            
            similar = await self.find_similar_chunks(
                query_embedding=chunk.embedding,
                candidate_chunks=candidate_chunks,
                top_k=top_k_per_chunk,
                exclude_message_id=exclude_message_id,
            )
            
            # Merge results (keep best similarity for each chunk)
            for sc in similar:
                chunk_id = sc.chunk.id
                if chunk_id not in all_similar or sc.similarity > all_similar[chunk_id].similarity:
                    all_similar[chunk_id] = sc
        
        # Sort by similarity and take top-N
        sorted_similar = sorted(
            all_similar.values(),
            key=lambda x: x.similarity,
            reverse=True,
        )[:max_total]
        
        logger.info(
            f"✅ Found {len(sorted_similar)} unique similar chunks "
            f"(from {len(all_similar)} total matches)"
        )
        
        return sorted_similar


# Singleton instance
_searcher_instance: SimilaritySearcher | None = None


def get_similarity_searcher(
    threshold: float | None = None,
    time_window_days: int | None = None,
) -> SimilaritySearcher:
    """Get or create similarity searcher instance.
    
    Args:
        threshold: Minimum similarity score
        time_window_days: Time window for search
        
    Returns:
        SimilaritySearcher instance
    """
    global _searcher_instance
    
    # Create new if params changed or not exists
    if _searcher_instance is None or (
        threshold is not None and threshold != _searcher_instance.threshold
    ):
        from app.core.config import settings
        _searcher_instance = SimilaritySearcher(
            threshold=threshold or settings.subconscious_similarity_threshold,
            time_window_days=time_window_days or settings.subconscious_default_time_window_days,
        )
    
    return _searcher_instance


"""OpenAI embeddings service with batch processing."""

import logging
from datetime import datetime
from typing import Any

from openai import AsyncOpenAI, OpenAIError

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Generate vector embeddings using OpenAI API.
    
    Supports batch processing for efficient API usage.
    Uses text-embedding-3-small model (1536 dimensions).
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
    ):
        """Initialize embeddings service.
        
        Args:
            api_key: OpenAI API key (default from settings)
            model: Embedding model (default text-embedding-3-small)
            dimensions: Output dimensions (default 1536)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_embedding_model
        self.dimensions = dimensions or settings.openai_embedding_dimensions
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        logger.info(
            f"🔢 Embeddings service initialized "
            f"(model={self.model}, dimensions={self.dimensions})"
        )

    async def generate(self, text: str) -> list[float]:
        """Generate embedding for single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (list of floats)
            
        Raises:
            EmbeddingError: If API call fails
        """
        embeddings = await self.generate_batch([text])
        return embeddings[0]

    async def generate_batch(
        self,
        texts: list[str],
        batch_size: int | None = None,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts (batch).
        
        OpenAI allows up to 2048 inputs per request. We batch accordingly.
        
        Args:
            texts: List of texts to embed
            batch_size: Maximum texts per API call (default from settings)
            
        Returns:
            List of embedding vectors in same order as input
            
        Raises:
            EmbeddingError: If API call fails
        """
        if not texts:
            return []
        
        batch_size = batch_size or settings.subconscious_batch_size
        
        logger.info(f"🔢 Generating embeddings for {len(texts)} texts...")
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    dimensions=self.dimensions,
                )
                
                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                logger.debug(
                    f"Generated embeddings for batch {i // batch_size + 1} "
                    f"({len(batch)} texts)"
                )
                
            except OpenAIError as e:
                logger.error(f"OpenAI API error: {e}", exc_info=True)
                raise EmbeddingError(f"Failed to generate embeddings: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                raise EmbeddingError(f"Embedding generation failed: {e}")
        
        logger.info(
            f"✅ Generated {len(all_embeddings)} embeddings "
            f"(dim={len(all_embeddings[0])})"
        )
        
        return all_embeddings

    async def embed_chunks(
        self,
        chunks: list[Any],  # list[Chunk] but avoid circular import
    ) -> None:
        """Generate and attach embeddings to chunks in-place.
        
        Modifies chunks by adding embedding vectors.
        
        Args:
            chunks: List of Chunk objects
        """
        if not chunks:
            return
        
        # Extract texts
        texts = [chunk.content for chunk in chunks]
        
        # Generate embeddings
        embeddings = await self.generate_batch(texts)
        
        # Attach to chunks
        now = datetime.now()
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
            chunk.embedding_model = self.model
            chunk.embedding_created_at = now
        
        logger.info(f"✅ Embedded {len(chunks)} chunks")


class EmbeddingError(Exception):
    """Error during embedding generation."""

    pass


# Singleton instance
_service_instance: EmbeddingsService | None = None


def get_embeddings_service() -> EmbeddingsService:
    """Get or create embeddings service instance.
    
    Returns:
        EmbeddingsService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = EmbeddingsService()
    return _service_instance


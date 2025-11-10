"""LangGraph nodes for Subconscious Agent."""

import logging
import time
from datetime import datetime

from app.agents.subconscious.context_formatter import ContextFormatter
from app.agents.subconscious.embeddings_service import EmbeddingsService, get_embeddings_service
from app.agents.subconscious.entity_extractor import EntityExtractor, get_entity_extractor
from app.agents.subconscious.repository import SubconsciousRepository
from app.agents.subconscious.similarity_searcher import SimilaritySearcher, get_similarity_searcher
from app.agents.subconscious.text_processor import SemanticTextSplitter, get_text_splitter
from app.core.config import settings

logger = logging.getLogger(__name__)


async def subconscious_analyze_node(
    state: dict,
    repository: SubconsciousRepository,
    text_splitter: SemanticTextSplitter | None = None,
    embeddings_service: EmbeddingsService | None = None,
    entity_extractor: EntityExtractor | None = None,
    similarity_searcher: SimilaritySearcher | None = None,
    context_formatter: ContextFormatter | None = None,
) -> dict:
    """Subconscious node: Analyze message and build rich context.
    
    Full pipeline:
    1. Check if message was recorded by Clerk
    2. Split text into semantic chunks
    3. Generate embeddings (OpenAI batch)
    4. Extract entities (OpenAI structured)
    5. Find similar chunks/entities in graph
    6. Build context for Orchestrator
    7. Save everything to graph
    
    Args:
        state: Current graph state
        repository: Subconscious repository
        text_splitter: Text processor (optional, will use singleton)
        embeddings_service: Embeddings service (optional, will use singleton)
        entity_extractor: Entity extractor (optional, will use singleton)
        similarity_searcher: Similarity searcher (optional, will use singleton)
        context_formatter: Context formatter (optional, will create)
        
    Returns:
        Updated state with context
    """
    logger.info("🧠 Підсвідомість: Починаю аналіз...")
    start_time = time.time()

    # Initialize services (singletons if not provided)
    text_splitter = text_splitter or get_text_splitter(
        max_chunk_size=settings.subconscious_chunk_size,
        overlap_percentage=settings.subconscious_chunk_overlap,
    )
    embeddings_service = embeddings_service or get_embeddings_service()
    entity_extractor = entity_extractor or get_entity_extractor()
    similarity_searcher = similarity_searcher or get_similarity_searcher()
    context_formatter = context_formatter or ContextFormatter(repository)

    try:
        # 0. Validate input
        if not state.get("recorded"):
            logger.warning("⚠️ Message not recorded by Clerk, skipping analysis")
            state["analyzed"] = False
            state["context"] = {}
            return state

        message_id = state.get("message_id")
        if not message_id:
            raise ValueError("message_id not found in state")

        # Get message data from state (already available from Clerk)
        message_content = state.get("message_content")
        message_role = state.get("message_role", "user")
        
        if not message_content:
            raise ValueError("message_content not found in state")

        # Create message object for context builder
        from app.agents.clerk.schemas import ChatMessage
        current_message = ChatMessage(
            id=message_id,
            content=message_content,
            role=message_role,
            timestamp=datetime.now(),
            session_id=state.get("session_id", ""),
        )

        logger.info(f"🧠 Analyzing message: {message_id} ({len(message_content)} chars)")

        # 1. SEMANTIC CHUNKING
        logger.info("📄 Step 1/5: Semantic chunking...")
        chunks = await text_splitter.split(message_content, message_id=message_id)
        logger.info(f"✅ Created {len(chunks)} semantic chunks")

        if not chunks:
            logger.warning("No chunks created, using full message as single chunk")
            from app.agents.subconscious.schemas import Chunk
            chunks = [Chunk(
                content=message_content,
                position=0,
                char_start=0,
                char_end=len(message_content),
                message_id=message_id,
            )]

        # 2. GENERATE EMBEDDINGS
        logger.info("🔢 Step 2/5: Generating embeddings...")
        await embeddings_service.embed_chunks(chunks)
        logger.info(f"✅ Generated embeddings for {len(chunks)} chunks")

        # 3. EXTRACT ENTITIES
        logger.info("🏷️ Step 3/5: Extracting entities...")
        extracted_entities = await entity_extractor.extract(message_content)
        logger.info(f"✅ Extracted {len(extracted_entities)} entities")

        # Convert to Entity objects with normalization
        entities = [entity_extractor.to_entity(e) for e in extracted_entities]

        # 4. FIND SIMILAR CHUNKS
        logger.info("🔍 Step 4/5: Finding similar chunks...")
        
        # Get all existing chunks from DB
        all_chunks = await repository.get_all_chunks_with_embeddings()
        logger.info(f"Searching through {len(all_chunks)} existing chunks...")

        # Find similar for all current chunks, then deduplicate
        similar_results = await similarity_searcher.find_similar_for_multiple(
            chunks=chunks,
            candidate_chunks=all_chunks,
            top_k_per_chunk=5,
            max_total=settings.subconscious_max_similar_chunks,
            exclude_message_id=message_id,
        )
        
        avg_sim = (sum(s.similarity for s in similar_results) / len(similar_results)) if similar_results else 0.0
        logger.info(
            f"✅ Found {len(similar_results)} similar chunks "
            f"(avg similarity: {avg_sim:.3f})"
        )

        # 5. BUILD CONTEXT
        logger.info("📋 Step 5/5: Building context...")
        context = await context_formatter.build_context(
            message=current_message,
            chunks=chunks,
            entities=entities,
            similar_chunks=similar_results,
        )
        
        # Add processing time
        processing_time = (time.time() - start_time) * 1000
        context.processing_time_ms = processing_time

        # 6. SAVE TO GRAPH
        logger.info("💾 Saving to graph...")
        
        # Save chunks
        await repository.create_chunks_batch(chunks)
        
        # Save entities
        entity_ids = []
        for entity in entities:
            entity_id = await repository.create_or_update_entity(entity)
            entity_ids.append(entity_id)
        
        # Create chunk → entity relationships
        for chunk in chunks:
            for entity_id in entity_ids:
                await repository.link_chunk_to_entity(
                    chunk_id=chunk.id,
                    entity_id=entity_id,
                    confidence=0.9,  # High confidence since we extracted them
                )
        
        # Create message → entity relationships
        for entity_id in entity_ids:
            await repository.link_message_to_entity(
                message_id=message_id,
                entity_id=entity_id,
                mention_count=1,
                salience=0.5,
            )
        
        # Create similarity edges
        for chunk in chunks:
            if chunk.embedding:
                # Find which similar chunks are similar to this chunk
                chunk_similar = await similarity_searcher.find_similar_chunks(
                    query_embedding=chunk.embedding,
                    candidate_chunks=all_chunks,
                    top_k=5,
                    exclude_message_id=message_id,
                )
                await repository.create_similarity_edges_batch(
                    similar_chunks=chunk_similar,
                    source_chunk_id=chunk.id,
                )
        
        logger.info("✅ Saved to graph")

        # 7. UPDATE STATE
        state["context"] = context.model_dump()
        state["analyzed"] = True
        state["error"] = None

        logger.info(
            f"🧠 Підсвідомість завершила аналіз: "
            f"{len(chunks)} chunks, {len(entities)} entities, "
            f"{len(similar_results)} similar, "
            f"continuity={context.conversation_continuity:.2f}, "
            f"time={processing_time:.0f}ms"
        )

    except Exception as e:
        logger.error(f"🧠 Підсвідомість: Помилка аналізу: {e}", exc_info=True)
        
        # Graceful degradation - minimal context
        state["analyzed"] = False
        state["error"] = f"Analysis failed: {str(e)}"
        
        # Provide empty context so Orchestrator can still function
        from app.agents.subconscious.schemas import ContextAnalysis
        state["context"] = ContextAnalysis().model_dump()

    return state


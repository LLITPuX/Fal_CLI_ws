"""Semantic text chunking logic.

Splits text by semantic boundaries (paragraphs, sentences) rather than
fixed-size chunks for better context preservation.
"""

import logging
import re
from typing import Literal

from app.agents.subconscious.schemas import Chunk

logger = logging.getLogger(__name__)


class SemanticTextSplitter:
    """Split text по смислових границях (semantic boundaries).
    
    Uses recursive splitting strategy:
    1. Try to split by paragraphs (\n\n)
    2. If chunk too large, split by sentences
    3. If sentence too large, split by words
    
    Adds overlap between chunks to preserve context.
    """

    def __init__(
        self,
        max_chunk_size: int = 800,
        overlap_percentage: float = 0.15,
    ):
        """Initialize text splitter.
        
        Args:
            max_chunk_size: Maximum characters per chunk
            overlap_percentage: Overlap between chunks (0.0-1.0)
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = int(max_chunk_size * overlap_percentage)
        
        # Recursive separators (priority order)
        self.separators = [
            "\n\n",  # Paragraphs (highest priority)
            "\n",    # Lines
            ". ",    # Sentences
            "! ",
            "? ",
            "; ",
            ": ",
            ", ",
            " ",     # Words (lowest priority)
        ]

    async def split(self, text: str, message_id: str | None = None) -> list[Chunk]:
        """Split text into semantic chunks.
        
        Args:
            text: Text to split
            message_id: Optional parent message ID
            
        Returns:
            List of Chunk objects with positions and types
        """
        if not text or not text.strip():
            return []
        
        # Recursively split text
        chunks_text = self._recursive_split(text.strip(), self.max_chunk_size)
        
        # Convert to Chunk objects
        chunks = []
        char_position = 0
        
        for i, chunk_text in enumerate(chunks_text):
            # Find actual position in original text (accounting for overlap)
            if i == 0:
                char_position = text.find(chunk_text)
            else:
                # Search from previous position
                char_position = text.find(chunk_text, char_position)
            
            if char_position == -1:
                # Fallback if not found (shouldn't happen)
                char_position = sum(len(c) for c in chunks_text[:i])
            
            chunk_type = self._detect_chunk_type(chunk_text)
            
            chunk = Chunk(
                content=chunk_text,
                position=i,
                char_start=char_position,
                char_end=char_position + len(chunk_text),
                chunk_type=chunk_type,
                message_id=message_id,
            )
            chunks.append(chunk)
            
            # Move position forward
            char_position += len(chunk_text)
        
        logger.info(
            f"Split text into {len(chunks)} semantic chunks "
            f"(avg size: {sum(len(c.content) for c in chunks) / len(chunks):.0f} chars)"
        )
        
        return chunks

    def _recursive_split(
        self,
        text: str,
        max_size: int,
        separator_index: int = 0,
    ) -> list[str]:
        """Recursively split text using separator hierarchy.
        
        Args:
            text: Text to split
            max_size: Maximum chunk size
            separator_index: Current separator in hierarchy
            
        Returns:
            List of text chunks
        """
        # Base case: text fits in one chunk
        if len(text) <= max_size:
            return [text] if text else []
        
        # Try current separator
        if separator_index >= len(self.separators):
            # No more separators, force split by size
            return self._force_split(text, max_size)
        
        separator = self.separators[separator_index]
        parts = text.split(separator)
        
        if len(parts) == 1:
            # Separator not found, try next one
            return self._recursive_split(text, max_size, separator_index + 1)
        
        # Merge parts into chunks with overlap
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, part in enumerate(parts):
            part_with_sep = part + (separator if i < len(parts) - 1 else "")
            part_size = len(part_with_sep)
            
            if current_size + part_size <= max_size:
                # Add to current chunk
                current_chunk.append(part_with_sep)
                current_size += part_size
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunk_text = "".join(current_chunk)
                    
                    # If chunk still too large, split recursively
                    if len(chunk_text) > max_size:
                        chunks.extend(
                            self._recursive_split(
                                chunk_text, max_size, separator_index + 1
                            )
                        )
                    else:
                        chunks.append(chunk_text)
                
                # Start new chunk with overlap
                if chunks and self.overlap_size > 0:
                    # Add last N chars from previous chunk as overlap
                    overlap = chunks[-1][-self.overlap_size:]
                    current_chunk = [overlap, part_with_sep]
                    current_size = len(overlap) + part_size
                else:
                    current_chunk = [part_with_sep]
                    current_size = part_size
        
        # Don't forget last chunk
        if current_chunk:
            chunk_text = "".join(current_chunk)
            if len(chunk_text) > max_size:
                chunks.extend(
                    self._recursive_split(chunk_text, max_size, separator_index + 1)
                )
            else:
                chunks.append(chunk_text)
        
        return chunks

    def _force_split(self, text: str, max_size: int) -> list[str]:
        """Force split text by character count (last resort).
        
        Args:
            text: Text to split
            max_size: Maximum chunk size
            
        Returns:
            List of chunks
        """
        chunks = []
        for i in range(0, len(text), max_size - self.overlap_size):
            chunk = text[i : i + max_size]
            if chunk:
                chunks.append(chunk)
        return chunks

    def _detect_chunk_type(
        self, text: str
    ) -> Literal["paragraph", "sentence", "code", "heading"]:
        """Detect semantic type of chunk.
        
        Args:
            text: Chunk text
            
        Returns:
            Type of chunk
        """
        text_stripped = text.strip()
        
        # Markdown heading
        if re.match(r"^#{1,6}\s+", text_stripped):
            return "heading"
        
        # Code block
        if text_stripped.startswith("```") or text_stripped.startswith("    "):
            return "code"
        
        # Single sentence (short, no newlines)
        if "\n" not in text_stripped and len(text_stripped) < 200:
            return "sentence"
        
        # Default: paragraph
        return "paragraph"


# Singleton instance
_splitter_instance: SemanticTextSplitter | None = None


def get_text_splitter(
    max_chunk_size: int = 800,
    overlap_percentage: float = 0.15,
) -> SemanticTextSplitter:
    """Get or create text splitter instance.
    
    Args:
        max_chunk_size: Maximum characters per chunk
        overlap_percentage: Overlap between chunks
        
    Returns:
        SemanticTextSplitter instance
    """
    global _splitter_instance
    if _splitter_instance is None:
        _splitter_instance = SemanticTextSplitter(max_chunk_size, overlap_percentage)
    return _splitter_instance


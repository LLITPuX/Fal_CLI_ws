"""OpenAI entity extraction service."""

import json
import logging
import re

from openai import AsyncOpenAI, OpenAIError

from app.agents.subconscious.schemas import Entity, ExtractedEntity
from app.core.config import settings

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract named entities using OpenAI structured output.
    
    Uses GPT-4o-mini with JSON mode for fast and cheap entity extraction.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        """Initialize entity extractor.
        
        Args:
            api_key: OpenAI API key (default from settings)
            model: Model to use (default gpt-4o-mini)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_entity_model
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        logger.info(f"🏷️ Entity extractor initialized (model={self.model})")

    async def extract(self, text: str) -> list[ExtractedEntity]:
        """Extract named entities from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted entities
            
        Raises:
            EntityExtractionError: If extraction fails
        """
        if not text or not text.strip():
            return []
        
        logger.info(f"🏷️ Extracting entities from text ({len(text)} chars)...")
        
        prompt = self._build_prompt(text)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,  # Deterministic output
                max_tokens=2000,
            )
            
            content = response.choices[0].message.content
            if not content:
                logger.warning("Empty response from OpenAI")
                return []
            
            # Parse JSON response
            data = json.loads(content)
            
            if "entities" not in data:
                logger.warning(f"No 'entities' field in response: {data}")
                return []
            
            # Convert to ExtractedEntity objects
            entities = []
            for item in data["entities"]:
                try:
                    entity = ExtractedEntity(
                        name=item["name"],
                        type=item["type"],
                        confidence=float(item.get("confidence", 1.0)),
                        context=item.get("context", ""),
                    )
                    entities.append(entity)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid entity: {item} ({e})")
                    continue
            
            logger.info(f"✅ Extracted {len(entities)} entities")
            return entities
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise EntityExtractionError(f"Failed to extract entities: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}", exc_info=True)
            raise EntityExtractionError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise EntityExtractionError(f"Entity extraction failed: {e}")

    def _build_prompt(self, text: str) -> str:
        """Build extraction prompt.
        
        Args:
            text: Input text
            
        Returns:
            Prompt string
        """
        return f"""Extract all named entities from the following text.

**Categories:**
- PERSON: People, characters, names
- ORG: Organizations, companies, teams, groups
- LOCATION: Countries, cities, places, regions
- TECH: Technologies, programming languages, frameworks, tools, software
- CONCEPT: Abstract concepts, methodologies, theories, approaches
- EVENT: Events, conferences, meetings, milestones

**Instructions:**
1. Extract entities that are clearly mentioned in the text
2. For each entity, provide:
   - name: exact text from input (preserve capitalization)
   - type: one of the categories above
   - confidence: 0.0-1.0 (how confident you are this is the right type)
   - context: 3-5 surrounding words for disambiguation

3. Return JSON in this format:
{{
    "entities": [
        {{"name": "Docker", "type": "TECH", "confidence": 0.95, "context": "using Docker containers"}},
        {{"name": "Google", "type": "ORG", "confidence": 1.0, "context": "works at Google"}}
    ]
}}

**Text to analyze:**
{text}

Return ONLY valid JSON, no markdown, no explanations."""

    def normalize_entity_name(self, name: str, entity_type: str) -> str:
        """Normalize entity name for grouping/deduplication.
        
        Args:
            name: Original entity name
            entity_type: Entity type
            
        Returns:
            Canonical name (lowercase, trimmed)
        """
        canonical = name.lower().strip()
        
        # Type-specific normalization
        if entity_type == "TECH":
            # Remove version numbers
            canonical = re.sub(r'\s+\d+(\.\d+)*', '', canonical)
            canonical = re.sub(r'\s+v\d+', '', canonical)
            
            # Known aliases
            aliases = {
                "k8s": "kubernetes",
                "js": "javascript",
                "ts": "typescript",
                "py": "python",
                "docker-compose": "docker compose",
            }
            canonical = aliases.get(canonical, canonical)
        
        elif entity_type == "ORG":
            # Remove common suffixes
            canonical = re.sub(r'\s+(inc|llc|ltd|corp|corporation)\.?$', '', canonical)
        
        return canonical

    def to_entity(self, extracted: ExtractedEntity) -> Entity:
        """Convert ExtractedEntity to Entity for storage.
        
        Args:
            extracted: Extracted entity from OpenAI
            
        Returns:
            Entity object
        """
        canonical = self.normalize_entity_name(extracted.name, extracted.type)
        
        return Entity(
            name=extracted.name,
            canonical_name=canonical,
            type=extracted.type,
            confidence=extracted.confidence,
        )


class EntityExtractionError(Exception):
    """Error during entity extraction."""

    pass


# Singleton instance
_extractor_instance: EntityExtractor | None = None


def get_entity_extractor() -> EntityExtractor:
    """Get or create entity extractor instance.
    
    Returns:
        EntityExtractor instance
    """
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = EntityExtractor()
    return _extractor_instance


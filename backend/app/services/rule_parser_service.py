"""Service for parsing .mdc documents into structured rules using LLM."""

import hashlib
import json
import logging
from pathlib import Path
from typing import List, Optional

from app.core.config import settings
from app.core.exceptions import CLIExecutionError, JSONParsingError
from app.models.rule_schemas import ParsedRulesResponse, RuleCacheEntry, RuleSchema
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class RuleParserService:
    """Parse .mdc documents into structured rules using Gemini LLM."""

    def __init__(self, gemini_service: Optional[GeminiService] = None):
        """Initialize rule parser service.

        Args:
            gemini_service: Optional GeminiService instance (creates new if None)
        """
        self.gemini = gemini_service or GeminiService()
        self.cache_dir = Path(settings.default_output_dir) / "rule_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _build_rule_parsing_prompt(self, content: str) -> str:
        """Build prompt for Gemini to parse document into rules.

        Args:
            content: Full document content

        Returns:
            Formatted prompt string
        """
        schema = """
{
  "rules": [
    {
      "id": "string - unique rule identifier (e.g., 'rule_docker_multistage_1')",
      "title": "string - concise, descriptive rule title",
      "content": "string - full rule text including context, explanations, and code examples",
      "rule_type": "best_practice|pattern|anti_pattern|guideline",
      "priority": "high|medium|low",
      "entities": ["array of strings - technologies, concepts, tools mentioned (e.g., 'Docker', 'FastAPI', 'Nginx')"],
      "contexts": ["array of strings - where rule applies: 'frontend', 'backend', 'server', 'container', 'database', 'api', etc."],
      "source_section": "string - section heading from document (e.g., 'Multi-stage Builds')",
      "code_examples": ["array of strings - code snippets if present in rule"]
    }
  ]
}
"""

        return (
            "You are an expert technical documentation analyzer specializing in extracting "
            "development rules and best practices from technical documentation.\n\n"
            "TASK: Analyze the provided documentation and extract logical, actionable rules. "
            "Each rule should be a complete, self-contained guideline that developers can follow.\n\n"
            "OUTPUT SCHEMA:\n"
            f"{schema}\n\n"
            "REQUIREMENTS:\n"
            "- Extract rules that are specific, actionable, and complete\n"
            "- Include full context: explanations, code examples, and rationale\n"
            "- Identify ALL relevant entities (technologies, tools, concepts)\n"
            "- Identify ALL contexts where rule applies (frontend, backend, server, etc.)\n"
            "- Set priority based on importance: 'high' for critical rules, 'medium' for important, 'low' for optional\n"
            "- Set rule_type: 'best_practice' for recommended approaches, 'pattern' for design patterns, "
            "'anti_pattern' for things to avoid, 'guideline' for general guidance\n"
            "- Extract code examples as separate strings in code_examples array\n"
            "- Each rule should have unique ID based on content hash\n\n"
            "CONTEXT EXTRACTION:\n"
            "- Look for keywords: 'frontend', 'backend', 'server', 'container', 'database', 'api', 'cli', etc.\n"
            "- If rule mentions specific technologies (React, FastAPI, Docker), include them in entities\n"
            "- If rule applies to multiple contexts, include all of them\n\n"
            "Return ONLY valid JSON matching the schema. No markdown, no explanations.\n\n"
            f"DOCUMENT CONTENT:\n{content}\n"
        )

    def _get_cache_path(self, content_hash: str) -> Path:
        """Get cache file path for content hash.

        Args:
            content_hash: SHA256 hash of document content

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{content_hash}.json"

    def _load_from_cache(self, content_hash: str) -> Optional[List[RuleSchema]]:
        """Load parsed rules from cache.

        Args:
            content_hash: SHA256 hash of document content

        Returns:
            List of rules if cached, None otherwise
        """
        cache_path = self._get_cache_path(content_hash)
        if not cache_path.exists():
            return None

        try:
            cache_data = json.loads(cache_path.read_text(encoding="utf-8"))
            cache_entry = RuleCacheEntry(**cache_data)
            logger.info(
                f"📦 Loaded {len(cache_entry.rules)} rules from cache "
                f"(parsed at {cache_entry.parsed_at})"
            )
            return cache_entry.rules
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def _save_to_cache(
        self, content_hash: str, file_path: str, rules: List[RuleSchema]
    ):
        """Save parsed rules to cache.

        Args:
            content_hash: SHA256 hash of document content
            file_path: Source file path
            rules: List of parsed rules
        """
        from datetime import datetime

        cache_path = self._get_cache_path(content_hash)
        cache_entry = RuleCacheEntry(
            file_path=file_path,
            content_hash=content_hash,
            rules=rules,
            parsed_at=datetime.now().isoformat(),
        )

        try:
            cache_path.write_text(
                cache_entry.model_dump_json(indent=2), encoding="utf-8"
            )
            logger.info(f"💾 Cached {len(rules)} rules to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    async def parse_document_to_rules(
        self, content: str, file_path: str, use_cache: bool = True
    ) -> List[RuleSchema]:
        """Parse document content into structured rules.

        Args:
            content: Full document content
            file_path: Source file path (for logging/caching)
            use_cache: Whether to use cache if available

        Returns:
            List of parsed rules

        Raises:
            CLIExecutionError: If LLM parsing fails
            JSONParsingError: If JSON parsing fails
        """
        # Calculate content hash for caching
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Try cache first
        if use_cache:
            cached_rules = self._load_from_cache(content_hash)
            if cached_rules:
                return cached_rules

        logger.info(f"🤖 Parsing {file_path} with Gemini...")

        try:
            # Build prompt
            prompt = self._build_rule_parsing_prompt(content)

            # Call Gemini
            output, processing_time = await self.gemini.run_cli(prompt)
            logger.info(f"✅ Gemini parsing completed in {processing_time:.2f}s")

            # Extract JSON
            json_data = self.gemini.extract_json(output)

            # Validate and parse
            parsed_response = ParsedRulesResponse(**json_data)
            rules = parsed_response.rules

            logger.info(f"📋 Extracted {len(rules)} rules from {file_path}")

            # Save to cache
            if use_cache:
                self._save_to_cache(content_hash, file_path, rules)

            return rules

        except (CLIExecutionError, JSONParsingError) as e:
            logger.error(f"❌ LLM parsing failed: {e}")
            logger.info("🔄 Falling back to simple parser...")
            # Fallback to simple parser
            return self._parse_with_fallback(content, file_path)

    def _parse_with_fallback(
        self, content: str, file_path: str
    ) -> List[RuleSchema]:
        """Fallback parser when LLM is unavailable.

        Uses simple heuristics to extract rules:
        - Looks for **Rule:** markers
        - Extracts sections with ### headings
        - Basic entity/context extraction

        Args:
            content: Full document content
            file_path: Source file path

        Returns:
            List of parsed rules
        """
        import re
        from datetime import datetime

        logger.info(f"📝 Using fallback parser for {file_path}")

        rules = []
        lines = content.split("\n")

        # Remove frontmatter
        content_clean = re.sub(
            r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL
        )

        # Split by sections (## or ###)
        sections = re.split(r"\n##+ ", content_clean)

        rule_counter = 1
        for section in sections:
            if not section.strip():
                continue

            # Extract section title (first line)
            section_lines = section.split("\n")
            section_title = section_lines[0].strip() if section_lines else "Unknown"

            # Look for **Rule:** markers
            rule_matches = re.finditer(
                r"\*\*Rule:\*\*\s*(.+?)(?=\n\n|\n\*\*Rule:|\Z)",
                section,
                re.DOTALL,
            )

            for match in rule_matches:
                rule_text = match.group(1).strip()

                # Extract code blocks
                code_examples = re.findall(r"```[\s\S]*?```", section)

                # Simple entity extraction (capitalized words, common tech names)
                entities = self._extract_entities_simple(section)

                # Simple context extraction
                contexts = self._extract_contexts_simple(section)

                # Determine rule type and priority (heuristics)
                rule_type = self._guess_rule_type(rule_text, section)
                priority = self._guess_priority(rule_text, section)

                rule_id = f"rule_{hashlib.sha256(rule_text.encode()).hexdigest()[:12]}"

                rules.append(
                    RuleSchema(
                        id=rule_id,
                        title=rule_text[:100] + ("..." if len(rule_text) > 100 else ""),
                        content=f"{section_title}\n\n{rule_text}",
                        rule_type=rule_type,
                        priority=priority,
                        entities=entities,
                        contexts=contexts,
                        source_section=section_title,
                        code_examples=code_examples,
                    )
                )

                rule_counter += 1

        # If no **Rule:** markers found, treat each ### section as a rule
        if not rules:
            sub_sections = re.split(r"\n### ", content_clean)
            for sub_section in sub_sections[1:]:  # Skip first (might be intro)
                if not sub_section.strip():
                    continue

                sub_lines = sub_section.split("\n")
                sub_title = sub_lines[0].strip() if sub_lines else "Unknown"
                sub_content = "\n".join(sub_lines[1:]).strip()

                if len(sub_content) < 50:  # Skip too short sections
                    continue

                entities = self._extract_entities_simple(sub_section)
                contexts = self._extract_contexts_simple(sub_section)
                code_examples = re.findall(r"```[\s\S]*?```", sub_section)

                rule_id = f"rule_{hashlib.sha256(sub_content.encode()).hexdigest()[:12]}"

                rules.append(
                    RuleSchema(
                        id=rule_id,
                        title=sub_title,
                        content=sub_content,
                        rule_type="guideline",
                        priority="medium",
                        entities=entities,
                        contexts=contexts,
                        source_section=sub_title,
                        code_examples=code_examples,
                    )
                )

        logger.info(f"📋 Fallback parser extracted {len(rules)} rules")
        return rules

    def _extract_entities_simple(self, text: str) -> List[str]:
        """Simple entity extraction using heuristics.

        Args:
            text: Text to analyze

        Returns:
            List of potential entity names
        """
        import re

        entities = set()

        # Common technology names
        tech_keywords = [
            "Docker",
            "FastAPI",
            "React",
            "TypeScript",
            "Python",
            "Node.js",
            "Nginx",
            "PostgreSQL",
            "Redis",
            "FalkorDB",
            "LangGraph",
            "Gemini",
            "PowerShell",
            "Windows",
            "Linux",
        ]

        text_lower = text.lower()
        for tech in tech_keywords:
            if tech.lower() in text_lower:
                entities.add(tech)

        # Capitalized words (potential entities)
        capitalized = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
        for cap in capitalized:
            if len(cap) > 3 and cap not in ["The", "This", "That", "When", "Where"]:
                entities.add(cap)

        return sorted(list(entities))[:10]  # Limit to 10

    def _extract_contexts_simple(self, text: str) -> List[str]:
        """Simple context extraction using keywords.

        Args:
            text: Text to analyze

        Returns:
            List of contexts
        """
        text_lower = text.lower()
        contexts = []

        context_keywords = {
            "frontend": ["frontend", "ui", "react", "component", "browser"],
            "backend": ["backend", "api", "server", "fastapi", "endpoint"],
            "server": ["server", "nginx", "deployment", "production"],
            "container": ["container", "docker", "dockerfile", "compose"],
            "database": ["database", "db", "postgres", "redis", "falkordb"],
            "cli": ["cli", "command", "terminal", "shell"],
        }

        for context, keywords in context_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                contexts.append(context)

        return contexts if contexts else ["general"]

    def _guess_rule_type(self, rule_text: str, section: str) -> str:
        """Guess rule type from content.

        Args:
            rule_text: Rule text
            section: Full section text

        Returns:
            Rule type
        """
        text_lower = (rule_text + " " + section).lower()

        if any(word in text_lower for word in ["avoid", "never", "don't", "bad"]):
            return "anti_pattern"
        elif any(word in text_lower for word in ["pattern", "design", "architecture"]):
            return "pattern"
        elif any(word in text_lower for word in ["always", "must", "should", "best"]):
            return "best_practice"
        else:
            return "guideline"

    def _guess_priority(self, rule_text: str, section: str) -> str:
        """Guess priority from content.

        Args:
            rule_text: Rule text
            section: Full section text

        Returns:
            Priority level
        """
        text_lower = (rule_text + " " + section).lower()

        if any(word in text_lower for word in ["always", "must", "critical", "security"]):
            return "high"
        elif any(word in text_lower for word in ["should", "recommended", "important"]):
            return "medium"
        else:
            return "low"


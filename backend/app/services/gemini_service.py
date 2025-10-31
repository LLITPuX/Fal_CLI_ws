"""Service for interacting with Gemini CLI."""

from __future__ import annotations

import asyncio
import json
import logging
import shlex
import time
import uuid
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import CLIExecutionError, JSONParsingError, ValidationException
from app.models.schemas import ProcessingMetrics, StructuredDoc

logger = logging.getLogger(__name__)


class GeminiService:
    """Handles Gemini CLI interactions and text structuring."""

    def __init__(
        self,
        cli_command: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ):
        """Initialize Gemini service.

        Args:
            cli_command: Override for CLI command (default from settings)
            model: Override for Gemini model (default from settings)
            timeout: Override for CLI timeout (default from settings)
        """
        self.cli_command = cli_command or settings.gemini_cli
        self.model = model or settings.gemini_model
        self.timeout = timeout or settings.gemini_timeout

    def build_prompt(self, text: str) -> str:
        """Build structured prompt for Gemini CLI.

        Args:
            text: Unstructured text to process

        Returns:
            Formatted prompt string
        """
        return (
            "You are a strict data structuring service. "
            "Return ONLY valid JSON matching this structure exactly:\n\n"
            "{\n"
            '  "title": "string",\n'
            '  "date_iso": "YYYY-MM-DD",\n'
            '  "summary": "string",\n'
            '  "tags": ["string", ...],\n'
            '  "sections": [{"name": "string", "content": "string"}, ...]\n'
            "}\n\n"
            "No markdown, no explanations, no trailing text. "
            "If date is missing, use today's date in ISO.\n\n"
            f"TEXT:\n{text}\n"
        )

    async def run_cli(self, prompt: str) -> tuple[str, float]:
        """Execute Gemini CLI command asynchronously with timing.

        Args:
            prompt: Formatted prompt string

        Returns:
            Tuple of (raw CLI stdout output, processing time in seconds)

        Raises:
            CLIExecutionError: If CLI execution fails
        """
        args = shlex.split(self.cli_command) + [
            "--model",
            self.model,
            "--output-format",
            "json",
            "--prompt",
            prompt,
        ]

        logger.info(f"Executing CLI with model: {self.model}")
        start_time = time.time()

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.timeout
            )

            processing_time = time.time() - start_time

            if proc.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore")
                logger.error(f"CLI failed with code {proc.returncode}: {error_msg}")
                raise CLIExecutionError(
                    f"CLI error ({proc.returncode}): {error_msg}"
                )

            output = stdout.decode("utf-8", errors="ignore")
            logger.info(
                f"CLI completed in {processing_time:.2f}s with model {self.model}"
            )
            logger.debug(f"CLI output: {output[:200]}...")
            return output, processing_time

        except asyncio.TimeoutError:
            logger.error(f"CLI timeout after {self.timeout}s")
            raise CLIExecutionError(f"CLI timeout after {self.timeout}s")
        except Exception as e:
            logger.error(f"CLI execution failed: {e}", exc_info=True)
            raise CLIExecutionError(f"CLI execution failed: {e}") from e

    def extract_json(self, raw_output: str) -> dict[str, Any]:
        """Extract JSON from CLI output.

        Handles various formats:
        - Direct JSON object
        - Wrapped in {"response": "..."}
        - Markdown code blocks

        Args:
            raw_output: Raw CLI output string

        Returns:
            Parsed JSON dictionary

        Raises:
            JSONParsingError: If JSON extraction fails
        """
        s = raw_output.strip()

        # Try parse as JSON first
        try:
            parsed = json.loads(s)
            # If wrapped in {"response": "..."}, unwrap it
            if isinstance(parsed, dict) and "response" in parsed:
                s = parsed["response"]
                # Re-parse unwrapped content
                if isinstance(s, str):
                    parsed = json.loads(self._extract_json_from_text(s))
                return parsed
            return parsed
        except json.JSONDecodeError:
            pass

        # Extract from markdown or raw text
        try:
            extracted = self._extract_json_from_text(s)
            return json.loads(extracted)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}. Output: {s[:500]}")
            raise JSONParsingError(
                f"Invalid JSON from CLI: {e}. Output: {s[:500]}"
            ) from e

    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON object from text with markdown.

        Args:
            text: Text containing JSON

        Returns:
            Extracted JSON string

        Raises:
            JSONParsingError: If no valid JSON found
        """
        # Remove markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()

        # Extract JSON object
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise JSONParsingError(
                f"No valid JSON object found in output: {text[:500]}"
            )

        return text[start : end + 1]

    def validate_schema(self, data: dict[str, Any]) -> StructuredDoc:
        """Validate data against StructuredDoc schema.

        Args:
            data: Dictionary to validate

        Returns:
            Validated StructuredDoc instance

        Raises:
            ValidationException: If validation fails
        """
        try:
            return StructuredDoc(**data)
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            raise ValidationException(f"Schema validation failed: {e}") from e

    def calculate_metrics(
        self, model: str, prompt: str, output: str, processing_time: float
    ) -> ProcessingMetrics:
        """Calculate processing metrics.

        Args:
            model: Gemini model name
            prompt: Input prompt text
            output: Output text from CLI
            processing_time: Time taken to process

        Returns:
            ProcessingMetrics instance
        """
        input_chars = len(prompt)
        output_chars = len(output)

        return ProcessingMetrics(
            model=model,
            processing_time_seconds=round(processing_time, 2),
            input_characters=input_chars,
            output_characters=output_chars,
            input_tokens_estimate=input_chars // 4,  # Rough estimate
            output_tokens_estimate=output_chars // 4,  # Rough estimate
        )

    async def save_result(
        self, doc: StructuredDoc, output_dir: str | None = None
    ) -> tuple[str, Path]:
        """Save structured document to JSON file.

        Args:
            doc: Validated structured document
            output_dir: Optional output directory

        Returns:
            Tuple of (file_id, json_path)
        """
        out_dir = Path(output_dir or settings.default_output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        file_id = uuid.uuid4().hex
        json_path = out_dir / f"{file_id}.json"

        # Atomic write with tmp file
        tmp_path = json_path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(doc.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(json_path)

        logger.info(f"Saved result to {json_path}")
        return file_id, json_path

    async def structure_text(
        self, text: str, output_dir: str | None = None
    ) -> tuple[str, str, StructuredDoc, ProcessingMetrics]:
        """Complete workflow: prompt -> CLI -> parse -> validate -> save.

        Args:
            text: Unstructured text to process
            output_dir: Optional output directory

        Returns:
            Tuple of (file_id, json_path, structured_doc, metrics)

        Raises:
            CLIExecutionError: If CLI fails
            JSONParsingError: If parsing fails
            ValidationException: If validation fails
        """
        # Build prompt
        prompt = self.build_prompt(text)

        # Execute CLI with timing
        raw_output, processing_time = await self.run_cli(prompt)

        # Parse JSON
        parsed_data = self.extract_json(raw_output)

        # Validate schema
        doc = self.validate_schema(parsed_data)

        # Save result
        file_id, json_path = await self.save_result(doc, output_dir)

        # Calculate metrics
        metrics = self.calculate_metrics(self.model, prompt, raw_output, processing_time)

        return file_id, str(json_path), doc, metrics


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

    def build_prompt(self, text: str, schema: str | None = None) -> str:
        """Build structured prompt for Gemini CLI with optional custom schema.

        Args:
            text: Unstructured text to process
            schema: Optional custom JSON schema definition

        Returns:
            Formatted prompt string
        """
        default_schema = """
{
  "title": "string - A concise, descriptive title extracted from the text",
  "date_iso": "YYYY-MM-DD - Publication or creation date in ISO 8601 format. Use today's date if not found",
  "summary": "string - A comprehensive 2-3 sentence summary capturing the main ideas",
  "tags": ["array of strings - Keywords or topics (3-7 tags). Be specific and relevant"],
  "sections": [
    {
      "name": "string - Section heading or topic name",
      "content": "string - Full content of this section, preserving important details"
    }
  ]
}
"""
        
        return (
            "You are a professional data structuring service specialized in extracting structured information from text.\n\n"
            "TASK: Analyze the provided text and extract information into the following JSON structure.\n\n"
            "OUTPUT SCHEMA (with field descriptions):\n"
            f"{schema or default_schema}\n\n"
            "REQUIREMENTS:\n"
            "- Return ONLY valid JSON, no markdown code blocks, no explanations\n"
            "- Preserve the original meaning and important details\n"
            "- Use null for missing optional fields\n"
            "- Ensure all text is properly escaped for JSON\n"
            "- Follow the schema structure exactly\n\n"
            f"INPUT TEXT:\n{text}\n"
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
                
                # Check for quota/rate limit errors
                if "429" in error_msg or "Resource exhausted" in error_msg:
                    raise CLIExecutionError(
                        f"Gemini API quota exceeded (429). Please wait and try again later."
                    )
                
                raise CLIExecutionError(
                    f"CLI error ({proc.returncode}): {error_msg}"
                )

            output = stdout.decode("utf-8", errors="ignore")
            stderr_text = stderr.decode("utf-8", errors="ignore") if stderr else ""
            
            logger.info(
                f"CLI completed in {processing_time:.2f}s with model {self.model}"
            )
            logger.info(f"CLI raw output length: {len(output)} chars")
            logger.info(f"CLI raw output (first 500 chars): {output[:500]}")
            
            if stderr_text.strip():
                logger.warning(f"CLI stderr: {stderr_text[:500]}")
                
                # Check for API errors in stderr even with returncode 0
                if "Error when talking to Gemini API" in stderr_text:
                    if "429" in stderr_text or "Resource exhausted" in stderr_text:
                        raise CLIExecutionError(
                            "Gemini API quota exceeded (429). Please wait and try again."
                        )
                    else:
                        logger.error(f"Gemini API error in stderr: {stderr_text[:1000]}")
            
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
                response_content = parsed["response"]
                
                # Check if response is empty or not a string
                if not response_content:
                    raise JSONParsingError(
                        f"Empty or invalid response from CLI. Full output: {s[:500]}"
                    )
                
                # Handle case where response is already a dict (not a string)
                if isinstance(response_content, dict):
                    return response_content
                
                # Re-parse unwrapped content (may have markdown)
                # First try to parse as JSON directly (in case it's already valid JSON)
                try:
                    return json.loads(response_content)
                except json.JSONDecodeError:
                    # If not valid JSON, extract from markdown
                    extracted = self._extract_json_from_text(response_content)
                    return json.loads(extracted)
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
        import re
        
        original_text = text
        
        # Remove markdown code blocks (try different patterns)
        # Pattern 1: ```json\n{...}\n``` (most common)
        json_block_pattern = r"```json\s*\n(.*?)\n```"
        match = re.search(json_block_pattern, text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        else:
            # Pattern 2: ```json{...}``` (no newlines)
            json_block_pattern2 = r"```json\s*(.*?)\s*```"
            match = re.search(json_block_pattern2, text, re.DOTALL)
            if match:
                text = match.group(1).strip()
            else:
                # Pattern 3: ```\njson\n{...}\n```
                json_block_pattern3 = r"```\s*json\s*\n(.*?)\n```"
                match = re.search(json_block_pattern3, text, re.DOTALL)
                if match:
                    text = match.group(1).strip()
                else:
                    # Pattern 4: ```\n{...}\n``` (generic code block)
                    code_block_pattern = r"```\s*\n(.*?)\n```"
                    match = re.search(code_block_pattern, text, re.DOTALL)
                    if match:
                        text = match.group(1).strip()
                        # Remove potential "json" at the beginning
                        if text.startswith("json\n") or text.startswith("json "):
                            text = text[5:].strip()

        # Extract JSON object (find outermost braces)
        # Use a simple counter to find matching braces
        start = text.find("{")
        if start == -1:
            # Try to find array start as well
            start = text.find("[")
            if start == -1:
                logger.error(f"Could not find JSON opening brace/bracket. Text preview: {original_text[:1000]}")
                raise JSONParsingError(
                    f"No valid JSON object/array found in output. Preview: {original_text[:1000]}"
                )
        
        # Find matching closing brace/bracket
        brace_count = 0
        bracket_count = 0
        end = start
        in_string = False
        escape_next = False
        
        for i in range(start, len(text)):
            char = text[i]
            
            # Handle string escaping
            if escape_next:
                escape_next = False
                continue
            
            if char == "\\":
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if in_string:
                continue
            
            # Count braces and brackets
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
            elif char == "[":
                bracket_count += 1
            elif char == "]":
                bracket_count -= 1
            
            # If we found the outermost closing
            if brace_count == 0 and bracket_count == 0:
                end = i
                break
        
        if brace_count != 0 or bracket_count != 0:
            logger.error(f"Unmatched JSON braces/brackets. Preview: {original_text[:1000]}")
            raise JSONParsingError(
                f"Invalid JSON structure. Preview: {original_text[:1000]}"
            )

        extracted = text[start : end + 1]
        logger.debug(f"Extracted JSON length: {len(extracted)} chars")
        return extracted

    def validate_schema(
        self, data: dict[str, Any], strict: bool = False
    ) -> dict[str, Any] | StructuredDoc:
        """Validate data against StructuredDoc schema or return as-is.

        Args:
            data: Dictionary to validate
            strict: If True, enforce StructuredDoc schema; otherwise return dict

        Returns:
            Validated StructuredDoc instance or raw dict for custom schemas

        Raises:
            ValidationException: If strict validation fails
        """
        if not strict:
            # Dynamic validation: just ensure it's valid JSON structure
            if not isinstance(data, dict):
                raise ValidationException("Parsed data must be a JSON object (dict)")
            return data
        
        # Strict validation against StructuredDoc
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
        self, doc: StructuredDoc | dict[str, Any], output_dir: str | None = None
    ) -> tuple[str, Path]:
        """Save structured document to JSON file.

        Args:
            doc: Validated structured document or dict
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
        
        # Handle both StructuredDoc and dict
        if isinstance(doc, dict):
            content = json.dumps(doc, ensure_ascii=False, indent=2)
        else:
            content = json.dumps(doc.model_dump(), ensure_ascii=False, indent=2)
        
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(json_path)

        logger.info(f"Saved result to {json_path}")
        return file_id, json_path

    async def structure_text(
        self,
        text: str,
        output_dir: str | None = None,
        custom_schema: str | None = None,
    ) -> tuple[str, str, StructuredDoc | dict[str, Any], ProcessingMetrics]:
        """Complete workflow: prompt -> CLI -> parse -> validate -> save.

        Args:
            text: Unstructured text to process
            output_dir: Optional output directory
            custom_schema: Optional custom JSON schema

        Returns:
            Tuple of (file_id, json_path, structured_doc, metrics)

        Raises:
            CLIExecutionError: If CLI fails
            JSONParsingError: If parsing fails
            ValidationException: If validation fails
        """
        # Build prompt with optional custom schema
        prompt = self.build_prompt(text, schema=custom_schema)

        # Execute CLI with timing
        raw_output, processing_time = await self.run_cli(prompt)

        # Parse JSON
        parsed_data = self.extract_json(raw_output)

        # Inject processing timestamp if field exists in schema
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Add timestamp to common time fields
        if isinstance(parsed_data, dict):
            if "time" in parsed_data:
                parsed_data["time"] = current_time
            if "processing_time" in parsed_data:
                parsed_data["processing_time"] = current_time
            if "timestamp" in parsed_data:
                parsed_data["timestamp"] = current_time

        # Validate schema (strict=False for custom schemas)
        doc = self.validate_schema(parsed_data, strict=(custom_schema is None))

        # Save result
        file_id, json_path = await self.save_result(doc, output_dir)

        # Calculate metrics
        metrics = self.calculate_metrics(self.model, prompt, raw_output, processing_time)

        return file_id, str(json_path), doc, metrics


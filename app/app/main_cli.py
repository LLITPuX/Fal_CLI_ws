from __future__ import annotations

import asyncio
import json
import os
import shlex
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError


app = FastAPI(title="Text Structurer (Gemini CLI)")


class StructuredDoc(BaseModel):
    title: str = Field(..., description="Human-readable title")
    date_iso: str = Field(..., description="ISO 8601 date, e.g. 2025-10-30")
    summary: str = Field(..., description="Short summary")
    tags: list[str] = Field(default_factory=list, description="Simple keyword tags")
    sections: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of sections with name and content",
    )


class StructureRequest(BaseModel):
    text: str
    out_dir: str | None = None
    cli_command: str | None = None
    model: str | None = None


class StructureResponse(BaseModel):
    id: str
    json_path: str
    data: StructuredDoc


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def build_prompt(text: str) -> str:
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


async def run_gemini_cli(command: str, model: str, prompt: str) -> str:
    args = shlex.split(command) + ["--model", model, "--output-format", "json", "--prompt", prompt]
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(
        proc.communicate(), timeout=90
    )
    if proc.returncode != 0:
        raise HTTPException(
            status_code=502,
            detail=f"CLI error ({proc.returncode}): {stderr.decode('utf-8', errors='ignore')}",
        )
    return stdout.decode("utf-8", errors="ignore")


def extract_json(s: str) -> str:
    # Try parse as JSON first (CLI might return wrapped response)
    try:
        parsed = json.loads(s)
        # If CLI returns {"response": "..."}, unwrap it
        if isinstance(parsed, dict) and "response" in parsed:
            s = parsed["response"]
    except json.JSONDecodeError:
        pass
    
    # Remove markdown code blocks if present
    if "```json" in s:
        start = s.find("```json") + 7
        end = s.find("```", start)
        if end != -1:
            s = s[start:end].strip()
    elif "```" in s:
        start = s.find("```") + 3
        end = s.find("```", start)
        if end != -1:
            s = s[start:end].strip()
    
    # Extract JSON object
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise HTTPException(status_code=502, detail=f"CLI did not return valid JSON. Output: {s[:500]}")
    return s[start : end + 1]


@app.post("/structure", response_model=StructureResponse)
async def structure_text(req: StructureRequest) -> StructureResponse:
    command = req.cli_command or os.getenv("GEMINI_CLI", "gemini")
    model = req.model or os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    prompt = build_prompt(req.text)

    raw = await run_gemini_cli(command, model, prompt)

    try:
        payload = json.loads(extract_json(raw))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"Invalid JSON from CLI: {e}. Raw output: {raw[:500]}")

    try:
        doc = StructuredDoc(**payload)
    except ValidationError as e:
        raise HTTPException(status_code=502, detail=f"Schema validation failed: {e}")

    out_dir = Path(req.out_dir or "data")
    out_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex
    json_path = out_dir / f"{file_id}.json"

    tmp_path = json_path.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(doc.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    tmp_path.replace(json_path)

    return StructureResponse(id=file_id, json_path=str(json_path), data=doc)





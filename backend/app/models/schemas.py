"""Data models for API validation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StructuredDoc(BaseModel):
    """Structured document schema returned by Gemini CLI."""

    title: str = Field(..., description="Human-readable title")
    date_iso: str = Field(..., description="ISO 8601 date, e.g. 2025-10-30")
    summary: str = Field(..., description="Short summary")
    tags: list[str] = Field(default_factory=list, description="Simple keyword tags")
    sections: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of sections with name and content",
    )


class StructureRequest(BaseModel):
    """Request for structuring text."""

    text: str = Field(..., min_length=1, description="Unstructured text to process")
    out_dir: str | None = Field(None, description="Optional output directory")
    cli_command: str | None = Field(None, description="Optional CLI command override")
    model: str | None = Field(None, description="Optional Gemini model override")


class StructureResponse(BaseModel):
    """Response after successful text structuring."""

    id: str = Field(..., description="Unique identifier for this result")
    json_path: str = Field(..., description="Path to saved JSON file")
    data: StructuredDoc = Field(..., description="Structured document data")


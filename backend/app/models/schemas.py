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


class ProcessingMetrics(BaseModel):
    """Metrics for processing performance."""

    model: str = Field(..., description="Gemini model used")
    processing_time_seconds: float = Field(..., description="Time taken to process")
    input_characters: int = Field(..., description="Number of input characters")
    output_characters: int = Field(..., description="Number of output characters")
    input_tokens_estimate: int = Field(
        ..., description="Estimated input tokens (chars / 4)"
    )
    output_tokens_estimate: int = Field(
        ..., description="Estimated output tokens (chars / 4)"
    )


class ModelResult(BaseModel):
    """Result from a single model."""

    id: str = Field(..., description="Unique identifier for this result")
    json_path: str = Field(..., description="Path to saved JSON file")
    data: StructuredDoc | None = Field(None, description="Structured document data")
    metrics: ProcessingMetrics | None = Field(None, description="Processing metrics")
    error: str | None = Field(None, description="Error message if processing failed")


class StructureRequest(BaseModel):
    """Request for structuring text."""

    text: str = Field(..., min_length=1, description="Unstructured text to process")
    out_dir: str | None = Field(None, description="Optional output directory")
    cli_command: str | None = Field(None, description="Optional CLI command override")
    model: str | None = Field(None, description="Optional Gemini model override")


class MultiModelResponse(BaseModel):
    """Response with results from processed models."""

    results: list[ModelResult] = Field(
        ..., description="Results from each model in order"
    )
    total_processing_time_seconds: float = Field(
        ..., description="Total time for all models"
    )


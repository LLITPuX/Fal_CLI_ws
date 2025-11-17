"""Pydantic schemas for rule parsing and storage."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RuleSchema(BaseModel):
    """Schema for a single rule extracted from documentation."""

    id: str = Field(..., description="Unique rule identifier")
    title: str = Field(..., description="Concise rule title")
    content: str = Field(..., description="Full rule text with context and examples")
    rule_type: Literal["best_practice", "pattern", "anti_pattern", "guideline"] = Field(
        ..., description="Type of rule"
    )
    priority: Literal["high", "medium", "low"] = Field(
        ..., description="Priority level"
    )
    entities: list[str] = Field(
        default_factory=list,
        description="List of technologies/concepts mentioned (e.g., Docker, FastAPI)",
    )
    contexts: list[str] = Field(
        default_factory=list,
        description="Contexts where rule applies (e.g., frontend, backend, server)",
    )
    source_section: str = Field(
        ..., description="Section heading from source document"
    )
    code_examples: list[str] = Field(
        default_factory=list, description="Code snippets if present"
    )


class ParsedRulesResponse(BaseModel):
    """Response from rule parser containing multiple rules."""

    rules: list[RuleSchema] = Field(..., description="List of extracted rules")


class RuleCacheEntry(BaseModel):
    """Cache entry for parsed rules."""

    file_path: str
    content_hash: str
    rules: list[RuleSchema]
    parsed_at: str  # ISO8601 timestamp


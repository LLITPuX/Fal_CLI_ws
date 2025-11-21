"""Pydantic schemas for document archiving system."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class FieldType(str, Enum):
    """Types of fields in node schema."""

    TEXT = "text"
    LONGTEXT = "longtext"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    DATE = "date"
    URL = "url"
    EMAIL = "email"
    ARRAY = "array"
    OBJECT = "object"


class FieldValidation(BaseModel):
    """Validation rules for schema fields."""

    min: int | float | None = None
    max: int | float | None = None
    pattern: str | None = None


class NodeSchemaField(BaseModel):
    """Field definition in node schema."""

    id: str = Field(..., description="Unique field identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Field name (property key)")
    type: FieldType = Field(..., description="Field type")
    label: str = Field(..., min_length=1, description="Display label for the field")
    required: bool = Field(default=False, description="Whether the field is required")
    default_value: Any | None = Field(
        default=None, description="Default value for the field"
    )
    enum_values: list[str] | None = Field(
        default=None, description="Possible values for enum type"
    )
    validation: FieldValidation | None = Field(
        default=None, description="Validation rules"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate field name format."""
        if not v.replace("_", "").isalnum():
            raise ValueError(
                "Field name must contain only alphanumeric characters and underscores"
            )
        return v


class NodeSchema(BaseModel):
    """Node schema definition with dynamic fields."""

    id: str = Field(..., description="Unique schema identifier")
    label: str = Field(
        ..., min_length=1, max_length=100, description="Node label (Document, Rule, Entity)"
    )
    description: str = Field(..., description="Schema description")
    fields: list[NodeSchemaField] = Field(
        ..., description="List of fields in the schema"
    )
    version: int = Field(default=1, description="Schema version")
    created_at: str = Field(..., description="Creation timestamp (ISO8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO8601)")

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        """Validate label format."""
        if not v.replace("_", "").isalnum():
            raise ValueError(
                "Label must contain only alphanumeric characters and underscores"
            )
        return v


class SchemaVersion(BaseModel):
    """Version of a node schema."""

    id: str = Field(..., description="Unique version identifier")
    schema_id: str = Field(..., description="Schema ID this version belongs to")
    version: int = Field(..., description="Version number")
    content: dict[str, Any] = Field(..., description="Full schema content as JSON")
    created_at: str = Field(..., description="Creation timestamp (ISO8601)")


class PromptTemplate(BaseModel):
    """Prompt template for document parsing."""

    id: str = Field(..., description="Unique prompt identifier")
    name: str = Field(..., min_length=1, description="Prompt name")
    content: str = Field(..., min_length=10, description="Prompt template content")
    placeholders: list[str] = Field(
        default_factory=list,
        description="List of available placeholders (e.g., {{content}}, {{schema}})",
    )
    version: int = Field(default=1, description="Prompt version")
    created_at: str = Field(..., description="Creation timestamp (ISO8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO8601)")


class PromptVersion(BaseModel):
    """Version of a prompt template."""

    id: str = Field(..., description="Unique version identifier")
    prompt_id: str = Field(..., description="Prompt ID this version belongs to")
    version: int = Field(..., description="Version number")
    content: str = Field(..., description="Full prompt content")
    created_at: str = Field(..., description="Creation timestamp (ISO8601)")


class DocumentTypeSchema(BaseModel):
    """Document type definition with associated schemas and prompts."""

    id: str = Field(..., description="Unique document type identifier")
    name: str = Field(..., min_length=1, description="Document type name (e.g., 'Markdown Rules')")
    file_extension: str = Field(
        ..., description="File extension (e.g., '.mdc', '.md', '.txt')"
    )
    description: str = Field(..., description="Type description")
    node_schemas: dict[str, str] = Field(
        ...,
        description="Mapping of node labels to schema IDs (e.g., {'Document': 'schema_1', 'Rule': 'schema_2'})",
    )
    prompt_id: str = Field(..., description="Prompt template ID for this document type")
    created_at: str = Field(..., description="Creation timestamp (ISO8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO8601)")


class ArchiveRequest(BaseModel):
    """Request to archive a document."""

    content: str = Field(..., min_length=1, description="Document content")
    file_path: str = Field(..., description="File path (relative or absolute)")
    document_type: str = Field(..., description="Document type ID")
    schema_id: str | None = Field(
        default=None,
        description="Specific schema ID (optional, uses default for document type)",
    )
    prompt_id: str | None = Field(
        default=None,
        description="Specific prompt ID (optional, uses default for document type)",
    )


class ArchiveStats(BaseModel):
    """Statistics from archiving operation."""

    document_id: str = Field(..., description="Created document node ID")
    rules_created: int = Field(default=0, description="Number of rule nodes created")
    entities_created: int = Field(default=0, description="Number of entity nodes created")
    relationships_created: int = Field(
        default=0, description="Number of relationships created"
    )


class ArchiveResponse(BaseModel):
    """Response from archive operation."""

    success: bool
    stats: ArchiveStats
    message: str = "Document archived successfully"


class PreviewRequest(BaseModel):
    """Request to preview document archiving without saving."""

    content: str = Field(..., min_length=1, description="Document content")
    document_type: str = Field(..., description="Document type ID")
    schema_id: str | None = Field(
        default=None,
        description="Specific schema ID (optional, uses default for document type)",
    )
    prompt_id: str | None = Field(
        default=None,
        description="Specific prompt ID (optional, uses default for document type)",
    )


class PreviewNode(BaseModel):
    """Preview of a node that would be created."""

    label: str = Field(..., description="Node label")
    properties: dict[str, Any] = Field(..., description="Node properties")


class PreviewRelationship(BaseModel):
    """Preview of a relationship that would be created."""

    from_label: str = Field(..., description="Source node label")
    to_label: str = Field(..., description="Target node label")
    relationship_type: str = Field(..., description="Relationship type")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Relationship properties"
    )


class PreviewResponse(BaseModel):
    """Response from preview operation."""

    success: bool
    nodes: list[PreviewNode] = Field(default_factory=list, description="Preview nodes")
    relationships: list[PreviewRelationship] = Field(
        default_factory=list, description="Preview relationships"
    )
    json_preview: dict[str, Any] = Field(
        ..., description="Complete JSON structure preview"
    )
    message: str = "Preview generated successfully"


class CreateDocumentTypeRequest(BaseModel):
    """Request to create a new document type."""

    name: str = Field(..., min_length=1, description="Document type name")
    file_extension: str = Field(..., description="File extension (e.g., '.mdc')")
    description: str = Field(..., description="Type description")
    node_schemas: dict[str, NodeSchema] = Field(
        ...,
        description="Node schemas for this type (e.g., {'Document': schema1, 'Rule': schema2})",
    )
    prompt_template: PromptTemplate = Field(
        ..., description="Prompt template for this type"
    )


class CreateSchemaVersionRequest(BaseModel):
    """Request to create a new schema version."""

    schema_id: str = Field(..., description="Schema ID to create version for")
    node_schema: NodeSchema = Field(..., description="New schema version", alias="schema")
    
    model_config = {"populate_by_name": True}


class RollbackSchemaRequest(BaseModel):
    """Request to rollback schema to a previous version."""

    schema_id: str = Field(..., description="Schema ID")
    version: int = Field(..., description="Version number to rollback to")


class CreatePromptVersionRequest(BaseModel):
    """Request to create a new prompt version."""

    prompt_id: str = Field(..., description="Prompt ID to create version for")
    prompt: PromptTemplate = Field(..., description="New prompt version")


class RollbackPromptRequest(BaseModel):
    """Request to rollback prompt to a previous version."""

    prompt_id: str = Field(..., description="Prompt ID")
    version: int = Field(..., description="Version number to rollback to")


class DocumentTypeResponse(BaseModel):
    """Response for document type operations."""

    success: bool
    document_type: DocumentTypeSchema | None = None
    message: str = "Operation completed successfully"


class DocumentTypeListResponse(BaseModel):
    """Response for listing document types."""

    success: bool
    document_types: list[DocumentTypeSchema] = Field(
        default_factory=list, description="List of document types"
    )
    count: int = 0
    message: str = "Document types retrieved successfully"


class SchemaVersionsResponse(BaseModel):
    """Response for schema versions list."""

    success: bool
    versions: list[SchemaVersion] = Field(
        default_factory=list, description="List of schema versions"
    )
    current_version: int = Field(..., description="Current version number")
    message: str = "Versions retrieved successfully"


class PromptVersionsResponse(BaseModel):
    """Response for prompt versions list."""

    success: bool
    versions: list[PromptVersion] = Field(
        default_factory=list, description="List of prompt versions"
    )
    current_version: int = Field(..., description="Current version number")
    message: str = "Versions retrieved successfully"


class SchemaResponse(BaseModel):
    """Response for schema operations."""

    success: bool
    node_schema: NodeSchema | None = Field(None, alias="schema")
    message: str = "Operation completed successfully"
    
    model_config = {"populate_by_name": True}


class PromptResponse(BaseModel):
    """Response for prompt operations."""

    success: bool
    prompt: PromptTemplate | None = None
    message: str = "Operation completed successfully"


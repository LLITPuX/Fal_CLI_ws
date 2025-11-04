"""Pydantic schemas for FalkorDB operations."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CreateNodeRequest(BaseModel):
    """Request to create a node in the graph."""

    label: str = Field(..., min_length=1, max_length=100, description="Node label")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Node properties"
    )
    template_id: str | None = Field(
        default=None, description="Template ID if creating from template"
    )

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        """Validate label format."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Label must contain only alphanumeric characters and underscores")
        return v


class NodeResponse(BaseModel):
    """Response for created node."""

    success: bool
    node_id: str | None = None
    label: str
    properties: dict[str, Any]
    message: str = "Node created successfully"


class CreateRelationshipRequest(BaseModel):
    """Request to create a relationship between nodes."""

    from_label: str = Field(..., description="Source node label")
    from_properties: dict[str, Any] = Field(..., description="Source node properties to match")
    to_label: str = Field(..., description="Target node label")
    to_properties: dict[str, Any] = Field(..., description="Target node properties to match")
    relationship_type: str = Field(..., description="Relationship type")
    relationship_properties: dict[str, Any] = Field(
        default_factory=dict, description="Relationship properties"
    )

    @field_validator("relationship_type")
    @classmethod
    def validate_relationship_type(cls, v: str) -> str:
        """Validate relationship type format."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Relationship type must contain only alphanumeric characters and underscores")
        return v.upper()


class RelationshipResponse(BaseModel):
    """Response for created relationship."""

    success: bool
    from_node: str
    to_node: str
    relationship_type: str
    message: str = "Relationship created successfully"


class QueryRequest(BaseModel):
    """Request to execute a Cypher query."""

    query: str = Field(..., min_length=1, max_length=5000, description="Cypher query")
    params: dict[str, Any] = Field(default_factory=dict, description="Query parameters")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Basic query validation."""
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        
        # Prevent dangerous operations
        dangerous_keywords = ["DELETE", "REMOVE", "DROP", "DETACH DELETE"]
        query_upper = v.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(f"Keyword '{keyword}' is not allowed for safety")
        
        return v


class QueryResponse(BaseModel):
    """Response for query execution."""

    success: bool
    results: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    message: str = "Query executed successfully"


class GraphStats(BaseModel):
    """Graph database statistics."""

    node_count: int = 0
    edge_count: int = 0
    labels: list[str] = Field(default_factory=list)
    relationship_types: list[str] = Field(default_factory=list)
    graph_name: str


# ============================================================================
# Node Template Schemas
# ============================================================================


class FieldType(str, Enum):
    """Types of fields that can be used in node templates."""
    
    TEXT = "text"
    LONGTEXT = "longtext"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ENUM = "enum"
    DATE = "date"
    URL = "url"
    EMAIL = "email"


class FieldValidation(BaseModel):
    """Validation rules for template fields."""
    
    min: int | float | None = None
    max: int | float | None = None
    pattern: str | None = None


class TemplateField(BaseModel):
    """Definition of a field in a node template."""
    
    model_config = {"populate_by_name": True}
    
    id: str = Field(..., description="Unique field ID")
    name: str = Field(..., min_length=1, max_length=100, description="Field name (property key)")
    type: FieldType = Field(..., description="Field type")
    label: str = Field(..., min_length=1, description="Display label for the field")
    required: bool = Field(default=False, description="Whether the field is required")
    placeholder: str | None = Field(default=None, description="Placeholder text")
    default_value: Any | None = Field(default=None, description="Default value for the field", alias="defaultValue")
    enum_values: list[str] | None = Field(default=None, description="Possible values for enum type", alias="enumValues")
    validation: FieldValidation | None = Field(default=None, description="Validation rules")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate field name format."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Field name must contain only alphanumeric characters and underscores")
        return v


class NodeTemplate(BaseModel):
    """Node template definition."""
    
    model_config = {"populate_by_name": True}
    
    id: str = Field(..., description="Unique template ID")
    label: str = Field(..., min_length=1, max_length=100, description="Node label")
    icon: str | None = Field(default=None, description="Icon for the template")
    description: str = Field(..., min_length=10, description="Template description")
    fields: list[TemplateField] = Field(..., description="Template fields")
    created_at: str = Field(..., description="Creation timestamp", alias="createdAt")
    updated_at: str = Field(..., description="Last update timestamp", alias="updatedAt")
    
    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        """Validate label format."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Label must contain only alphanumeric characters and underscores")
        return v


class CreateTemplateRequest(BaseModel):
    """Request to create a new node template."""
    
    label: str = Field(..., min_length=1, max_length=100, description="Node label")
    icon: str | None = Field(default=None, description="Icon for the template")
    description: str = Field(..., min_length=10, description="Template description")
    fields: list[TemplateField] = Field(..., description="Template fields")
    
    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        """Validate label format."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Label must contain only alphanumeric characters and underscores")
        return v


class UpdateTemplateRequest(BaseModel):
    """Request to update an existing node template."""
    
    icon: str | None = None
    description: str | None = Field(default=None, min_length=10)
    fields: list[TemplateField] | None = None


class TemplateResponse(BaseModel):
    """Response for template operations."""
    
    success: bool
    template: NodeTemplate | None = None
    message: str = "Template operation completed successfully"


class TemplateListResponse(BaseModel):
    """Response for listing templates."""
    
    success: bool
    templates: list[NodeTemplate] = Field(default_factory=list)
    count: int = 0
    message: str = "Templates retrieved successfully"


class TemplateMigrationRequest(BaseModel):
    """Request to migrate nodes after template update."""
    
    template_id: str = Field(..., description="Template ID to migrate")
    apply_defaults: bool = Field(
        default=True, 
        description="Whether to apply default values to new fields"
    )


class TemplateMigrationResponse(BaseModel):
    """Response for template migration."""
    
    success: bool
    nodes_updated: int = 0
    fields_added: list[str] = Field(default_factory=list)
    message: str = "Migration completed successfully"


class TemplateExportResponse(BaseModel):
    """Response for template export."""
    
    success: bool
    templates: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    message: str = "Templates exported successfully"


class TemplateImportRequest(BaseModel):
    """Request to import templates."""
    
    templates: list[dict[str, Any]] = Field(..., description="Templates to import")
    overwrite: bool = Field(
        default=False,
        description="Whether to overwrite existing templates with same label"
    )


class TemplateImportResponse(BaseModel):
    """Response for template import."""
    
    success: bool
    imported: int = 0
    skipped: int = 0
    errors: list[str] = Field(default_factory=list)
    message: str = "Import completed"


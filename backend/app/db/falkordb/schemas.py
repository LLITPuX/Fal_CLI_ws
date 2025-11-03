"""Pydantic schemas for FalkorDB operations."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class CreateNodeRequest(BaseModel):
    """Request to create a node in the graph."""

    label: str = Field(..., min_length=1, max_length=100, description="Node label")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Node properties"
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


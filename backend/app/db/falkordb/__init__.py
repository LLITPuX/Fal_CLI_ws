"""FalkorDB integration module.

This module provides async interface to FalkorDB graph database.
"""

from .client import FalkorDBClient, get_falkordb_client
from .schemas import (
    CreateNodeRequest,
    CreateRelationshipRequest,
    GraphStats,
    NodeResponse,
    QueryRequest,
    QueryResponse,
    RelationshipResponse,
)

__all__ = [
    "FalkorDBClient",
    "get_falkordb_client",
    "CreateNodeRequest",
    "CreateRelationshipRequest",
    "GraphStats",
    "NodeResponse",
    "QueryRequest",
    "QueryResponse",
    "RelationshipResponse",
]


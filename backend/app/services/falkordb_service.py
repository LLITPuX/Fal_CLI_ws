"""FalkorDB service - business logic layer."""

import logging
from typing import Any

from app.core.exceptions import ValidationError
from app.db.falkordb.client import FalkorDBClient
from app.db.falkordb.schemas import (
    CreateNodeRequest,
    CreateRelationshipRequest,
    GraphStats,
    NodeResponse,
    QueryRequest,
    QueryResponse,
    RelationshipResponse,
)

logger = logging.getLogger(__name__)


class FalkorDBService:
    """Service for FalkorDB operations."""

    def __init__(self, client: FalkorDBClient):
        """Initialize service with FalkorDB client.

        Args:
            client: FalkorDB client instance
        """
        self._client = client

    async def create_node(self, request: CreateNodeRequest) -> NodeResponse:
        """Create a new node in the graph.

        Args:
            request: Node creation request

        Returns:
            Node creation response

        Raises:
            ValidationError: If node creation fails
        """
        try:
            # Build properties string
            props_list = [
                f"{key}: ${key}" for key in request.properties.keys()
            ]
            props_str = "{" + ", ".join(props_list) + "}" if props_list else ""
            
            # Cypher query to create node
            cypher = f"CREATE (n:{request.label} {props_str}) RETURN id(n) as node_id"
            
            results, _ = await self._client.query(cypher, request.properties)
            
            node_id = str(results[0]["node_id"]) if results else None
            
            logger.info(
                f"Created node with label '{request.label}', id: {node_id}"
            )
            
            return NodeResponse(
                success=True,
                node_id=node_id,
                label=request.label,
                properties=request.properties,
            )
            
        except Exception as e:
            logger.error(f"Failed to create node: {e}", exc_info=True)
            raise ValidationError(f"Node creation failed: {str(e)}")

    async def create_relationship(
        self, request: CreateRelationshipRequest
    ) -> RelationshipResponse:
        """Create a relationship between two nodes.

        Args:
            request: Relationship creation request

        Returns:
            Relationship creation response

        Raises:
            ValidationError: If relationship creation fails
        """
        try:
            # Build MATCH clauses for source and target nodes
            from_props = self._build_match_properties(
                request.from_properties, "from"
            )
            to_props = self._build_match_properties(
                request.to_properties, "to"
            )
            
            # Build relationship properties
            rel_props_list = [
                f"{key}: ${key}"
                for key in request.relationship_properties.keys()
            ]
            rel_props_str = (
                "{" + ", ".join(rel_props_list) + "}"
                if rel_props_list
                else ""
            )
            
            # Cypher query
            cypher = f"""
            MATCH (from:{request.from_label} {from_props})
            MATCH (to:{request.to_label} {to_props})
            CREATE (from)-[r:{request.relationship_type} {rel_props_str}]->(to)
            RETURN id(from) as from_id, id(to) as to_id
            """
            
            # Combine all parameters
            params = {
                **{f"from_{k}": v for k, v in request.from_properties.items()},
                **{f"to_{k}": v for k, v in request.to_properties.items()},
                **request.relationship_properties,
            }
            
            results, _ = await self._client.query(cypher, params)
            
            if not results:
                raise ValidationError(
                    "Could not find matching nodes for relationship"
                )
            
            logger.info(
                f"Created relationship {request.relationship_type} "
                f"from {request.from_label} to {request.to_label}"
            )
            
            return RelationshipResponse(
                success=True,
                from_node=f"{request.from_label}({results[0]['from_id']})",
                to_node=f"{request.to_label}({results[0]['to_id']})",
                relationship_type=request.relationship_type,
            )
            
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}", exc_info=True)
            raise ValidationError(f"Relationship creation failed: {str(e)}")

    async def execute_query(self, request: QueryRequest) -> QueryResponse:
        """Execute a custom Cypher query.

        Args:
            request: Query execution request

        Returns:
            Query execution response

        Raises:
            ValidationError: If query execution fails
        """
        try:
            logger.info(f"Executing query: {request.query[:100]}...")
            
            results, execution_time = await self._client.query(
                request.query, request.params
            )
            
            logger.info(
                f"Query executed successfully: {len(results)} rows in "
                f"{execution_time:.2f}ms"
            )
            
            return QueryResponse(
                success=True,
                results=results,
                row_count=len(results),
                execution_time_ms=execution_time,
            )
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}", exc_info=True)
            raise ValidationError(f"Query execution failed: {str(e)}")

    async def get_graph_stats(self) -> GraphStats:
        """Get graph statistics.

        Returns:
            Graph statistics

        Raises:
            ValidationError: If stats retrieval fails
        """
        try:
            stats = await self._client.get_stats()
            
            return GraphStats(
                node_count=stats["node_count"],
                edge_count=stats["edge_count"],
                labels=stats["labels"],
                relationship_types=stats["relationship_types"],
                graph_name=stats["graph_name"],
            )
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}", exc_info=True)
            raise ValidationError(f"Stats retrieval failed: {str(e)}")

    def _build_match_properties(
        self, properties: dict[str, Any], prefix: str
    ) -> str:
        """Build property match string for MATCH clause.

        Args:
            properties: Properties to match
            prefix: Prefix for parameter names

        Returns:
            Property match string
        """
        if not properties:
            return ""
        
        props_list = [
            f"{key}: ${prefix}_{key}" for key in properties.keys()
        ]
        return "{" + ", ".join(props_list) + "}"


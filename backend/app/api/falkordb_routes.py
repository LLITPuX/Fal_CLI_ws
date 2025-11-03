"""FalkorDB API routes."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.falkordb.client import FalkorDBClient, get_falkordb_client
from app.db.falkordb.schemas import (
    CreateNodeRequest,
    CreateRelationshipRequest,
    GraphStats,
    NodeResponse,
    QueryRequest,
    QueryResponse,
    RelationshipResponse,
)
from app.services.falkordb_service import FalkorDBService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/falkordb", tags=["falkordb"])


def get_falkordb_service(
    client: Annotated[FalkorDBClient, Depends(get_falkordb_client)]
) -> FalkorDBService:
    """Get FalkorDB service instance.

    Args:
        client: FalkorDB client from dependency

    Returns:
        FalkorDB service instance
    """
    return FalkorDBService(client)


FalkorDBServiceDep = Annotated[FalkorDBService, Depends(get_falkordb_service)]


@router.post(
    "/nodes",
    response_model=NodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a node",
    description="Create a new node in the graph database with specified label and properties",
)
async def create_node(
    request: CreateNodeRequest,
    service: FalkorDBServiceDep,
) -> NodeResponse:
    """Create a new node in the graph.

    Args:
        request: Node creation request with label and properties
        service: FalkorDB service instance

    Returns:
        Created node information

    Raises:
        HTTPException: If node creation fails
    """
    try:
        return await service.create_node(request)
    except Exception as e:
        logger.error(f"Node creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/relationships",
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a relationship",
    description="Create a relationship between two existing nodes",
)
async def create_relationship(
    request: CreateRelationshipRequest,
    service: FalkorDBServiceDep,
) -> RelationshipResponse:
    """Create a relationship between two nodes.

    Args:
        request: Relationship creation request
        service: FalkorDB service instance

    Returns:
        Created relationship information

    Raises:
        HTTPException: If relationship creation fails
    """
    try:
        return await service.create_relationship(request)
    except Exception as e:
        logger.error(f"Relationship creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Execute Cypher query",
    description="Execute a custom Cypher query on the graph database",
)
async def execute_query(
    request: QueryRequest,
    service: FalkorDBServiceDep,
) -> QueryResponse:
    """Execute a Cypher query.

    Args:
        request: Query execution request with Cypher query and parameters
        service: FalkorDB service instance

    Returns:
        Query execution results and statistics

    Raises:
        HTTPException: If query execution fails
    """
    try:
        return await service.execute_query(request)
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/stats",
    response_model=GraphStats,
    summary="Get graph statistics",
    description="Retrieve statistics about the graph database",
)
async def get_stats(
    service: FalkorDBServiceDep,
) -> GraphStats:
    """Get graph statistics.

    Args:
        service: FalkorDB service instance

    Returns:
        Graph statistics including node count, edge count, labels, etc.

    Raises:
        HTTPException: If stats retrieval fails
    """
    try:
        return await service.get_graph_stats()
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check if FalkorDB connection is healthy",
)
async def health_check(
    client: Annotated[FalkorDBClient, Depends(get_falkordb_client)]
) -> dict[str, str]:
    """Check FalkorDB health.

    Args:
        client: FalkorDB client instance

    Returns:
        Health status

    Raises:
        HTTPException: If health check fails
    """
    is_healthy = await client.health_check()
    
    if not is_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="FalkorDB is not healthy",
        )
    
    return {"status": "healthy", "service": "FalkorDB"}


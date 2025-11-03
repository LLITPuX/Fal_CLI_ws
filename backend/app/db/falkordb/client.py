"""FalkorDB async client with connection pooling."""

import asyncio
import logging
import time
from typing import Any

from falkordb import FalkorDB

from app.core.config import settings
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class FalkorDBClient:
    """Async FalkorDB client with connection management."""

    def __init__(
        self,
        host: str,
        port: int,
        graph_name: str,
        max_query_time: int = 30,
    ):
        """Initialize FalkorDB client.

        Args:
            host: FalkorDB host
            port: FalkorDB port
            graph_name: Name of the graph database
            max_query_time: Maximum query execution time in seconds
        """
        self._host = host
        self._port = port
        self._graph_name = graph_name
        self._max_query_time = max_query_time
        self._client: FalkorDB | None = None
        self._graph = None
        self._connected = False

    async def connect(self) -> None:
        """Initialize connection to FalkorDB."""
        try:
            logger.info(f"Connecting to FalkorDB at {self._host}:{self._port}")
            
            # Run sync FalkorDB initialization in executor
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                None,
                lambda: FalkorDB(
                    host=self._host,
                    port=self._port,
                )
            )
            
            # Select graph
            self._graph = self._client.select_graph(self._graph_name)
            
            # Test connection
            await loop.run_in_executor(None, self._client.connection.ping)
            
            self._connected = True
            logger.info(f"Successfully connected to FalkorDB graph: {self._graph_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to FalkorDB: {e}", exc_info=True)
            raise DatabaseError(f"FalkorDB connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Close FalkorDB connection."""
        if self._client:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._client.close)
                self._connected = False
                logger.info("Disconnected from FalkorDB")
            except Exception as e:
                logger.error(f"Error disconnecting from FalkorDB: {e}")

    def _ensure_connected(self) -> None:
        """Ensure client is connected."""
        if not self._connected or not self._client:
            raise DatabaseError("FalkorDB client is not connected")

    async def query(
        self, 
        cypher: str, 
        params: dict[str, Any] | None = None
    ) -> tuple[list[dict[str, Any]], float]:
        """Execute Cypher query.

        Args:
            cypher: Cypher query string
            params: Query parameters

        Returns:
            Tuple of (results list, execution time in ms)

        Raises:
            DatabaseError: If query execution fails
        """
        self._ensure_connected()
        
        try:
            start_time = time.time()
            
            # Execute query in executor with timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self._graph.query(cypher, params or {})
                ),
                timeout=self._max_query_time
            )
            
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Parse results
            results = []
            if result.result_set:
                for record in result.result_set:
                    row_dict = {}
                    for idx, col_name in enumerate(result.header):
                        # FalkorDB returns header as [[index, name], ...] 
                        # Extract the column name (second element) if it's a list
                        if isinstance(col_name, list) and len(col_name) >= 2:
                            key = col_name[1]  # Name is at index 1
                        elif isinstance(col_name, list) and len(col_name) == 1:
                            key = str(col_name[0])
                        else:
                            key = str(col_name)
                        row_dict[key] = self._serialize_value(record[idx])
                    results.append(row_dict)
            
            logger.debug(
                f"Query executed in {execution_time:.2f}ms, "
                f"returned {len(results)} rows"
            )
            
            return results, execution_time
            
        except asyncio.TimeoutError:
            logger.error(f"Query timeout after {self._max_query_time}s: {cypher}")
            raise DatabaseError(f"Query execution timeout ({self._max_query_time}s)")
        except Exception as e:
            logger.error(f"Query execution failed: {e}", exc_info=True)
            raise DatabaseError(f"Query failed: {str(e)}")

    def _serialize_value(self, value: Any) -> Any:
        """Serialize FalkorDB value to JSON-compatible format.

        Args:
            value: Value from FalkorDB

        Returns:
            JSON-serializable value
        """
        # Handle lists/arrays
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        
        # Handle dictionaries
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        
        # Handle Node objects
        if hasattr(value, 'properties'):
            return {
                'id': getattr(value, 'id', None),
                'label': getattr(value, 'label', None),
                'properties': dict(value.properties) if value.properties else {}
            }
        
        # Handle Edge/Relationship objects
        if hasattr(value, 'relation'):
            return {
                'type': getattr(value, 'relation', None),
                'properties': dict(value.properties) if hasattr(value, 'properties') else {}
            }
        
        # Handle Path objects
        if hasattr(value, 'nodes') and hasattr(value, 'edges'):
            return {
                'nodes': [self._serialize_value(n) for n in value.nodes()],
                'edges': [self._serialize_value(e) for e in value.edges()]
            }
        
        # Primitive types
        return value

    async def get_stats(self) -> dict[str, Any]:
        """Get graph statistics.

        Returns:
            Dictionary with graph statistics

        Raises:
            DatabaseError: If stats retrieval fails
        """
        self._ensure_connected()
        
        try:
            # Get node count
            node_result, _ = await self.query("MATCH (n) RETURN count(n) as count")
            node_count = node_result[0]["count"] if node_result else 0
            
            # Get edge count
            edge_result, _ = await self.query("MATCH ()-[r]->() RETURN count(r) as count")
            edge_count = edge_result[0]["count"] if edge_result else 0
            
            # Get labels - simplified approach
            labels = []
            try:
                loop = asyncio.get_event_loop()
                label_list = await loop.run_in_executor(None, self._graph.labels)
                if label_list and len(label_list) > 0:
                    labels = list(label_list)
            except Exception:
                pass
            
            # Get relationship types - simplified approach
            relationship_types = []
            try:
                loop = asyncio.get_event_loop()
                rel_list = await loop.run_in_executor(None, self._graph.relationship_types)
                if rel_list and len(rel_list) > 0:
                    relationship_types = list(rel_list)
            except Exception:
                pass
            
            return {
                "node_count": node_count,
                "edge_count": edge_count,
                "labels": labels,
                "relationship_types": relationship_types,
                "graph_name": self._graph_name,
            }
            
        except Exception as e:
            logger.error(f"Failed to get graph stats: {e}", exc_info=True)
            raise DatabaseError(f"Stats retrieval failed: {str(e)}")

    async def health_check(self) -> bool:
        """Check if FalkorDB connection is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._connected or not self._client:
                return False
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._client.connection.ping)
            return True
        except Exception:
            return False


# Global client instance
_falkordb_client: FalkorDBClient | None = None


def get_falkordb_client() -> FalkorDBClient:
    """Get FalkorDB client instance.

    Returns:
        FalkorDB client instance

    Raises:
        DatabaseError: If client is not initialized
    """
    if _falkordb_client is None:
        raise DatabaseError("FalkorDB client not initialized")
    return _falkordb_client


async def init_falkordb_client() -> FalkorDBClient:
    """Initialize global FalkorDB client.

    Returns:
        Initialized FalkorDB client
    """
    global _falkordb_client
    
    _falkordb_client = FalkorDBClient(
        host=settings.falkordb_host,
        port=settings.falkordb_port,
        graph_name=settings.falkordb_graph_name,
        max_query_time=settings.falkordb_max_query_time,
    )
    
    await _falkordb_client.connect()
    return _falkordb_client


async def close_falkordb_client() -> None:
    """Close global FalkorDB client."""
    global _falkordb_client
    
    if _falkordb_client:
        await _falkordb_client.disconnect()
        _falkordb_client = None


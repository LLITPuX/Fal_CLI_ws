#!/usr/bin/env python
"""Initialize cursor_memory graph with schema and indexes."""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.falkordb.client import FalkorDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_cursor_memory_graph():
    """Initialize cursor_memory graph with schema."""
    
    logger.info("=== Initializing cursor_memory graph ===")
    
    # Connect to FalkorDB
    client = FalkorDBClient(
        host=settings.falkordb_host,
        port=settings.falkordb_port,
        graph_name=settings.cursor_graph_name,
        max_query_time=30,
    )
    
    await client.connect()
    
    try:
        # 1. Create indexes for performance
        indexes = {
            "DevelopmentSession": ["started_at", "status"],
            "UserQuery": ["session_id", "timestamp"],
            "AssistantResponse": ["query_id", "timestamp"],
        }
        
        logger.info("Creating indexes...")
        for node_label, fields in indexes.items():
            for field in fields:
                cypher = f"CREATE INDEX ON :{node_label}({field})"
                try:
                    await client.query(cypher, {})
                    logger.info(f"✓ Created index: {node_label}.{field}")
                except Exception as e:
                    logger.warning(f"Index may already exist: {node_label}.{field} - {e}")
        
        # 2. Create metadata node
        logger.info("Creating graph metadata...")
        metadata_query = """
        MERGE (meta:GraphMetadata {graph_name: 'cursor_memory'})
        ON CREATE SET
          meta.created_at = $created_at,
          meta.schema_version = '1.0.0',
          meta.description = 'Development session tracking for Cursor Agent',
          meta.owner_agent = 'cursor',
          meta.last_migration = NULL,
          meta.migrations_applied = '[]'
        ON MATCH SET
          meta.last_checked = $checked_at
        RETURN meta
        """
        
        await client.query(metadata_query, {
            "created_at": datetime.now().isoformat(),
            "checked_at": datetime.now().isoformat(),
        })
        logger.info("✓ Graph metadata created")
        
        # 3. Create backup directory
        backup_dir = Path("backups/cursor_memory/exports/sessions")
        backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Backup directory created: {backup_dir}")
        
        # 4. Verify graph is accessible
        test_query = "MATCH (n) RETURN count(n) as count"
        result, exec_time = await client.query(test_query, {})
        node_count = result[0]["count"] if result else 0
        
        logger.info(f"✓ Graph verification passed (nodes={node_count}, {exec_time:.2f}ms)")
        
        logger.info("\n=== cursor_memory graph initialized successfully ===")
        logger.info("Graph name: cursor_memory")
        logger.info("Schema version: 1.0.0")
        logger.info("Indexes created: DevelopmentSession, UserQuery, AssistantResponse")
        logger.info("Backup directory: backups/cursor_memory/exports/sessions")
        logger.info("\nNext steps:")
        logger.info("1. Start development session: POST /api/cursor/session/start")
        logger.info("2. Make requests in Cursor IDE")
        logger.info("3. View in FalkorDB Browser: http://localhost:3001")
        logger.info("4. End session: POST /api/cursor/session/end")
        
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(init_cursor_memory_graph())



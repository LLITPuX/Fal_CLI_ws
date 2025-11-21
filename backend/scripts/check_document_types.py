"""Check document types in database."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.falkordb.client import FalkorDBClient
from app.core.config import settings


async def check_document_types():
    """Check document types in database."""
    client = FalkorDBClient(
        host=settings.falkordb_host,
        port=settings.falkordb_port,
        graph_name=settings.falkordb_graph_name,
        max_query_time=60,
    )

    try:
        await client.connect()
        print(f"Connected to graph: {settings.falkordb_graph_name}")
        
        # Check document types
        cypher = """
        MATCH (dt:DocumentType)
        RETURN dt.id as id, dt.name as name, dt.file_extension as file_extension
        ORDER BY dt.name
        """
        results, _ = await client.query(cypher, {})
        
        print(f"\nFound {len(results)} document types:")
        for r in results:
            print(f"  - {r.get('name', 'N/A')} ({r.get('file_extension', 'N/A')}) - ID: {r.get('id', 'N/A')}")
        
        if len(results) == 0:
            print("\n⚠️  No document types found!")
            print(f"   Graph name: {settings.falkordb_graph_name}")
            print(f"   Host: {settings.falkordb_host}:{settings.falkordb_port}")
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        try:
            await client.disconnect()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(check_document_types())


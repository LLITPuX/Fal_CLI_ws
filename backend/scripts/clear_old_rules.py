"""
Clear old rules (Chunk nodes) from Knowledge Base.

This script removes old chunk-based rules to prepare for new rule-based structure.

Usage:
    python backend/scripts/clear_old_rules.py [--confirm]
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.falkordb.client import FalkorDBClient
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)


async def clear_old_rules(confirm: bool = False):
    """Clear old Chunk-based rules from Knowledge Base.
    
    Args:
        confirm: If True, actually delete. If False, only show what would be deleted.
    """
    kb_id = "cursor_rules_v3"
    
    print("[*] Old Rules Cleaner")
    print(f"    Target Graph: cursor_memory")
    print(f"    KB ID: {kb_id}\n")
    
    # Connect to FalkorDB
    print("[+] Connecting to FalkorDB...")
    client = FalkorDBClient(
        host=settings.falkordb_host,
        port=settings.falkordb_port,
        graph_name="cursor_memory",
        max_query_time=60
    )
    
    try:
        await client.connect()
        print(f"    [OK] Connected to FalkorDB\n")
    except Exception as e:
        print(f"    [ERROR] Failed to connect: {e}")
        return False
    
    try:
        # Count old chunks
        count_cypher = """
        MATCH (kb:KnowledgeBase {id: $kb_id})<-[:IN_BASE]-(d:Document)
        OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk)
        RETURN count(c) as chunk_count, count(d) as doc_count
        """
        
        results, _ = await client.query(count_cypher, {"kb_id": kb_id})
        chunk_count = results[0].get("chunk_count", 0) if results else 0
        doc_count = results[0].get("doc_count", 0) if results else 0
        
        print(f"[*] Found:")
        print(f"    Documents: {doc_count}")
        print(f"    Chunks: {chunk_count}")
        
        if chunk_count == 0 and doc_count == 0:
            print("\n[!] No old rules found. Knowledge Base is empty.")
            return True
        
        if not confirm:
            print("\n[!] DRY RUN - No changes made")
            print("    Use --confirm to actually delete")
            return True
        
        print("\n[+] Deleting old rules...")
        
        # Delete chunks and documents
        delete_cypher = """
        MATCH (kb:KnowledgeBase {id: $kb_id})<-[:IN_BASE]-(d:Document)
        OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk)
        DETACH DELETE c, d
        """
        
        await client.query(delete_cypher, {"kb_id": kb_id})
        
        print("    [OK] Deleted old Chunk nodes and Documents")
        print("\n[SUCCESS] Old rules cleared!")
        print("    You can now reload rules with new structure:")
        print("    python backend/scripts/load_rules_to_kb.py --force-reload")
        
        return True
        
    except Exception as e:
        print(f"    [ERROR] Failed to clear: {e}")
        return False
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clear old chunk-based rules from Knowledge Base"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually delete (default is dry-run)"
    )
    
    args = parser.parse_args()
    
    success = await clear_old_rules(confirm=args.confirm)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())


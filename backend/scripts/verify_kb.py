"""Verify Knowledge Base loading."""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.scripts.load_rules_standalone import FalkorDBClientSimple


async def verify():
    """Verify KB was loaded correctly."""
    print("[*] Verifying Knowledge Base...\n")
    
    client = FalkorDBClientSimple("localhost", 6379, "cursor_memory")
    await client.connect()
    
    # Check KnowledgeBase
    results, _ = await client.query("""
        MATCH (kb:KnowledgeBase {id: 'cursor_rules_v3'})
        RETURN kb.version as version, kb.initialized_at as initialized_at
    """)
    
    if results:
        print(f"[OK] KnowledgeBase found:")
        print(f"     Version: {results[0]['version']}")
        print(f"     Initialized: {results[0]['initialized_at']}\n")
    else:
        print("[!] KnowledgeBase not found!\n")
        return
    
    # Count documents
    results, _ = await client.query("""
        MATCH (kb:KnowledgeBase {id: 'cursor_rules_v3'})<-[:IN_BASE]-(d:Document)
        RETURN count(d) as count
    """)
    doc_count = results[0]['count'] if results else 0
    print(f"[OK] Documents: {doc_count}")
    
    # Count chunks
    results, _ = await client.query("""
        MATCH (kb:KnowledgeBase {id: 'cursor_rules_v3'})<-[:IN_BASE]-(d:Document)
        MATCH (d)<-[:PART_OF]-(c:Chunk)
        RETURN count(c) as count
    """)
    chunk_count = results[0]['count'] if results else 0
    print(f"[OK] Chunks: {chunk_count}")
    
    # Sample documents by category
    results, _ = await client.query("""
        MATCH (d:Document)
        RETURN d.category as category, count(*) as count
        ORDER BY count DESC
    """)
    
    print(f"\n[*] Documents by category:")
    for row in results:
        print(f"     {row['category']}: {row['count']}")
    
    # Sample chunk types
    results, _ = await client.query("""
        MATCH (c:Chunk)
        RETURN c.chunk_type as type, count(*) as count
        ORDER BY count DESC
    """)
    
    print(f"\n[*] Chunks by type:")
    for row in results:
        print(f"     {row['type']}: {row['count']}")
    
    # Sample content
    results, _ = await client.query("""
        MATCH (c:Chunk {chunk_type: 'heading'})
        RETURN c.content as content
        LIMIT 5
    """)
    
    print(f"\n[*] Sample headings:")
    for row in results:
        content = row['content'][:80]
        print(f"     {content}...")
    
    await client.disconnect()
    print(f"\n[SUCCESS] Verification complete!")


if __name__ == "__main__":
    asyncio.run(verify())


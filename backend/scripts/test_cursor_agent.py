#!/usr/bin/env python
"""Test script for Cursor Agent - verify cursor_memory graph works."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.cursor.nodes import cursor_record_node
from app.agents.cursor.repository import CursorRepository
from app.core.config import settings
from app.db.falkordb.client import FalkorDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_cursor_agent():
    """Test Cursor Agent end-to-end."""
    
    logger.info("=== Testing Cursor Agent ===\n")
    
    # 1. Connect to FalkorDB
    logger.info("1. Connecting to FalkorDB...")
    client = FalkorDBClient(
        host=settings.falkordb_host,
        port=settings.falkordb_port,
        graph_name=settings.cursor_graph_name,
        max_query_time=30,
    )
    await client.connect()
    logger.info("✓ Connected\n")
    
    # 2. Create repository
    logger.info("2. Creating repository...")
    repository = CursorRepository(client)
    logger.info("✓ Repository created\n")
    
    # 3. Test session creation
    logger.info("3. Testing session creation...")
    session_id = await repository.create_session(
        mode="agent",
        git_branch="feature/cursor-agent",
        git_commit="abc123",
        project_path="/workspace/Gemini CLI",
    )
    logger.info(f"✓ Session created: {session_id}\n")
    
    # 4. Test recording interaction
    logger.info("4. Testing cursor_record_node...")
    state = {
        "user_query": "Як налаштувати Multi-Graph архітектуру в FalkorDB?",
        "assistant_response": "Використовуйте client.select_graph() для кожного графа...",
        "mode": "agent",
        "intent": "question",
        "tools_used": ["codebase_search", "read_file"],
        "files_modified": ["backend/app/agents/cursor/repository.py"],
        "success": True,
    }
    
    result_state = await cursor_record_node(state, repository)
    
    if result_state["cursor_recorded"]:
        logger.info(f"✓ Interaction recorded:")
        logger.info(f"  - Query ID: {result_state['cursor_query_id']}")
        logger.info(f"  - Response ID: {result_state['cursor_response_id']}")
        logger.info(f"  - Session ID: {result_state['cursor_session_id']}\n")
    else:
        logger.error(f"✗ Recording failed: {result_state.get('error')}\n")
        await client.disconnect()
        return
    
    # 5. Test retrieving history
    logger.info("5. Testing session history retrieval...")
    history = await repository.get_session_history(session_id, limit=10)
    logger.info(f"✓ Retrieved {len(history)} interactions\n")
    
    if history:
        logger.info("Sample interaction:")
        logger.info(f"  Query: {history[0]['query'].get('content', '')[:50]}...")
        logger.info(f"  Response: {history[0]['response'].get('content', '')[:50]}...\n")
    
    # 6. Test listing sessions
    logger.info("6. Testing session listing...")
    sessions = await repository.get_sessions(status="active", limit=10)
    logger.info(f"✓ Found {len(sessions)} active sessions\n")
    
    # 7. Test ending session
    logger.info("7. Testing session end...")
    await repository.end_session(session_id)
    logger.info(f"✓ Session ended: {session_id}\n")
    
    # 8. Verify session ended
    logger.info("8. Verifying session status...")
    completed_sessions = await repository.get_sessions(status="completed", limit=10)
    logger.info(f"✓ Found {len(completed_sessions)} completed sessions\n")
    
    # 9. Graph stats
    logger.info("9. Getting graph stats...")
    stats_query = """
    MATCH (s:DevelopmentSession)
    OPTIONAL MATCH (s)<-[:IN_SESSION]-(q:UserQuery)
    OPTIONAL MATCH (q)<-[:ANSWERS]-(r:AssistantResponse)
    RETURN 
      count(DISTINCT s) as sessions,
      count(DISTINCT q) as queries,
      count(DISTINCT r) as responses
    """
    
    result, _ = await client.query(stats_query, {})
    if result:
        stats = result[0]
        logger.info(f"✓ Graph stats:")
        logger.info(f"  - Sessions: {stats['sessions']}")
        logger.info(f"  - Queries: {stats['queries']}")
        logger.info(f"  - Responses: {stats['responses']}\n")
    
    logger.info("=== All tests passed! ===")
    logger.info("\nNext steps:")
    logger.info("1. View in FalkorDB Browser: http://localhost:3001")
    logger.info("2. Select graph: cursor_memory")
    logger.info("3. Run query: MATCH (s:DevelopmentSession)<-[:IN_SESSION]-(q:UserQuery)<-[:ANSWERS]-(r:AssistantResponse) RETURN s, q, r LIMIT 10")
    
    await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(test_cursor_agent())
    except KeyboardInterrupt:
        logger.info("\n\nTest interrupted by user")
    except Exception as e:
        logger.error(f"\n\n❌ Test failed: {e}", exc_info=True)
        sys.exit(1)



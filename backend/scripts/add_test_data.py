"""Add test data to all FalkorDB graphs."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.falkordb.client import FalkorDBClient
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_test_data():
    """Add test data to all three graphs."""
    
    graphs = {
        "gemini_graph": {
            "nodes": [
                ("Person", {"name": "Alice", "age": 28, "city": "Kyiv"}),
                ("Person", {"name": "Bob", "age": 30, "city": "Lviv"}),
                ("Company", {"name": "TechCorp", "industry": "IT", "employees": 100}),
                ("Product", {"name": "AI Assistant", "version": "1.0", "price": 99.99}),
            ],
            "relationships": [
                ("Person", {"name": "Alice"}, "WORKS_AT", {"since": 2020}, "Company", {"name": "TechCorp"}),
                ("Person", {"name": "Bob"}, "WORKS_AT", {"since": 2019}, "Company", {"name": "TechCorp"}),
                ("Company", {"name": "TechCorp"}, "PRODUCES", {"year": 2024}, "Product", {"name": "AI Assistant"}),
            ]
        },
        "cybersich_chat": {
            "nodes": [
                ("UserQuery", {"text": "How to use Docker?", "timestamp": "2025-11-13T10:00:00"}),
                ("AIResponse", {"text": "Docker is a containerization platform...", "timestamp": "2025-11-13T10:00:05"}),
                ("UserQuery", {"text": "What is Kubernetes?", "timestamp": "2025-11-13T10:05:00"}),
                ("AIResponse", {"text": "Kubernetes is an orchestration system...", "timestamp": "2025-11-13T10:05:10"}),
            ],
            "relationships": [
                ("UserQuery", {"text": "How to use Docker?"}, "ANSWERED_BY", {}, "AIResponse", {"text": "Docker is a containerization platform..."}),
                ("UserQuery", {"text": "What is Kubernetes?"}, "ANSWERED_BY", {}, "AIResponse", {"text": "Kubernetes is an orchestration system..."}),
            ]
        },
        "cursor_memory": {
            "nodes": [
                ("CursorSession", {"session_id": "session-001", "date": "2025-11-12", "duration_minutes": 120}),
                ("ArchitecturalDecision", {"title": "Use Multi-Agent System", "rationale": "Better separation of concerns", "date": "2025-11-12"}),
                ("CursorSession", {"session_id": "session-002", "date": "2025-11-13", "duration_minutes": 180}),
                ("ArchitecturalDecision", {"title": "Custom Graph Viewer", "rationale": "Avoid FalkorDB Browser auth issues", "date": "2025-11-13"}),
            ],
            "relationships": [
                ("CursorSession", {"session_id": "session-001"}, "PRODUCED", {}, "ArchitecturalDecision", {"title": "Use Multi-Agent System"}),
                ("CursorSession", {"session_id": "session-002"}, "PRODUCED", {}, "ArchitecturalDecision", {"title": "Custom Graph Viewer"}),
            ]
        }
    }
    
    # Create and connect client
    client = FalkorDBClient(
        host=settings.falkordb_host,
        port=settings.falkordb_port,
        graph_name=settings.falkordb_graph_name,
        max_query_time=settings.falkordb_max_query_time,
    )
    await client.connect()
    
    try:
        for graph_name, data in graphs.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Adding test data to graph: {graph_name}")
            logger.info(f"{'='*60}")
            
            # Switch to graph
            client.select_graph(graph_name)
            
            # Add nodes
            logger.info(f"Adding {len(data['nodes'])} nodes...")
            for label, properties in data["nodes"]:
                props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
                query = f"CREATE (n:{label} {{{props_str}}})"
                await client.query(query, properties)
                logger.info(f"  ✓ Created {label}: {properties.get('name', properties.get('text', properties.get('title', properties.get('session_id', 'unnamed'))))[:50]}")
            
            # Add relationships
            logger.info(f"Adding {len(data['relationships'])} relationships...")
            for from_label, from_props, rel_type, rel_props, to_label, to_props in data["relationships"]:
                # Match nodes and create relationship
                from_match = " AND ".join([f"from.{k} = ${f'from_{k}'}" for k in from_props.keys()])
                to_match = " AND ".join([f"to.{k} = ${f'to_{k}'}" for k in to_props.keys()])
                
                params = {f"from_{k}": v for k, v in from_props.items()}
                params.update({f"to_{k}": v for k, v in to_props.items()})
                params.update({f"rel_{k}": v for k, v in rel_props.items()})
                
                rel_props_str = ""
                if rel_props:
                    rel_props_str = " {" + ", ".join([f"{k}: $rel_{k}" for k in rel_props.keys()]) + "}"
                
                query = f"""
                MATCH (from:{from_label}), (to:{to_label})
                WHERE {from_match} AND {to_match}
                CREATE (from)-[r:{rel_type}{rel_props_str}]->(to)
                """
                
                await client.query(query, params)
                logger.info(f"  ✓ Created {rel_type} relationship")
            
            # Verify stats
            stats = await client.get_stats(graph_name)
            logger.info(f"\nGraph '{graph_name}' stats:")
            logger.info(f"  Nodes: {stats['node_count']}")
            logger.info(f"  Edges: {stats['edge_count']}")
            logger.info(f"  Labels: {stats['labels']}")
            logger.info(f"  Relationship types: {stats['relationship_types']}")
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ Test data added successfully to all graphs!")
        logger.info(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Error adding test data: {e}", exc_info=True)
        raise
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(add_test_data())


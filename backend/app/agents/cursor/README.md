# Cursor Agent (Курсор)

Development memory agent для автоматичного збереження історії розробки в `cursor_memory` граф.

## Quick Start

### 1. Initialize Graph

```bash
docker compose exec backend python scripts/init_cursor_graph.py
```

### 2. Start Development Session

```bash
curl -X POST http://localhost:8000/api/cursor/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "agent",
    "git_branch": "feature/cursor-agent",
    "project_path": "/workspace"
  }'
```

Response:
```json
{
  "session_id": "abc-123",
  "status": "active"
}
```

### 3. Record Interactions (Manual for Phase 1)

```python
from app.agents.cursor.nodes import cursor_record_node
from app.agents.cursor.repository import CursorRepository

state = {
    "user_query": "How to implement Multi-Graph?",
    "assistant_response": "Use client.select_graph()...",
    "mode": "agent",
    "tools_used": ["codebase_search", "read_file"],
    "files_modified": ["backend/app/agents/cursor/repository.py"],
    "success": True,
}

result = await cursor_record_node(state, repository)
```

### 4. View in FalkorDB Browser

1. Open http://localhost:3001
2. Connect to `cursor_memory` graph
3. Run query:
```cypher
MATCH (s:DevelopmentSession)<-[:IN_SESSION]-(q:UserQuery)<-[:ANSWERS]-(r:AssistantResponse)
RETURN s, q, r
ORDER BY q.timestamp DESC
LIMIT 10
```

### 5. Get Session History

```bash
curl http://localhost:8000/api/cursor/session/{session_id}/history
```

### 6. End Session

```bash
curl -X POST http://localhost:8000/api/cursor/session/end \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc-123",
    "backup_to_git": true
  }'
```

Backup file: `backups/cursor_memory/exports/sessions/{session_id}.json`

## API Endpoints

- `POST /api/cursor/session/start` - Start new session
- `POST /api/cursor/session/end` - End session + backup
- `GET /api/cursor/sessions?status=active&limit=10` - List sessions
- `GET /api/cursor/session/{id}/history?limit=50` - Session history
- `GET /api/cursor/health` - Health check

## Graph Schema

### Nodes

- `:DevelopmentSession` - Development session container
- `:UserQuery` - User request/question
- `:AssistantResponse` - AI response

### Relationships

- `(:UserQuery)-[:IN_SESSION]->(:DevelopmentSession)` - Query belongs to session
- `(:AssistantResponse)-[:ANSWERS]->(:UserQuery)` - Response to query
- `(:UserQuery)-[:FOLLOWED_BY]->(:UserQuery)` - Sequential queries

## Testing

Run full test suite:

```bash
docker compose exec backend python scripts/test_cursor_agent.py
```

## Future Phases

**Phase 2:**
- ArchitecturalDecision extraction
- CodePattern recognition
- Component tracking

**Phase 3:**
- Semantic search (embeddings)
- Bug tracking
- Technology graph




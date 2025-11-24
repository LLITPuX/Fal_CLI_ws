# Cybersich Chat System - Multi-Agent Architecture

**Статус:** Phase 2 Complete ✅  
**Версія:** 2.3.0  
**Дата оновлення:** 12 листопада 2025

---

## Огляд

Cybersich Chat System — це мультиагентна система чату, побудована на LangGraph, яка забезпечує безкінечну пам'ять через графову базу даних FalkorDB. Система організована за принципом козацької Січі, де кожен агент має свою роль та відповідальність.

## Архітектура

### Multi-Agent Workflow (Phase 2)

```
User Message
    ↓
┌─────────────────┐
│  Clerk Agent    │ → Записує повідомлення в граф (cybersich_chat)
│  (Писарь)       │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Subconscious     │ → Аналізує контекст, знаходить схожі повідомлення
│ Agent            │   Виділяє сутності, створює embeddings
│ (Підсвідомість)  │
└────────┬────────┘
         ↓
    [END] (Phase 2)
    
    [Future: Phase 3]
         ↓
┌─────────────────┐
│ Orchestrator     │ → Приймає рішення про відповідь
│ Agent            │   Використовує контекст від Subconscious
│ (Оркестратор)    │
└─────────────────┘
```

### Графи в FalkorDB

| Граф | Призначення | Агенти | Статус |
|------|-------------|--------|--------|
| `cybersich_chat` | Історія чату | Clerk, Subconscious, Orchestrator | ✅ Active |
| `cursor_memory` | Розробка та сесії | Cursor Agent | ✅ Active |
| `gemini_graph` | Загальні дані | Multiple | ✅ Active |

---

## Phase 2: Clerk + Subconscious (✅ Complete)

### Clerk Agent (Писарь)

**Роль:** Записує всі повідомлення в граф без обробки.

**Функції:**
- ✅ Запис кожного повідомлення (user/assistant) в FalkorDB
- ✅ Створення та управління сесіями чату
- ✅ Збереження метаданих (timestamp, role, session_id)
- ✅ Temporal queries для історії

**Схема даних:**
```cypher
(:ChatSession {
  id, created_at, user_id, title, status, metadata
})

(:ChatMessage {
  id, content, role, timestamp, session_id, status, metadata
})

(:ChatSession)<-[:IN_SESSION]-(:ChatMessage)
```

**API Endpoints:**
- `POST /api/chat/send` - Відправити повідомлення
- `GET /api/chat/sessions` - Список сесій
- `GET /api/chat/session/{id}/messages` - Історія повідомлень
- `POST /api/chat/session` - Створити сесію

### Subconscious Agent (Підсвідомість)

**Роль:** Аналізує контекст та знаходить схожі повідомлення з минулого.

**Функції:**
- ✅ Семантичне розбиття повідомлень на chunks
- ✅ Створення embeddings через OpenAI API
- ✅ Пошук схожих chunks в історії
- ✅ Виділення сутностей (entities extraction)
- ✅ Формування контексту для Orchestrator

**Технології:**
- OpenAI `text-embedding-3-small` (1536 dimensions)
- Semantic text splitting (paragraphs, sentences)
- Cosine similarity search
- Temporal filtering (time windows)

**Схема даних:**
```cypher
(:Chunk {
  id, content, position, char_start, char_end,
  chunk_type, embedding, embedding_model, message_id
})

(:Entity {
  id, name, type, confidence, context
})

(:ChatMessage)-[:HAS_CHUNK]->(:Chunk)
(:Chunk)-[:CONTAINS_ENTITY]->(:Entity)
(:Chunk)-[:SIMILAR_TO]->(:Chunk)  // Similarity relationships
```

**Налаштування (config.py):**
```python
subconscious_chunk_size: int = 800
subconscious_chunk_overlap: float = 0.15  # 15%
subconscious_similarity_threshold: float = 0.7
subconscious_max_similar_chunks: int = 10
subconscious_recent_messages_limit: int = 10
subconscious_batch_size: int = 100
```

---

## Phase 3: Orchestrator (🔄 Planned)

**Роль:** Приймає рішення про відповідь на основі контексту від Subconscious.

**Планові функції:**
- Аналіз контексту від Subconscious
- Вибір стратегії відповіді
- Інтеграція з Gemini AI для генерації
- Управління діалогом

---

## Використання

### Frontend

1. Відкрийте http://localhost:3000
2. Перейдіть на сторінку "💬 Chat"
3. Введіть повідомлення та натисніть Enter
4. Повідомлення автоматично записується Clerk Agent
5. Subconscious Agent аналізує контекст у фоновому режимі

### API

**Відправити повідомлення:**
```bash
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Розкажи про козацьку історію",
    "session_id": "optional-session-id"
  }'
```

**Отримати історію:**
```bash
curl http://localhost:8000/api/chat/session/{session_id}/messages
```

**Створити сесію:**
```bash
curl -X POST http://localhost:8000/api/chat/session \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Нова розмова",
    "user_id": "user123"
  }'
```

---

## Структура коду

### Backend

```
backend/app/agents/
├── clerk/
│   ├── nodes.py          # clerk_record_node()
│   ├── repository.py     # MessageRepository
│   └── schemas.py        # ChatSession, ChatMessage
├── subconscious/
│   ├── nodes.py          # subconscious_analyze_node()
│   ├── repository.py    # SubconsciousRepository
│   ├── schemas.py       # Chunk, Entity, ContextAnalysis
│   ├── text_processor.py      # SemanticTextSplitter
│   ├── embeddings_service.py  # EmbeddingsService
│   ├── similarity_searcher.py # SimilaritySearcher
│   ├── entity_extractor.py    # EntityExtractor
│   └── context_formatter.py   # ContextFormatter
├── graph.py             # LangGraph workflow
└── state.py             # ChatState
```

### Frontend

```
frontend/src/
├── pages/
│   └── ChatPage.tsx     # Головна сторінка чату
├── components/chat/
│   ├── ChatHeader.tsx
│   ├── ChatInput.tsx
│   └── ChatMessage.tsx
└── services/
    └── chat-api.ts      # API client
```

---

## Налаштування

### Environment Variables

```env
# OpenAI для Subconscious Agent
OPENAI_API_KEY=your-openai-api-key

# FalkorDB
FALKORDB_HOST=falkordb
FALKORDB_PORT=6379
FALKORDB_GRAPH_NAME=cybersich_chat  # Для чату
```

### Config (backend/app/core/config.py)

```python
# Subconscious Agent Settings
subconscious_chunk_size: int = 800
subconscious_chunk_overlap: float = 0.15
subconscious_similarity_threshold: float = 0.7
subconscious_max_similar_chunks: int = 10
subconscious_recent_messages_limit: int = 10
subconscious_batch_size: int = 100
subconscious_timeout: int = 30

# OpenAI Settings
openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
openai_embedding_model: str = "text-embedding-3-small"
openai_embedding_dimensions: int = 1536
openai_entity_model: str = "gpt-4o-mini"
```

---

## Приклади Cypher запитів

### Отримати всі повідомлення сесії

```cypher
MATCH (s:ChatSession {id: $session_id})<-[:IN_SESSION]-(m:ChatMessage)
RETURN m
ORDER BY m.timestamp ASC
```

### Знайти схожі повідомлення

```cypher
MATCH (c:Chunk {id: $chunk_id})-[:SIMILAR_TO]->(similar:Chunk)
MATCH (similar)<-[:HAS_CHUNK]-(m:ChatMessage)
RETURN m, similar.similarity_score
ORDER BY similar.similarity_score DESC
LIMIT 10
```

### Отримати сутності з повідомлення

```cypher
MATCH (m:ChatMessage {id: $message_id})-[:HAS_CHUNK]->(c:Chunk)-[:CONTAINS_ENTITY]->(e:Entity)
RETURN e.name, e.type, e.confidence
ORDER BY e.confidence DESC
```

### Останні N повідомлень

```cypher
MATCH (m:ChatMessage)
WHERE m.timestamp >= datetime() - duration({days: 7})
RETURN m
ORDER BY m.timestamp DESC
LIMIT 50
```

---

## Troubleshooting

### Subconscious не працює

**Проблема:** Помилки з OpenAI API

**Рішення:**
1. Перевірте `OPENAI_API_KEY` в `.env`
2. Перевірте баланс OpenAI account
3. Перегляньте логи: `docker compose logs backend | grep subconscious`

### Повідомлення не записуються

**Проблема:** Clerk Agent не записує повідомлення

**Рішення:**
1. Перевірте підключення до FalkorDB: `docker compose ps falkordb`
2. Перевірте логи: `docker compose logs backend | grep clerk`
3. Перевірте граф: `cybersich_chat` має існувати

### Embeddings не створюються

**Проблема:** Chunks без embeddings

**Рішення:**
1. Перевірте OpenAI API key
2. Перевірте налаштування `subconscious_batch_size`
3. Перегляньте логи помилок OpenAI API

---

## Roadmap

### Phase 2 (✅ Complete)
- [x] Clerk Agent - запис повідомлень
- [x] Subconscious Agent - аналіз контексту
- [x] Embeddings та similarity search
- [x] Entity extraction
- [x] Context building

### Phase 3 (🔄 Planned)
- [ ] Orchestrator Agent - генерація відповідей
- [ ] Integration з Gemini AI
- [ ] Multi-turn dialogue management
- [ ] Context-aware responses

### Phase 4 (📋 Future)
- [ ] Voice input/output
- [ ] Multi-language support
- [ ] Advanced entity linking
- [ ] Knowledge graph expansion

---

## Додаткові ресурси

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FalkorDB Documentation](https://docs.falkordb.com/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)

---

**Slava Ukraini!** 🇺🇦


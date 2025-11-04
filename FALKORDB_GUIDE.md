# FalkorDB Integration Guide

## 📋 Огляд

FalkorDB - це графова база даних на основі Redis, що підтримує мову запитів Cypher. Інтеграція додає можливість створювати вузли (nodes), зв'язки (relationships) та виконувати складні графові запити.

## 🏗️ Архітектура

### Backend (FastAPI)

```
backend/app/
├── db/falkordb/
│   ├── __init__.py          # Public API
│   ├── client.py            # Async FalkorDB client з connection pooling
│   └── schemas.py           # Pydantic models для валідації
├── services/
│   └── falkordb_service.py  # Business logic layer
└── api/
    └── falkordb_routes.py   # REST API endpoints
```

### Frontend (React + TypeScript)

```
frontend/src/
├── pages/
│   └── FalkorDBPage.tsx           # Головна сторінка FalkorDB
├── components/falkordb/
│   ├── NodeForm.tsx               # Форма створення вузлів
│   ├── RelationshipForm.tsx       # Форма створення зв'язків
│   ├── QueryForm.tsx              # Форма виконання Cypher запитів
│   ├── ResultsViewer.tsx          # Відображення результатів
│   └── GraphStatsCard.tsx         # Статистика графа
├── services/
│   └── falkordb-api.ts            # API client
├── types/
│   └── falkordb.ts                # TypeScript типи
└── styles/
    └── FalkorDB.css               # Стилі
```

## 🚀 Запуск

### 1. Оновлення .env файлу

Додайте налаштування FalkorDB:

```env
# FalkorDB Configuration
FALKORDB_HOST=falkordb
FALKORDB_PORT=6379
FALKORDB_GRAPH_NAME=gemini_graph
FALKORDB_MAX_QUERY_TIME=30
```

### 2. Запуск через Docker Compose

```powershell
# Збілдити та запустити всі сервіси (включно з FalkorDB)
docker compose up --build

# Перевірити статус
docker compose ps
```

Сервіси будуть доступні:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **FalkorDB**: localhost:6379
- **API Docs**: http://localhost:8000/docs

### 3. Встановлення залежностей (якщо потрібно локально)

#### Backend
```powershell
cd backend
pip install -r requirements.txt
```

#### Frontend
```powershell
cd frontend
npm install
```

## 📡 API Endpoints

### 1. Створення вузла (Node)
```http
POST /api/falkordb/nodes
Content-Type: application/json

{
  "label": "Person",
  "properties": {
    "name": "John Doe",
    "age": 30,
    "email": "john@example.com"
  }
}
```

**Response:**
```json
{
  "success": true,
  "node_id": "0",
  "label": "Person",
  "properties": {
    "name": "John Doe",
    "age": 30,
    "email": "john@example.com"
  },
  "message": "Node created successfully"
}
```

### 2. Створення зв'язку (Relationship)
```http
POST /api/falkordb/relationships
Content-Type: application/json

{
  "from_label": "Person",
  "from_properties": {"name": "John Doe"},
  "to_label": "Company",
  "to_properties": {"name": "ACME Corp"},
  "relationship_type": "WORKS_AT",
  "relationship_properties": {"since": 2020}
}
```

### 3. Виконання Cypher запиту
```http
POST /api/falkordb/query
Content-Type: application/json

{
  "query": "MATCH (p:Person) RETURN p LIMIT 10",
  "params": {}
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "p": {
        "id": 0,
        "label": "Person",
        "properties": {
          "name": "John Doe",
          "age": 30
        }
      }
    }
  ],
  "row_count": 1,
  "execution_time_ms": 12.5,
  "message": "Query executed successfully"
}
```

### 4. Статистика графа
```http
GET /api/falkordb/stats
```

**Response:**
```json
{
  "node_count": 150,
  "edge_count": 200,
  "labels": ["Person", "Company", "Product"],
  "relationship_types": ["WORKS_AT", "OWNS", "KNOWS"],
  "graph_name": "gemini_graph"
}
```

### 5. Health Check
```http
GET /api/falkordb/health
```

## 🔍 Приклади Cypher запитів

### Базові запити

```cypher
-- Отримати всі вузли
MATCH (n) RETURN n LIMIT 10

-- Отримати всі вузли з певним label
MATCH (p:Person) RETURN p

-- Знайти вузол за властивістю
MATCH (p:Person {name: "John Doe"}) RETURN p

-- Отримати всі зв'язки
MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 10
```

### Складні запити

```cypher
-- Знайти людей, які працюють в компанії
MATCH (p:Person)-[:WORKS_AT]->(c:Company {name: "ACME Corp"})
RETURN p.name, p.age

-- Знайти друзів друзів
MATCH (me:Person {name: "John"})-[:KNOWS]->(friend)-[:KNOWS]->(fof)
WHERE fof <> me
RETURN DISTINCT fof.name

-- Порахувати кількість співробітників в кожній компанії
MATCH (p:Person)-[:WORKS_AT]->(c:Company)
RETURN c.name, count(p) as employee_count
ORDER BY employee_count DESC
```

## 🎨 Використання Frontend

### Навігація
1. Відкрийте http://localhost:3000
2. Натисніть на "🔗 FalkorDB" в навігації

### Створення вузла (Node)

1. Виберіть таб **"📍 Node"**
2. Введіть **Label**: `Person`
3. Додайте **Properties** використовуючи typed editor:
   - Натисніть **+ Add** для додавання властивості
   - Введіть **Key**: `name`
   - Оберіть **Type**: Text (з dropdown: Text/Number/Boolean)
   - Введіть **Value**: `Alice`
   - Повторіть для інших властивостей:
     - `age` (Number) = `28`
     - `city` (Text) = `Kyiv`
   - Кнопка **×** видаляє властивість
4. Натисніть **"Create Node"**

💡 **Smart Dropdowns**: Після створення першого вузла Label стане доступним в dropdown для швидкого вибору.

### Створення зв'язку (Relationship)

1. Виберіть таб **"🔗 Relationship"**
2. Заповніть **📍 From Node**:
   - **Label**: `Person` (dropdown або custom)
   - **Properties**: `name` (Text) = `Alice`
3. Заповніть **🔗 Relationship**:
   - **Type**: `KNOWS` (великими літерами)
   - **Properties** (опціонально): `since` (Number) = `2020`
4. Заповніть **📍 To Node**:
   - **Label**: `Person` (dropdown)
   - **Properties**: `name` (Text) = `Bob`
5. Натисніть **"Create Relationship"**

### Виконання запитів
1. Виберіть таб **"🔍 Query"**
2. Введіть Cypher запит або натисніть на один з прикладів знизу
3. Натисніть **"Execute Query"**
4. Результати відобразяться в центральній панелі з метриками виконання

### Статистика
- **Права панель** показує актуальну статистику графа:
  - Кількість Nodes та Relationships
  - Всі Labels (з можливістю використання в формах)
  - Всі Relationship Types
- Натисніть **🔄** для оновлення статистики

## ⚙️ Конфігурація

### Backend Config (app/core/config.py)

```python
# FalkorDB Settings
falkordb_host: str = "falkordb"          # FalkorDB host
falkordb_port: int = 6379                # FalkorDB port
falkordb_graph_name: str = "gemini_graph" # Ім'я графа
falkordb_max_query_time: int = 30        # Максимальний час запиту (сек)
```

### Docker Compose

FalkorDB запускається як окремий контейнер:

```yaml
falkordb:
  image: falkordb/falkordb:latest
  container_name: gemini-falkordb
  ports:
    - "6379:6379"
  volumes:
    - falkordb-data:/data
  networks:
    - gemini-network
```

## 🔒 Безпека

### Валідація
- ✅ Всі input дані валідуються через Pydantic schemas
- ✅ Заборонені небезпечні операції (DELETE, DROP, REMOVE)
- ✅ Параметризовані запити для запобігання injection
- ✅ Timeout для запитів (30 секунд за замовчуванням)

### Обмеження
- Максимальна довжина запиту: 5000 символів
- Максимальна довжина label: 100 символів
- Тільки alphanumeric символи та underscore в labels

## 🐛 Troubleshooting

### FalkorDB не підключається

```powershell
# Перевірити статус контейнера
docker compose ps falkordb

# Переглянути логи
docker compose logs falkordb

# Перезапустити FalkorDB
docker compose restart falkordb
```

### Backend не може підключитися до FalkorDB

```powershell
# Перевірити мережу Docker
docker network inspect gemini-network

# Перевірити змінні оточення backend
docker compose exec backend env | grep FALKORDB

# Перевірити логи backend
docker compose logs backend
```

### Помилка "FalkorDB client not initialized"

Переконайтеся, що:
1. FalkorDB контейнер запущений та healthy
2. Backend залежить від FalkorDB в docker-compose.yml
3. Змінні оточення правильно встановлені

## 📚 Додаткові ресурси

- [FalkorDB Documentation](https://docs.falkordb.com/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Router Documentation](https://reactrouter.com/)

## 🎯 Наступні кроки

1. **Візуалізація графа**: Додати D3.js або Cytoscape.js для візуалізації
2. **Експорт даних**: Додати можливість експорту графа
3. **Шаблони запитів**: Створити бібліотеку готових Cypher запитів
4. **Авторизація**: Додати ролі та права доступу
5. **Batch операції**: Можливість створювати багато вузлів одночасно

## 📝 Приклад Use Case

### Створення соціальної мережі

```cypher
-- 1. Створити людей
CREATE (alice:Person {name: "Alice", age: 28, city: "Kyiv"})
CREATE (bob:Person {name: "Bob", age: 30, city: "Lviv"})
CREATE (charlie:Person {name: "Charlie", age: 25, city: "Kyiv"})

-- 2. Створити зв'язки
CREATE (alice)-[:KNOWS {since: 2020}]->(bob)
CREATE (alice)-[:KNOWS {since: 2021}]->(charlie)
CREATE (bob)-[:KNOWS {since: 2019}]->(charlie)

-- 3. Запити
-- Хто знає Alice?
MATCH (p:Person)-[:KNOWS]->(alice:Person {name: "Alice"})
RETURN p.name

-- Хто з Києва?
MATCH (p:Person {city: "Kyiv"})
RETURN p.name, p.age

-- Найкоротший шлях між Alice та Charlie
MATCH path = shortestPath((alice:Person {name: "Alice"})-[:KNOWS*]-(charlie:Person {name: "Charlie"}))
RETURN path
```

---

**Автор**: Gemini CLI Team  
**Версія**: 2.2.0  
**Дата**: 3 листопада 2025


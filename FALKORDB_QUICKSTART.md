# 🚀 FalkorDB Quick Start

## Швидкий запуск за 3 кроки

### 1️⃣ Переконайтеся, що у вас є `.env` файл

```bash
# Якщо немає - створіть з env.example
copy env.example .env
```

Перевірте, що є FalkorDB налаштування:
```env
FALKORDB_HOST=falkordb
FALKORDB_PORT=6379
FALKORDB_GRAPH_NAME=gemini_graph
FALKORDB_MAX_QUERY_TIME=30
```

### 2️⃣ Запустіть Docker Compose

```powershell
# Зупинити попередні контейнери (якщо потрібно)
docker compose down

# Збілдити та запустити всі сервіси
docker compose up --build
```

Зачекайте поки всі сервіси стануть healthy (~30-60 секунд).

### 3️⃣ Відкрийте браузер

```
http://localhost:3000
```

Натисніть на **"🔗 FalkorDB"** в навігації зверху.

---

## 📝 Швидкий тест

### Створіть ваш перший вузол

1. На сторінці FalkorDB виберіть таб **"📍 Node"**
2. Введіть:
   - **Label**: `Person`
   - **Properties**:
   ```json
   {"name": "Alice", "age": 25, "city": "Kyiv"}
   ```
3. Натисніть **"Create Node"**

### Створіть другий вузол

1. Введіть:
   - **Label**: `Person`
   - **Properties**:
   ```json
   {"name": "Bob", "age": 30, "city": "Lviv"}
   ```
2. Натисніть **"Create Node"**

### Створіть зв'язок

1. Перейдіть на таб **"🔗 Relationship"**
2. Заповніть форму:
   - **From Label**: `Person`
   - **From Properties**: `{"name": "Alice"}`
   - **Relationship Type**: `KNOWS`
   - **To Label**: `Person`
   - **To Properties**: `{"name": "Bob"}`
   - **Relationship Properties**: `{"since": 2020}` (опціонально)
3. Натисніть **"Create Relationship"**

### Виконайте запит

1. Перейдіть на таб **"🔍 Query"**
2. Введіть Cypher запит:
   ```cypher
   MATCH (p:Person) RETURN p
   ```
3. Або виберіть один з прикладів нижче
4. Натисніть **"Execute Query"**
5. Перегляньте результати!

---

## 🎯 Приклади Cypher запитів

### Базові

```cypher
-- Всі вузли
MATCH (n) RETURN n LIMIT 10

-- Всі люди
MATCH (p:Person) RETURN p

-- Знайти конкретну людину
MATCH (p:Person {name: "Alice"}) RETURN p

-- Всі зв'язки
MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 10
```

### Складніші

```cypher
-- Знайти друзів Alice
MATCH (alice:Person {name: "Alice"})-[:KNOWS]->(friend)
RETURN friend.name, friend.city

-- Люди з Києва
MATCH (p:Person {city: "Kyiv"})
RETURN p.name, p.age

-- Кількість друзів кожної людини
MATCH (p:Person)-[:KNOWS]->(friend)
RETURN p.name, count(friend) as friends_count
ORDER BY friends_count DESC
```

---

## 📊 Статистика

Права панель показує:
- 📈 Кількість вузлів (Nodes)
- 🔗 Кількість зв'язків (Relationships)
- 🏷️ Всі Labels
- 🔀 Всі типи зв'язків

Натисніть 🔄 для оновлення.

---

## 🔧 Troubleshooting

### ❌ "Failed to connect to FalkorDB"

```powershell
# Перевірити статус
docker compose ps

# Перезапустити FalkorDB
docker compose restart falkordb

# Перевірити логи
docker compose logs falkordb
```

### ❌ Frontend не відкривається

```powershell
# Перевірити порт
docker compose ps frontend

# Перевірити логи
docker compose logs frontend
```

### ❌ Backend помилки

```powershell
# Перевірити логи backend
docker compose logs backend -f

# Перезапустити backend
docker compose restart backend
```

---

## 📚 Наступні кроки

- 📖 Детальна документація: [FALKORDB_GUIDE.md](./FALKORDB_GUIDE.md)
- 🌐 API Docs: http://localhost:8000/docs
- 📊 FalkorDB Docs: https://docs.falkordb.com/

---

**Готово! Користуйтеся FalkorDB графовою базою даних! 🎉**


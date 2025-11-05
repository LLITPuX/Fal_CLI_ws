# Chat System - Швидкий старт

Посібник для швидкого запуску та тестування Cybersich Chat System (Писарь Agent).

## 🚀 Запуск системи

### 1. Встановлення залежностей

```powershell
# В директорії backend/
cd backend
pip install -r requirements.txt
```

**Нові залежності:**
- `langgraph==0.2.28` — Multi-agent orchestration
- `langchain-core==0.3.10` — Core primitives

### 2. Запуск через Docker Compose

```powershell
# З кореневої директорії проєкту
docker-compose up --build
```

**Сервіси:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- FalkorDB: localhost:6379

### 3. Перевірка статусу

```powershell
# Health check
curl http://localhost:8000/health

# API documentation
# Відкрий в браузері: http://localhost:8000/docs
```

## 🧪 Тестування

### Автоматичний тест

```powershell
# З кореневої директорії
python test_chat_system.py
```

**Що робить тест:**
1. ✅ Створює chat session
2. ✅ Відправляє 3 повідомлення користувача
3. ✅ Симулює 3 відповіді асистента
4. ✅ Отримує історію повідомлень
5. ✅ Перевіряє інформацію про сесію

**Очікуваний вивід:**
```
🧪 Testing Cybersich Chat System (Писарь Agent)
============================================================

📝 Step 1: Creating chat session...
✅ Session created: abc123xyz
   Created at: 2025-11-05T12:00:00
   Title: Тестова розмова про козацтво

📨 Step 2: Sending messages...
   Message 1: Розкажи про історію козацтва...
   ✅ Message recorded: msg_abc123
      Status: recorded
      Recorded: True
   ✅ Assistant response recorded: msg_abc456

...

🎉 All tests passed successfully!
```

### Ручне тестування через curl

#### 1. Створити сесію
```powershell
curl -X POST http://localhost:8000/api/chat/session `
  -H "Content-Type: application/json" `
  -d '{\"user_id\": \"test_user\", \"title\": \"Моя розмова\"}'
```

**Отримаємо:**
```json
{
  "session_id": "abc123xyz",
  "created_at": "2025-11-05T12:00:00",
  "user_id": "test_user",
  "title": "Моя розмова",
  "status": "active"
}
```

#### 2. Відправити повідомлення
```powershell
curl -X POST http://localhost:8000/api/chat/message `
  -H "Content-Type: application/json" `
  -d '{\"content\": \"Привіт!\", \"session_id\": \"abc123xyz\", \"role\": \"user\"}'
```

**Отримаємо:**
```json
{
  "message_id": "msg_123",
  "session_id": "abc123xyz",
  "status": "recorded",
  "recorded": true,
  "error": null
}
```

#### 3. Отримати історію
```powershell
curl http://localhost:8000/api/chat/session/abc123xyz/history
```

**Отримаємо:**
```json
{
  "session_id": "abc123xyz",
  "messages": [
    {
      "id": "msg_123",
      "content": "Привіт!",
      "role": "user",
      "timestamp": "2025-11-05T12:00:00",
      "status": "recorded"
    }
  ],
  "total": 1
}
```

## 🔍 Перевірка в FalkorDB

### Через Redis CLI

```powershell
# Підключитись до FalkorDB
docker exec -it gemini-falkordb redis-cli

# В Redis CLI:
GRAPH.QUERY gemini_graph "MATCH (s:ChatSession) RETURN s"
GRAPH.QUERY gemini_graph "MATCH (m:Message) RETURN count(m)"
```

### Через FastAPI Cypher endpoint

```powershell
curl -X POST http://localhost:8000/api/falkordb/query `
  -H "Content-Type: application/json" `
  -d '{\"query\": \"MATCH (s:ChatSession) RETURN s.id, s.title\"}'
```

### Корисні Cypher запити

Див. повний список в [backend/test_chat_cypher.md](backend/test_chat_cypher.md)

**Приклади:**

```cypher
// Всі сесії
MATCH (s:ChatSession) RETURN s

// Всі повідомлення сесії
MATCH (m:Message)-[:IN_SESSION]->(s:ChatSession {id: 'SESSION_ID'})
RETURN m.id, m.role, m.content, m.timestamp
ORDER BY m.timestamp ASC

// Статистика
MATCH (m:Message) RETURN m.role, count(m) as count
```

## 📊 Моніторинг логів

### Backend logs
```powershell
# Real-time
docker-compose logs -f backend

# Шукаємо логи Писаря
docker-compose logs backend | Select-String "Писарь"
```

**Очікувані логи:**
```
backend_1  | 🤖 Multi-agent chat system (Писарь) initialized
backend_1  | 📝 Писарь: Починаю запис повідомлення...
backend_1  | 📝 Писарь успішно записав: msg_123 (role=user, content_length=45)
```

## 🐛 Troubleshooting

### Проблема: "Chat workflow not initialized"

**Причина:** FalkorDB не підключений або workflow не ініціалізувався

**Рішення:**
1. Перевірте статус FalkorDB: `docker-compose ps`
2. Перевірте логи: `docker-compose logs falkordb`
3. Перезапустіть: `docker-compose restart backend`

### Проблема: "Session not found"

**Причина:** Намагаєтесь відправити повідомлення без створення сесії

**Рішення:**
```powershell
# Спочатку створіть сесію
curl -X POST http://localhost:8000/api/chat/session `
  -H "Content-Type: application/json" `
  -d '{\"user_id\": \"user123\"}'
```

### Проблема: Import errors (langgraph)

**Причина:** Не встановлені нові залежності

**Рішення:**
```powershell
cd backend
pip install -r requirements.txt

# Або пересоберіть Docker
docker-compose build backend
```

### Проблема: FalkorDB connection refused

**Причина:** FalkorDB сервіс не запущений

**Рішення:**
```powershell
# Перевірити статус
docker-compose ps falkordb

# Перезапустити FalkorDB
docker-compose restart falkordb

# Якщо не допомагає - повний перезапуск
docker-compose down
docker-compose up
```

## 📝 Наступні кроки

### 1. Frontend інтеграція

Адаптувати `.figma/chat_ai/` під наш API:

```typescript
// src/services/chat-api.ts
export async function createSession(userId: string, title: string) {
  const response = await fetch('http://localhost:8000/api/chat/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, title })
  });
  return response.json();
}

export async function sendMessage(content: string, sessionId: string) {
  const response = await fetch('http://localhost:8000/api/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, session_id: sessionId, role: 'user' })
  });
  return response.json();
}
```

### 2. Phase 2: Підсвідомість Agent

Створити агента для аналізу контексту:

- Пошук схожих повідомлень через Cypher
- Виявлення тем та сутностей
- Формування контексту для Оркестратора

### 3. Phase 3: Оркестратор Agent

Додати агента для прийняття рішень:

- Вибір дії (respond, search, ask_clarification)
- Інтеграція з Gemini для генерації відповідей
- Використання контексту від Підсвідомості

## 📚 Документація

- [Повна документація Chat System](CHAT_SYSTEM.md)
- [Cypher запити для тестування](backend/test_chat_cypher.md)
- [Архітектурні принципи](.cursor/rules/architecture.mdc)
- [FalkorDB інтеграція](.cursor/rules/falkordb.mdc)

## ✅ Чеклист готовності

- [ ] Docker Compose запущений
- [ ] Backend доступний на :8000
- [ ] FalkorDB доступний на :6379
- [ ] `test_chat_system.py` виконується без помилок
- [ ] Логи показують "🤖 Multi-agent chat system (Писарь) initialized"
- [ ] Можна створювати сесії через API
- [ ] Можна відправляти повідомлення
- [ ] Історія повідомлень зберігається в FalkorDB
- [ ] Cypher запити повертають дані

## 🎉 Готово!

Система готова до використання! Писарь працює та записує всі повідомлення в FalkorDB. 

**Корисні команди:**

```powershell
# Перезапустити все
docker-compose restart

# Переглянути логи
docker-compose logs -f backend

# Очистити FalkorDB (для чистого тесту)
docker-compose down -v
docker-compose up
```


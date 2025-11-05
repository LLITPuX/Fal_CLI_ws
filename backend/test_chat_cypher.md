# Cypher Queries для тестування Chat System

Після запуску `test_chat_system.py`, використовуй ці Cypher запити для перевірки даних в FalkorDB.

## 📊 Базова статистика

### Кількість сесій
```cypher
MATCH (s:ChatSession)
RETURN count(s) as total_sessions
```

### Кількість повідомлень
```cypher
MATCH (m:Message)
RETURN count(m) as total_messages
```

### Статистика по ролях
```cypher
MATCH (m:Message)
RETURN m.role as role, count(m) as count
ORDER BY count DESC
```

## 🔍 Перегляд даних

### Всі сесії
```cypher
MATCH (s:ChatSession)
RETURN s.id, s.title, s.user_id, s.created_at, s.status
ORDER BY s.created_at DESC
```

### Всі повідомлення конкретної сесії
```cypher
// Замініть 'SESSION_ID' на актуальний ID з test_chat_system.py
MATCH (m:Message)-[:IN_SESSION]->(s:ChatSession {id: 'SESSION_ID'})
RETURN m.id, m.role, m.content, m.timestamp, m.status
ORDER BY m.timestamp ASC
```

### Останні N повідомлень
```cypher
MATCH (m:Message)-[:IN_SESSION]->(s:ChatSession)
RETURN m.id, m.role, m.content, m.timestamp, s.title as session
ORDER BY m.timestamp DESC
LIMIT 10
```

## 📈 Аналітичні запити

### Розмір контенту повідомлень
```cypher
MATCH (m:Message)
RETURN m.role, 
       avg(size(m.content)) as avg_length,
       min(size(m.content)) as min_length,
       max(size(m.content)) as max_length
```

### Активність по часу
```cypher
MATCH (m:Message)
WITH m, datetime(m.timestamp) as dt
RETURN 
  dt.hour as hour,
  count(m) as message_count
ORDER BY hour ASC
```

### Найдовші повідомлення
```cypher
MATCH (m:Message)-[:IN_SESSION]->(s:ChatSession)
RETURN 
  m.id,
  m.role,
  size(m.content) as length,
  substring(m.content, 0, 100) + '...' as preview,
  s.title as session
ORDER BY length DESC
LIMIT 5
```

## 🧹 Очищення (для тестування)

### Видалити всі повідомлення
```cypher
MATCH (m:Message)
DETACH DELETE m
```

### Видалити всі сесії та повідомлення
```cypher
MATCH (s:ChatSession)
OPTIONAL MATCH (m:Message)-[:IN_SESSION]->(s)
DETACH DELETE s, m
```

### Видалити конкретну сесію
```cypher
MATCH (s:ChatSession {id: 'SESSION_ID'})
OPTIONAL MATCH (m:Message)-[:IN_SESSION]->(s)
DETACH DELETE s, m
```

## 🔮 Підготовка до Phase 2 (Підсвідомість)

### Додати зв'язок послідовності між повідомленнями
```cypher
// Створити FOLLOWS зв'язки між послідовними повідомленнями в сесії
MATCH (s:ChatSession)
MATCH (m1:Message)-[:IN_SESSION]->(s)
MATCH (m2:Message)-[:IN_SESSION]->(s)
WHERE datetime(m2.timestamp) > datetime(m1.timestamp)
WITH s, m1, m2, datetime(m1.timestamp) as t1, datetime(m2.timestamp) as t2
ORDER BY s.id, t1, t2
WITH s, m1, collect(m2)[0] as next_message
WHERE next_message IS NOT NULL
CREATE (m1)-[:FOLLOWS]->(next_message)
RETURN count(*) as follows_created
```

### Перевірити граф послідовності
```cypher
MATCH path = (m1:Message)-[:FOLLOWS*]->(m2:Message)
WHERE m1.id = 'FIRST_MESSAGE_ID'
RETURN path
LIMIT 1
```

## 🎯 Корисні views

### Full conversation view
```cypher
MATCH (s:ChatSession {id: 'SESSION_ID'})
MATCH (m:Message)-[:IN_SESSION]->(s)
WITH s, m ORDER BY m.timestamp ASC
RETURN {
  session: {
    id: s.id,
    title: s.title,
    user_id: s.user_id
  },
  messages: collect({
    id: m.id,
    role: m.role,
    content: m.content,
    timestamp: m.timestamp
  })
} as conversation
```

### User activity summary
```cypher
MATCH (s:ChatSession)
MATCH (m:Message)-[:IN_SESSION]->(s)
WHERE m.role = 'user'
RETURN 
  s.user_id as user,
  count(DISTINCT s) as sessions_count,
  count(m) as messages_count,
  min(datetime(s.created_at)) as first_session,
  max(datetime(m.timestamp)) as last_activity
```

## 📝 Нотатки

- Всі timestamps в ISO 8601 форматі
- Session ID та Message ID — це UUID в hex форматі
- Role може бути: 'user', 'assistant', 'system'
- Status може бути: 'recorded', 'analyzed', 'responded'


# 🎨 Custom Graph Viewer Setup

## ✅ Що виконано

### 1. Дослідження FalkorDB Browser (✅ Завершено)
- Клоновано репозиторій: `D:\Development\Cursor_workspace\research\falkordb-browser`
- Вивчено структуру проекту
- З'ясовано проблему: edge версія використовує складну NextAuth систему
- Виявлено: REDIS_URL не підтримується належним чином
- Рішення: Створити власний простий візуалізатор

### 2. Створено SimpleGraphViewer компонент (✅ Завершено)
- **Файл**: `frontend/src/components/SimpleGraphViewer.tsx`
- **Бібліотека**: vis-network (потрібно встановити)
- **Функції**:
  - Автоматичне завантаження даних з FalkorDB
  - Інтерактивна візуалізація вузлів і зв'язків
  - Zoom In/Out, Fit to Screen
  - Refresh даних
  - Кольорова схема у козацькому стилі
  - Hover tooltips з властивостями вузлів/зв'язків

### 3. Інтеграція в GraphVisualizationPage (✅ Завершено)
- **Файл**: `frontend/src/pages/GraphVisualizationPage.tsx`
- Замінено інструкції на SimpleGraphViewer
- Підтримка Graph Selector (gemini_graph, cybersich_chat, cursor_memory)
- Зберігається козацький дизайн

---

## 🚀 Наступні кроки для запуску

### Крок 1: Встановлення vis-network

#### Варіант A: Через Docker (Рекомендовано)

```powershell
# 1. Зупинити контейнери
docker compose down

# 2. Додати vis-network в package.json
cd "D:\Development\Cursor_workspace\Gemini CLI\frontend"

# Відкрити package.json і додати в dependencies:
# "vis-network": "^9.1.9"

# АБО виконати через npm (якщо Node.js встановлений локально):
npm install vis-network@^9.1.9

# 3. Перебілдити і запустити
cd "D:\Development\Cursor_workspace\Gemini CLI"
docker compose build --no-cache frontend
docker compose up -d
```

#### Варіант B: Локальна розробка (якщо Node.js встановлений)

```powershell
cd "D:\Development\Cursor_workspace\Gemini CLI\frontend"
npm install vis-network@^9.1.9
npm run dev
```

### Крок 2: Перевірити роботу

```powershell
# Перевірити логи frontend
docker compose logs -f frontend

# Відкрити у браузері
# http://localhost:3000

# Перейти на: Graph Visualization → таб "Візуалізація Графа"
```

---

## 📦 Зміни в package.json

Додати в `frontend/package.json` → `dependencies`:

```json
{
  "dependencies": {
    // ... existing dependencies
    "vis-network": "^9.1.9"
  }
}
```

---

## 🎯 Як працює SimpleGraphViewer

### 1. Запит до Backend API

```typescript
POST /api/falkordb/query
{
  "query": "MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50",
  "graph_name": "gemini_graph"
}
```

### 2. Трансформація даних

FalkorDB результати → vis-network формат:

```typescript
{
  nodes: [
    {
      id: 0,
      label: "Alice",
      group: "Person",
      color: "#0057B7", // Blue
      title: "name: Alice\nage: 25"
    }
  ],
  edges: [
    {
      id: "0-KNOWS-1",
      from: 0,
      to: 1,
      label: "KNOWS",
      arrows: "to"
    }
  ]
}
```

### 3. Візуалізація

- **Вузли**: круглі точки з кольором за типом (label)
- **Зв'язки**: стрілки з підписами типу (relationship type)
- **Фізика**: Barnes-Hut алгоритм для автоматичного розташування
- **Інтерактивність**: hover, click, zoom, drag

---

## 🎨 Кольорова схема вузлів

```typescript
const NODE_COLORS: Record<string, string> = {
  Person: '#0057B7',              // Синій (🇺🇦)
  Company: '#FFD700',             // Золотий
  UserQuery: '#4CAF50',           // Зелений
  AIResponse: '#9C27B0',          // Фіолетовий
  CursorSession: '#FF9800',       // Помаранчевий
  ArchitecturalDecision: '#F44336', // Червоний
  default: '#757575',             // Сірий
};
```

Можна розширювати додаючи нові типи вузлів.

---

## 🔧 Налаштування візуалізації

У `SimpleGraphViewer.tsx` можна змінити:

### Фізика графа

```typescript
physics: {
  barnesHut: {
    gravitationalConstant: -2000,  // Сила відштовхування
    springConstant: 0.04,          // Жорсткість зв'язків
    springLength: 95,              // Довжина зв'язків
  },
}
```

### Розмір та вигляд вузлів

```typescript
nodes: {
  shape: 'dot',        // dot, box, circle, ellipse
  size: 20,            // Розмір
  borderWidth: 2,      // Товщина обводки
}
```

### Стрілки зв'язків

```typescript
edges: {
  width: 2,
  arrows: {
    to: {
      enabled: true,
      scaleFactor: 0.5,  // Розмір стрілки
    },
  },
}
```

---

## 🐛 Troubleshooting

### Помилка: "Cannot find module 'vis-network'"

```powershell
# Встановити залежність
cd "D:\Development\Cursor_workspace\Gemini CLI\frontend"
npm install vis-network@^9.1.9

# Перебілдити Docker контейнер
docker compose build --no-cache frontend
docker compose up -d frontend
```

### Помилка: "Failed to initialize graph visualization"

- Перевірити чи встановлена бібліотека
- Перевірити логи браузера (F12 → Console)
- Перевірити що backend API доступний

### Граф порожній

```powershell
# Перевірити чи є дані в FalkorDB
docker exec -it gemini-backend python -c "
from app.db.falkordb import get_falkordb_client
import asyncio
async def check():
    client = await get_falkordb_client()
    result = await client.query('MATCH (n) RETURN count(n) as count')
    print(result)
asyncio.run(check())
"
```

### Backend API не відповідає

```powershell
# Перевірити backend логи
docker compose logs -f backend

# Перевірити endpoint
curl -X POST http://localhost:8000/api/falkordb/query `
  -H "Content-Type: application/json" `
  -d '{\"query\":\"MATCH (n) RETURN n LIMIT 1\",\"graph_name\":\"gemini_graph\"}'
```

---

## 📊 Приклади використання

### Візуалізувати всі вузли типу Person

```typescript
<SimpleGraphViewer 
  graphName="cybersich_chat" 
  cypherQuery="MATCH (p:Person) OPTIONAL MATCH (p)-[r]->(m) RETURN p, r, m LIMIT 30"
  autoLoad={true}
/>
```

### Візуалізувати сесії Cursor Agent

```typescript
<SimpleGraphViewer 
  graphName="cursor_memory" 
  cypherQuery="MATCH (s:CursorSession)-[r]-(n) RETURN s, r, n"
  autoLoad={true}
/>
```

### Візуалізувати архітектурні рішення

```typescript
<SimpleGraphViewer 
  graphName="cursor_memory" 
  cypherQuery="MATCH (d:ArchitecturalDecision)-[r]-(n) RETURN d, r, n"
  autoLoad={true}
/>
```

---

## ✅ Переваги власного візуалізатора

1. **Простота**: Немає складної аутентифікації
2. **Інтеграція**: Прямий доступ до нашого backend API
3. **Кастомізація**: Повний контроль над дизайном
4. **Козацький стиль**: Відповідає загальному дизайну
5. **Швидкість**: Менше залежностей, швидше завантаження
6. **Надійність**: Не залежить від edge версії FalkorDB Browser

---

## 🎯 Наступні покращення (опціонально)

### Phase 1 Extensions:
- [ ] Додати search по вузлах
- [ ] Додати filter по типах вузлів
- [ ] Експорт графа як PNG/SVG
- [ ] History запитів

### Phase 2 Enhancements:
- [ ] Edit вузлів прямо в графі
- [ ] Створення нових зв'язків drag&drop
- [ ] Layout алгоритми (hierarchical, circular)
- [ ] Кластеризація великих графів

### Phase 3 Advanced:
- [ ] Real-time updates через WebSocket
- [ ] 3D візуалізація (force-graph-3d)
- [ ] Semantic search integration
- [ ] Timeline view по сесіях

---

## 📝 Файли створені/змінені

### Створено:
1. `frontend/src/components/SimpleGraphViewer.tsx` (402 рядки)
2. `GRAPH_VIEWER_SETUP.md` (цей файл)

### Змінено:
1. `frontend/src/pages/GraphVisualizationPage.tsx`
   - Додано імпорт SimpleGraphViewer
   - Замінено browser tab content
   - Видалено невикористану змінну browserUrl

### Референс (для дослідження):
1. `D:\Development\Cursor_workspace\research\falkordb-browser\` (клонований репо)

---

## 🔄 Git Workflow

```powershell
# Після встановлення vis-network і перевірки:

git add frontend/src/components/SimpleGraphViewer.tsx
git add frontend/src/pages/GraphVisualizationPage.tsx
git add frontend/package.json
git add GRAPH_VIEWER_SETUP.md

git commit -m "feat: Custom Graph Viewer with vis-network

- Replace FalkorDB Browser with SimpleGraphViewer component
- Direct integration with backend /api/falkordb/query
- Interactive visualization with zoom, pan, refresh
- Cossack color scheme
- Support for all graphs (gemini_graph, cybersich_chat, cursor_memory)
- No authentication issues
"

git push origin main
```

---

**Slava Ukraini!** 🇺🇦 🎨

**Час створення**: ~40 хвилин  
**Результат**: Власний функціональний візуалізатор без проблем з аутентифікацією


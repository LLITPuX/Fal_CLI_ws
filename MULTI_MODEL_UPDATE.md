# 🚀 Multi-Model Comparison Update

## Огляд змін

Проект оновлено для послідовного тестування всіх трьох моделей Gemini з детальними метриками продуктивності.

## ✨ Нові можливості

### 1. **Багатомодельне тестування**
- ✅ Послідовна обробка тексту трьома моделями:
  - `gemini-2.5-pro` (найточніша)
  - `gemini-2.5-flash` (збалансована)
  - `gemini-2.5-flash-light` (найшвидша)

### 2. **Детальні метрики**
- ⏱️ **Час обробки** кожної моделі (секунди)
- 📥 **Вхідні дані**: кількість символів та токенів
- 📤 **Вихідні дані**: кількість символів та токенів
- 📊 **Загальний час** обробки всіх моделей

### 3. **Розширені таймаути**
- ⏰ Таймаут на модель: **5 хвилин** (300 секунд)
- ⏰ Максимальний час: **15 хвилин** (для всіх трьох моделей)

### 4. **Покращений UI**
- 🎨 Окремі карточки для результатів кожної моделі
- 📊 Візуальна сітка метрик
- ❌ Відображення помилок для моделей, що не спрацювали
- ✅ Статистика успішних/невдалих спроб

## 📝 Зміни в коді

### Backend

#### `backend/app/models/schemas.py`
```python
# Нові моделі:
- ProcessingMetrics  # Метрики обробки
- ModelResult        # Результат однієї моделі
- MultiModelResponse # Відповідь з усіх моделей
```

#### `backend/app/core/config.py`
```python
gemini_timeout: int = 300  # 5 хвилин на модель
gemini_models: list[str] = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-light",
]
```

#### `backend/app/services/gemini_service.py`
- ✅ Додано вимірювання часу в `run_cli()`
- ✅ Новий метод `calculate_metrics()`
- ✅ Розширено `structure_text()` для повернення метрик

#### `backend/app/api/routes.py`
- ✅ Ендпоїнт `/structure` обробляє всі 3 моделі послідовно
- ✅ Обробка помилок без зупинки на інших моделях
- ✅ Повернення `MultiModelResponse`

### Frontend

#### `frontend/src/types/api.ts`
```typescript
// Нові типи:
- ProcessingMetrics
- ModelResult
- MultiModelResponse
```

#### `frontend/src/components/JsonViewer.tsx`
- ✅ Повністю переписано для багатомодельного відображення
- ✅ Компонент `ModelResultCard` для кожної моделі
- ✅ Відображення метрик у сітці
- ✅ Обробка помилок окремих моделей

#### `frontend/src/App.tsx`
- ✅ Оновлено заголовки та описи
- ✅ Новий loading state з інформацією про моделі
- ✅ Оновлений idle state з переліком моделей

#### `frontend/src/styles/App.css`
- ✅ Стилі для метрик (`.metrics-grid`, `.metric`)
- ✅ Стилі для порівняння моделей (`.models-comparison`)
- ✅ Стилі для карточок результатів (`.model-result`)
- ✅ Responsive дизайн

## 🔧 Запуск оновленого проекту

### 1. Перевірте .env файл
```ini
HOST_GEMINI_DIR=C:\Users\YourUser\.gemini
GEMINI_CLI=gemini
GEMINI_MODEL=gemini-2.5-flash  # Використовується як запасний
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
API_PORT=8000
FRONTEND_PORT=3000
```

### 2. Пересоберіть контейнери
```powershell
# Зупиніть існуючі контейнери
docker compose down

# Пересоберіть образи
docker compose build --no-cache

# Запустіть сервіси
docker compose up -d

# Перевірте логи
docker compose logs -f
```

### 3. Перевірте роботу
```powershell
# Health check
curl http://localhost:3000/api/health

# Відкрийте у браузері
start http://localhost:3000
```

## 📊 Приклад використання

### Через Web UI
1. Відкрийте http://localhost:3000
2. Вставте текст у textarea
3. Натисніть **"Structure Text"**
4. Зачекайте до 15 хвилин (залежно від обсягу тексту)
5. Переглядайте результати всіх трьох моделей з метриками

### Через API
```powershell
$body = @{
    text = "Ваш текст для аналізу..."
} | ConvertTo-Json -Compress

$response = Invoke-RestMethod -Uri http://localhost:3000/api/structure `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $body

# Результат містить:
$response.results                          # Масив результатів (3 моделі)
$response.total_processing_time_seconds    # Загальний час
```

## 🎯 Структура відповіді

```json
{
  "results": [
    {
      "id": "abc123...",
      "json_path": "data/abc123.json",
      "data": {
        "title": "...",
        "date_iso": "2025-10-31",
        "summary": "...",
        "tags": [...],
        "sections": [...]
      },
      "metrics": {
        "model": "gemini-2.5-pro",
        "processing_time_seconds": 45.23,
        "input_characters": 1234,
        "output_characters": 567,
        "input_tokens_estimate": 308,
        "output_tokens_estimate": 141
      },
      "error": null
    },
    // ... результати інших моделей
  ],
  "total_processing_time_seconds": 123.45
}
```

## ⚠️ Важливі зауваження

### Таймаути
- Кожна модель має **5 хвилин** на обробку
- Загальний час може сягати **15 хвилин**
- Якщо одна модель падає, інші продовжують роботу

### Обробка помилок
- Якщо модель не спрацювала, `error` містить опис помилки
- `data` та `metrics` будуть `null` для невдалих моделей
- Система продовжує обробку наступними моделями

### Ресурси
- Всі три моделі працюють **послідовно** (не паралельно)
- Кожна модель створює окремий JSON файл
- Результати зберігаються в Docker volume `backend-data`

## 🐛 Troubleshooting

### Таймаут на всіх моделях
```powershell
# Збільште таймаут у backend/app/core/config.py
gemini_timeout: int = 600  # 10 хвилин

# Пересоберіть backend
docker compose build backend
docker compose up -d backend
```

### Одна модель постійно падає
- Перевірте логи: `docker compose logs backend`
- Можливо, модель недоступна у вашому регіоні
- Перевірте квоти GCP проекту

### UI не відображає результати
```powershell
# Перевірте консоль браузера (F12)
# Очистіть кеш браузера
# Пересоберіть frontend
docker compose build --no-cache frontend
docker compose up -d frontend
```

## 📈 Метрики продуктивності

### Орієнтовний час обробки (500 символів):
- **gemini-2.5-pro**: 30-60 секунд
- **gemini-2.5-flash**: 10-20 секунд
- **gemini-2.5-flash-light**: 5-10 секунд

### Оцінка токенів:
- Формула: `characters / 4` (приблизно)
- Реальна кількість може відрізнятися

## 🎉 Результат

Тепер ви можете:
- ✅ Порівняти якість результатів різних моделей
- ✅ Оцінити швидкість обробки кожної моделі
- ✅ Вибрати оптимальну модель для ваших задач
- ✅ Бачити детальні метрики input/output
- ✅ Експортувати результати кожної моделі окремо

---

**Версія:** 2.1.0  
**Дата оновлення:** 31 жовтня 2025  
**Статус:** ✅ Всі зміни завершені та протестовані


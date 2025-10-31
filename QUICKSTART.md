# 🚀 Quick Start Guide

Запуск Gemini Text Structurer за 3 хвилини.

## Крок 1: Налаштування `.env`

```powershell
# Копіюємо шаблон
Copy-Item env.example .env

# Редагуємо конфігурацію
notepad .env
```

**Обов'язково змініть:**
- `HOST_GEMINI_DIR` - шлях до ваших Gemini креденшелів
- `GOOGLE_CLOUD_PROJECT` - ваш GCP project ID

```ini
HOST_GEMINI_DIR=C:\Users\YourUser\.gemini
GEMINI_MODEL=gemini-2.5-flash
GOOGLE_CLOUD_PROJECT=your-project-id
API_PORT=8000                # Backend port (опціонально)
FRONTEND_PORT=3000           # Frontend port (опціонально)
```

## Крок 2: Збірка і запуск

```powershell
# Збираємо Docker образи
docker compose build

# Запускаємо сервіси
docker compose up -d

# Перевіряємо статус
docker compose ps
```

Очікуємо:
```
NAME               STATUS         PORTS
gemini-backend     Up (healthy)   8000/tcp
gemini-frontend    Up (healthy)   0.0.0.0:3000->80/tcp
```

## Крок 3: Відкриваємо додаток

**Web Interface:** http://localhost:3000

**API Docs:** http://localhost:3000/api/docs

## Перевірка роботи

```powershell
# Health check
curl http://localhost:3000/api/health

# Тестовий запит
$body = @{
    text = "Стаття про AI. Дата: 31 жовтня 2025. AI змінює світ."
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:3000/api/structure `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

## Troubleshooting

### Порти зайняті
```powershell
# Змініть FRONTEND_PORT в .env
$env:FRONTEND_PORT=8080
docker compose up -d
```

### Backend не запускається
```powershell
# Перевіряємо логи
docker compose logs backend

# Перевіряємо креденшели
Test-Path $env:HOST_GEMINI_DIR
```

### Frontend білий екран
```powershell
# Пересобираємо frontend
docker compose build --no-cache frontend
docker compose up -d frontend
```

## Корисні команди

```powershell
# Зупинити все
docker compose down

# Переглянути логи
docker compose logs -f

# Перезапустити сервіс
docker compose restart backend

# Видалити все (з даними)
docker compose down -v
```

## Що далі?

- Читайте [README.md](README.md) для повної документації
- Використовуйте gemini-2.5-flash (найкращий баланс для free tier)
- Перегляньте API docs на http://localhost:3000/api/docs

---

**Підтримка:** Якщо виникли проблеми, перевірте секцію Troubleshooting в README.md


# Gemini Text Structurer

Модерний full-stack застосунок для перетворення неструктурованого тексту у структурований JSON за допомогою Google Gemini AI.

## Можливості
- сучасний інтерфейс на React + TypeScript з темною темою
- асинхронний FastAPI backend із суворою модульністю
- інтеграція з Gemini CLI (flash та pro моделі)
- автоматична валідація JSON через Pydantic
- контейнеризація Docker Compose
- готові сценарії копіювання/завантаження результатів

## Архітектура

```
┌─────────────────┐         ┌──────────────────┐         ┌────────────────┐
│   Frontend      │  HTTP   │     Backend      │  CLI    │  Gemini AI     │
│   (React+TS)    │────────▶│    (FastAPI)     │────────▶│  (Google)      │
│   Port: 3000    │         │    Port: 8000    │         │                │
└─────────────────┘         └──────────────────┘         └────────────────┘
        │                            │
        │    Nginx Reverse Proxy     │
        └────────────────────────────┘
```

## Технологічний стек

**Frontend**: React 18, TypeScript (strict mode), Vite, Nginx (production)

**Backend**: FastAPI 0.115+, Python 3.12, Pydantic v2, asyncio

**Інфраструктура**: Docker Compose, Gemini CLI (npm), multi-stage Dockerfile

## Структура проєкту

```
Gemini CLI/
├── backend/
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   ├── core/             # Config & exceptions
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── main.py           # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── types/
│   │   ├── styles/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── nginx.conf
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env
└── README.md
```

## Швидкий старт

### Передумови
- Docker Desktop (Windows)
- Налаштовані облікові дані Gemini CLI (`gemini configure` у локальній системі)
- Google Cloud Project ID

### Клонування та початкове налаштування

```powershell
git clone <repo-url>
cd "Gemini CLI"

# Скопіювати шаблон конфігурації
Copy-Item env.example .env

# Відкрити для редагування
notepad .env
```

### Конфігурація `.env`

Заповніть ключові змінні середовища:

```ini
HOST_GEMINI_DIR=C:\Users\YourUser\.gemini
GEMINI_CLI=gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MODELS=gemini-2.5-flash,gemini-2.5-pro
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
API_PORT=8000
FRONTEND_PORT=3000
VITE_GEMINI_MODEL=gemini-2.5-flash
```

> **Правила конфігурації моделей**
> - `GEMINI_MODEL` — дефолтне значення для бекенду, якщо запит не передає `model`.
> - `GEMINI_MODELS` — список доступних моделей через кому. Може містити одну або кілька позицій (наприклад, `gemini-2.5-flash,gemini-2.5-pro`).
> - `VITE_GEMINI_MODEL` — модель, попередньо обрана у UI; вона має входити до `GEMINI_MODELS`.
> - Підтримуйте синхронізацію цих трьох змінних при додаванні/видаленні моделей.

### Запуск у Docker

```powershell
# Повна збірка образів
docker compose build --no-cache

# Старт сервісів
docker compose up -d

# Перегляд логів
docker compose logs -f
```

### Доступ до застосунку
- Frontend: http://localhost:3000
- Backend health: http://localhost:3000/api/health
- Swagger UI: http://localhost:3000/api/docs

## Використання

### Веб-інтерфейс
1. Відкрийте фронтенд у браузері.
2. Вставте неструктурований текст.
3. За потреби оберіть модель у *Advanced Settings*.
4. Натисніть **Structure Text** і дочекайтеся результату.
5. Користуйтеся кнопками **Copy** або **Download** для експорту JSON.

### API

**Health Check**

```bash
curl http://localhost:3000/api/health
```

**Structure Text**

```powershell
$body = @{
    text = "Неструктурований текст про AI..."
    model = "gemini-2.5-pro"
} | ConvertTo-Json -Compress

Invoke-RestMethod -Uri http://localhost:3000/api/structure `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $body
```

## Розробка

### Backend

```powershell
docker compose exec backend bash
pytest  # коли тести будуть додані
docker compose logs -f backend
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
# або всередині контейнера
docker compose exec frontend sh
```

### Перевірка збірки

Перед кожним PR/комітом фронтенду виконуйте продакшн-збірку:

```powershell
npm run build
```

Цей самий крок рекомендується додати в CI, щоб виявляти `tsc`/Vite-помилки та невикористані символи.

## Тестування

**Backend**

```bash
pytest backend/tests/
pytest backend/tests/integration/
pytest --cov=app --cov-report=html
```

**Frontend**

```bash
npm test
npm run test:e2e
```

## Усунення несправностей
- *Model '...'' is not allowed* — перевірте, що вибрана модель додана до `GEMINI_MODELS` і контейнер перезібраний.
- CLI timeout — збільшіть `gemini_timeout` у `backend/app/core/config.py` та рестартуйте бекенд.
- Немає доступу до Gemini — переконайтеся, що облікові дані змонтовані у `HOST_GEMINI_DIR` та флаг `GEMINI_CLI` вказує на доступну CLI.

## Моніторинг та логи

```powershell
# Статус контейнерів
docker compose ps

# Health-перевірки всередині контейнерів
docker compose exec backend curl http://localhost:8000/health
docker compose exec frontend wget -q -O- http://localhost:80

# Поточні логи
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend
```

## Збереження даних
Результати зберігаються у volume `backend-data`.

```powershell
docker volume ls
docker volume inspect gemini-cli_backend-data
docker run --rm -v gemini-cli_backend-data:/data -v ${PWD}:/backup alpine `
  tar czf /backup/data-backup.tar.gz /data
```

## Безпека
- запуск сервісів під non-root користувачем у контейнерах
- монтування credential-директорій лише в режимі read-only
- CORS налаштований під фронтенд
- винятки та логування без чутливих даних
- Pydantic гарантує валідацію введення

## Внесок
1. Дотримуйтеся SOLID та асинхронних практик.
2. Пишіть типи (Python typing / TypeScript strict).
3. Додавайте тести для нової логіки.
4. Оновлюйте документацію та приклади.
5. Перевіряйте `npm run build` перед створенням PR.

## Ліцензія
MIT License

---

**Версія:** 2.0.0  
**Останнє оновлення:** 1 листопада 2025 року

# Gemini CLI Service (Docker Compose)

FastAPI сервіс, який викликає Gemini CLI в неінтерактивному режимі для структурування неструктурованого тексту у JSON.

## Можливості

- 🚀 **FastAPI REST API** з асинхронною обробкою
- 🤖 **Gemini CLI integration** через Docker
- 📦 **Автоматична валідація** вихідного JSON за Pydantic-схемою
- 🔒 **Безпечне монтування** креденшелів з хоста
- 📊 **Структурування тексту** з автоматичним визначенням title, date, summary, tags, sections

## Вимоги

- Docker Desktop на Windows
- Аутентифіковані креденшели Gemini CLI у `C:\Users\<YourUser>\.gemini`
- Google Cloud Project ID (для workspace GCA)

## Швидкий старт

### 1. Налаштування `.env`

```powershell
# Копіюємо приклад і редагуємо
Copy-Item env.example .env
notepad .env
```

**Обов'язкові параметри в `.env`:**
```ini
HOST_GEMINI_DIR=C:\Users\E6440\.gemini
GEMINI_CLI=gemini
GEMINI_MODEL=gemini-2.5-flash  # Available: gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-light
GOOGLE_CLOUD_PROJECT=your-actual-gcp-project-id  # <-- Вставте свій project ID!
API_PORT=8000
```

### 2. Збірка і запуск

```powershell
docker compose build --no-cache
docker compose up -d
```

### 3. Перевірка здоров'я

```powershell
curl http://localhost:8000/health
# Відповідь: {"status":"ok"}
```

## Використання API

### Ендпоінт: `POST /structure`

Структурує неструктурований текст у JSON.

**Request:**
```powershell
$body = @{
    text = "Неструктурований текст про AI. Дата: 31 жовтня 2025. Теми: машинне навчання, нейронні мережі."
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/structure `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $body
```

**Response:**
```json
{
  "id": "abc123...",
  "json_path": "data/abc123....json",
  "data": {
    "title": "AI and Machine Learning",
    "date_iso": "2025-10-31",
    "summary": "Короткий опис тексту",
    "tags": ["AI", "ML", "neural networks"],
    "sections": [
      {
        "name": "Introduction",
        "content": "..."
      }
    ]
  }
}
```

### Додаткові параметри

```json
{
  "text": "ваш текст...",
  "out_dir": "custom_output",        // необов'язково
  "cli_command": "gemini",            // необов'язково
  "model": "gemini-2.5-flash"         // необов'язково (gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-light)
}
```

## Архітектура

```
┌─────────────┐     HTTP POST       ┌──────────────┐
│   Frontend  │ ──────────────────> │  FastAPI     │
│             │                     │  (port 8000) │
└─────────────┘                     └──────┬───────┘
                                           │
                                           │ subprocess
                                           v
                                    ┌──────────────┐
                                    │  Gemini CLI  │
                                    │  (npm global)│
                                    └──────┬───────┘
                                           │
                                           │ authenticated
                                           v
                                    ┌──────────────┐
                                    │  Google AI   │
                                    │  (GCP)       │
                                    └──────────────┘
```

## Структура проєкту

```
Gemini CLI/
├── docker-compose.yml      # Compose config
├── Dockerfile              # Multi-stage build (Node.js + Python)
├── entrypoint.sh           # Credential staging script
├── env.example             # Environment variables template
├── README.md               # Ця документація
└── app/
    ├── requirements.txt    # Python deps (FastAPI, uvicorn, pydantic)
    └── app/
        └── main_cli.py     # FastAPI application
```

## Технічні деталі

### Entrypoint механізм

`entrypoint.sh` при старті контейнера:
1. Копіює креденшели з `/host_gemini` (змонтована `C:\Users\E6440\.gemini`)
2. Дублює у `/home/app/.gemini`, `/home/app/.config/gemini`, `/home/app/.config/@google/gemini`
3. Встановлює права доступу для користувача `app`
4. Додає `/home/app/.local/bin` до `PATH` (для `uvicorn`)

### JSON парсинг

Gemini CLI повертає відповідь у форматі:
```json
{
  "response": "```json\n{...}\n```"
}
```

Парсер автоматично:
- Розпаковує `response` поле
- Видаляє markdown code blocks (` ```json ... ``` `)
- Валідує фінальний JSON за Pydantic-схемою

### Валідація схеми

```python
class StructuredDoc(BaseModel):
    title: str
    date_iso: str              # ISO 8601 (YYYY-MM-DD)
    summary: str
    tags: list[str] = []
    sections: list[dict] = []  # [{"name": "...", "content": "..."}]
```

## Управління

### Перезапуск

```powershell
docker compose restart gemini-cli-api
```

### Перегляд логів

```powershell
docker compose logs -f gemini-cli-api
```

### Зупинка

```powershell
docker compose down
```

### Оновлення коду

```powershell
# Код монтується як volume, тому зміни застосовуються одразу
docker compose restart gemini-cli-api
```

## Troubleshooting

### Помилка: `ProjectIdRequiredError`

**Причина:** Не встановлено `GOOGLE_CLOUD_PROJECT` у `.env`

**Рішення:**
```powershell
# Відредагуйте .env і додайте свій project ID
notepad .env
# Перезапустіть контейнер
docker compose restart gemini-cli-api
```

### Помилка: `Connection failed for 'MCP_DOCKER'`

**Причина:** Gemini CLI шукає MCP сервери, які недоступні в контейнері

**Рішення:** Ця помилка не критична — CLI продовжує працювати з основною моделлю.

### Помилка: `CLI did not return valid JSON`

**Причина:** Gemini повернув текст замість JSON

**Рішення:** Перевірте промпт у `build_prompt()` — він повинен чітко вимагати JSON.

### Помилка: `Schema validation failed`

**Причина:** JSON не відповідає очікуваній структурі

**Рішення:** Перевірте логи (`docker compose logs`) і адаптуйте `StructuredDoc` модель або промпт.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HOST_GEMINI_DIR` | ✅ Yes | - | Шлях до `.gemini` на хості |
| `GEMINI_CLI` | No | `gemini` | Команда CLI |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Модель Gemini (2.5-pro, 2.5-flash, 2.5-flash-light) |
| `GOOGLE_CLOUD_PROJECT` | ✅ Yes | - | GCP Project ID |
| `API_PORT` | No | `8000` | Порт FastAPI |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/structure` | Структурування тексту |

## Залежності

### Python (requirements.txt)
- `fastapi==0.115.5`
- `uvicorn[standard]==0.32.0`
- `pydantic==2.9.2`

### System (Dockerfile)
- `python:3.12-slim`
- `nodejs` + `npm`
- `@google/gemini-cli` (npm global)

## Розробка

### Додавання нових полів до схеми

1. Оновіть `StructuredDoc` в `main_cli.py`:
```python
class StructuredDoc(BaseModel):
    title: str
    # ... existing fields
    new_field: str = Field(default="", description="New field")
```

2. Оновіть промпт у `build_prompt()`:
```python
def build_prompt(text: str) -> str:
    return (
        "Return JSON with: title, date_iso, summary, tags, sections, new_field\n"
        # ...
    )
```

3. Перезапустіть: `docker compose restart gemini-cli-api`

## Ліцензія

MIT License

## Автор

Created for structuring unstructured text via Gemini CLI in containerized environment.

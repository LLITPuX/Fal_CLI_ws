# Gemini Text Structurer

Modern full-stack application for structuring unstructured text using Google Gemini AI.

## 🚀 Features

- **Modern Web Interface** - React + TypeScript with beautiful dark theme UI
- **FastAPI Backend** - Async-first, modular architecture with SOLID principles
- **Gemini AI Integration** - Multiple model support (2.5-pro, 2.5-flash, 2.5-flash-light)
- **JSON Validation** - Automatic schema validation with Pydantic
- **Docker Compose** - Full containerized deployment
- **Real-time Processing** - Async operations with loading states
- **Copy & Download** - Export structured results as JSON

## 📋 Architecture

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

### Stack

**Frontend:**
- React 18
- TypeScript (strict mode)
- Vite (build tool)
- Nginx (production server)

**Backend:**
- FastAPI 0.115+
- Python 3.12
- Pydantic v2 (validation)
- Async/await patterns

**Infrastructure:**
- Docker Compose
- Gemini CLI (npm global)
- Multi-stage builds

## 🎯 Project Structure

```
Gemini CLI/
├── backend/
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── core/             # Config & exceptions
│   │   │   ├── config.py
│   │   │   └── exceptions.py
│   │   ├── models/           # Pydantic schemas
│   │   │   └── schemas.py
│   │   ├── services/         # Business logic
│   │   │   └── gemini_service.py
│   │   └── main.py           # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── TextInput.tsx
│   │   │   ├── JsonViewer.tsx
│   │   │   └── ErrorMessage.tsx
│   │   ├── services/         # API client
│   │   │   └── api.ts
│   │   ├── types/            # TypeScript types
│   │   │   └── api.ts
│   │   ├── styles/
│   │   │   └── App.css
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── nginx.conf
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env
└── README.md
```

## 🛠️ Setup & Installation

### Prerequisites

- Docker Desktop (Windows)
- Google Gemini credentials in `C:\Users\<YourUser>\.gemini`
- Google Cloud Project ID

### 1. Clone & Configure

```powershell
# Copy environment template
Copy-Item .env.new .env

# Edit .env with your settings
notepad .env
```

**Required `.env` variables:**

```ini
HOST_GEMINI_DIR=C:\Users\YourUser\.gemini
GEMINI_CLI=gemini
GEMINI_MODEL=gemini-2.5-flash
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
API_PORT=8000
FRONTEND_PORT=3000
```

### 2. Build & Run

```powershell
# Build all services
docker compose build --no-cache

# Start services
docker compose up -d

# Check logs
docker compose logs -f
```

### 3. Access Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:3000/api/health
- **API Docs:** http://localhost:3000/api/docs

## 📖 Usage

### Web Interface

1. Open http://localhost:3000
2. Paste unstructured text in the textarea
3. (Optional) Configure model in Advanced Settings
4. Click "Structure Text"
5. View structured result with:
   - Title, date, summary, tags
   - Sections with content
   - Copy to clipboard or download JSON

### API Endpoints

#### Health Check

```bash
curl http://localhost:3000/api/health
```

Response:
```json
{"status": "ok", "service": "gemini-text-structurer"}
```

#### Structure Text

```powershell
$body = @{
    text = "Неструктурований текст про AI..."
    model = "gemini-2.5-flash"
} | ConvertTo-Json -Compress

Invoke-RestMethod -Uri http://localhost:3000/api/structure `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body $body
```

Response:
```json
{
  "id": "abc123...",
  "json_path": "data/abc123.json",
  "data": {
    "title": "AI Overview",
    "date_iso": "2025-10-31",
    "summary": "...",
    "tags": ["AI", "ML"],
    "sections": [
      {"name": "Introduction", "content": "..."}
    ]
  }
}
```

## 🔧 Development

### Backend Development

```powershell
# Enter backend container
docker compose exec backend bash

# Run tests (when implemented)
pytest

# Check logs
docker compose logs -f backend
```

### Custom Ports

Якщо потрібно змінити порти:

```ini
# .env
API_PORT=9000        # Backend internal port
FRONTEND_PORT=8080   # Frontend external port
```

Після зміни:
```powershell
docker compose down
docker compose build
docker compose up -d
```

### Frontend Development

```powershell
# Local development (requires Node.js)
cd frontend
npm install
npm run dev

# Or use container
docker compose exec frontend sh
```

### Hot Reload

Both services support hot reload in development:
- **Backend:** `/app/app` mounted as volume
- **Frontend:** Vite HMR through Nginx proxy

## 🐛 Troubleshooting

### Backend Issues

**Error: `ProjectIdRequiredError`**
```powershell
# Ensure GOOGLE_CLOUD_PROJECT is set in .env
notepad .env
docker compose restart backend
```

**Error: CLI timeout**
```
# Increase timeout in backend/app/core/config.py
gemini_timeout: int = 120  # seconds
docker compose restart backend
```

### Frontend Issues

**Cannot connect to backend**
```powershell
# Check backend health
docker compose ps
curl http://localhost:3000/api/health

# Check nginx config
docker compose exec frontend cat /etc/nginx/conf.d/default.conf
```

**Build fails**
```powershell
# Clear cache and rebuild
docker compose down
docker compose build --no-cache frontend
docker compose up -d
```

## 🧪 Testing

### Backend Tests

```bash
# Unit tests
pytest backend/tests/

# Integration tests
pytest backend/tests/integration/

# Coverage
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
# Unit tests
npm test

# E2E tests (when implemented)
npm run test:e2e
```

## 📊 Monitoring

### Container Health

```powershell
# Check status
docker compose ps

# Health checks
docker compose exec backend curl http://localhost:8000/health
docker compose exec frontend wget -q -O- http://localhost:80
```

### Logs

```powershell
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend

# Tail last 100 lines
docker compose logs --tail=100 backend
```

## 🚀 Deployment

### Production Build

```powershell
# Build production images
docker compose -f docker-compose.yml build

# Deploy
docker compose up -d

# Scale (if needed)
docker compose up -d --scale backend=3
```

### Environment Variables

Production `.env`:
```ini
HOST_GEMINI_DIR=C:\Production\.gemini
GEMINI_MODEL=gemini-2.5-pro
GOOGLE_CLOUD_PROJECT=production-project-id
FRONTEND_PORT=80
```

## 📦 Data Persistence

Structured documents are saved in Docker volume `backend-data`:

```powershell
# List volumes
docker volume ls

# Inspect volume
docker volume inspect gemini-cli_backend-data

# Backup volume
docker run --rm -v gemini-cli_backend-data:/data -v ${PWD}:/backup alpine tar czf /backup/data-backup.tar.gz /data
```

## 🔒 Security

- Non-root user in containers
- Read-only credential mounting
- CORS configured for frontend origin
- No sensitive data in logs
- Input validation with Pydantic
- Error sanitization in responses

## 🤝 Contributing

1. Follow SOLID principles
2. Use async/await for I/O
3. Add type hints (Python) / strict types (TS)
4. Write tests for new features
5. Update documentation

## 📝 License

MIT License

## 👤 Author

Created for structuring unstructured text via Gemini AI in modern containerized environment.

---

**Version:** 2.0.0  
**Last Updated:** October 31, 2025

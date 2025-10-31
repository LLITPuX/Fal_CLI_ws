# ⚠️ Gemini API Quota Limits

## Проблема "Resource exhausted" (Error 429)

Якщо ви бачите помилку **429** або **"Resource exhausted"**, це означає що ви досягли ліміту запитів до Gemini API.

### 🔍 Типові помилки:

```
Error 429: Resource exhausted. Please try again later.
```

```
JSONParsingError: Empty or invalid response from CLI
```

## 📊 Ліміти Gemini API (Free Tier)

### Gemini 2.5 Models
- **gemini-2.5-pro**: 2 requests per minute (RPM)
- **gemini-2.5-flash**: 15 RPM
- **gemini-1.5-flash-8b**: 15 RPM

### Dengi Limits
- Daily: 1,500 requests per day
- Rate limit resets every minute

## 🛠️ Рішення проблеми

### 1. Зачекайте кілька хвилин
Найпростіше рішення - почекати 1-2 хвилини перед наступним запитом.

### 2. Використовуйте швидші моделі
```bash
# Замість gemini-2.5-pro використовуйте:
gemini-2.5-flash       # швидше і більше RPM
gemini-1.5-flash-8b    # найшвидше
```

### 3. Збільште квоти (Paid Tier)

Перейдіть на платний план Google Cloud:
- **Pay-as-you-go**: $0.001 - $0.075 per 1K characters
- Вищі ліміти: до 1000 RPM

**Як увімкнути:**
1. Відкрийте [Google Cloud Console](https://console.cloud.google.com/)
2. Оберіть проект
3. Перейдіть до **APIs & Services** → **Gemini API**
4. Налаштуйте billing account
5. Увімкніть paid quota

### 4. Використовуйте затримки між запитами

Якщо тестуєте багато разів, додайте затримки:

**Frontend** (для розробників):
```typescript
// У api.ts додайте затримку між запитами
await new Promise(resolve => setTimeout(resolve, 60000)); // 1 хвилина
```

**Backend** (для production):
```python
# У routes.py додайте затримку між моделями
import asyncio

for model in settings.gemini_models:
    # ... обробка моделі
    await asyncio.sleep(5)  # 5 секунд між моделями
```

### 5. Тестуйте з однією моделлю

Замість тестування всіх трьох моделей одночасно, тестуйте по одній:

```bash
# У .env тимчасово змініть:
GEMINI_MODEL=gemini-2.5-flash  # тільки одна модель
```

Або модифікуйте `config.py`:
```python
# Тимчасово використовуйте тільки одну модель
gemini_models: list[str] = [
    "gemini-2.5-flash",  # закоментуйте інші
    # "gemini-2.5-pro",
    # "gemini-1.5-flash-8b",
]
```

## 📈 Моніторинг квот

### Перевірте поточне використання:

1. **Google Cloud Console**:
   - https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
   - Перегляньте "Requests per minute" та "Requests per day"

2. **Логи Backend**:
```bash
docker compose logs backend | grep "429\|Resource exhausted"
```

### Типові сценарії:

#### Сценарій 1: Розробка і тестування
- Використовуйте `gemini-2.5-flash` (баланс між швидкістю і точністю)
- Тестуйте з невеликими текстами
- Робіть паузи між тестами (1-2 хвилини)

#### Сценарій 2: Production
- Налаштуйте paid tier
- Використовуйте rate limiting middleware
- Додайте retry logic з exponential backoff

#### Сценарій 3: Порівняння моделей
- Тестуйте по одній моделі за раз
- Робіть паузи між моделями (мінімум 30 секунд)
- Враховуйте що `gemini-2.5-pro` має найнижчий RPM (2)

## 🔧 Налаштування для роботи з квотами

### Додайте затримки між моделями:

**backend/app/api/routes.py**:
```python
import asyncio

# Додайте після кожної обробки моделі
results.append(model_result)

# Затримка між моделями (крім останньої)
if model != settings.gemini_models[-1]:
    await asyncio.sleep(30)  # 30 секунд пауза
```

### Додайте retry logic:

**backend/app/services/gemini_service.py**:
```python
async def run_cli_with_retry(self, prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await self.run_cli(prompt)
        except CLIExecutionError as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 10  # exponential backoff
                logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                raise
```

## ⚡ Швидке виправлення зараз

**Якщо зараз бачите помилку 429:**

1. Зачекайте **2 хвилини**
2. Тимчасово вимкніть багатомодельне тестування:

```python
# backend/app/core/config.py
gemini_models: list[str] = [
    "gemini-2.5-flash",  # тільки одна модель
]
```

3. Пересоберіть та перезапустіть:
```bash
docker compose build backend
docker compose restart backend
```

4. Спробуйте знову через 2 хвилини

## 📚 Додаткова інформація

- [Gemini API Pricing](https://ai.google.dev/pricing)
- [Gemini API Quotas](https://cloud.google.com/vertex-ai/docs/quotas)
- [Rate Limiting Best Practices](https://cloud.google.com/apis/docs/rate-limits)

---

**Підсумок:**
- Free tier має суворі ліміти (2-15 RPM)
- Робіть паузи між запитами
- Для production використовуйте paid tier
- Додайте retry logic з exponential backoff


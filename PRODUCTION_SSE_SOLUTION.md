# Полное решение SSE для MCP Restaurant Optimizer

## Обзор решения

Данное решение предоставляет полнофункциональный SSE (Server-Sent Events) endpoint для потоковой передачи ресторанных данных в реальном времени, готовый к развертыванию на продакшен домене `https://mcp.madlen.space/api/v1/mcp/sse`.

## Архитектура

### 1. Основные компоненты

```
app/
├── services/
│   ├── sse_service.py              # Основной SSE сервис
│   └── database_integration.py     # Интеграция с БД
├── api/v1/
│   ├── endpoints.py                # Существующие API endpoints
│   └── sse_endpoints.py            # Новые SSE endpoints
└── main.py                         # Главный файл приложения
```

### 2. Возможности

- **Потоковые данные**: Продажи, бронирования, загрузка зала, смены сотрудников
- **Авторизация**: Bearer tokens, API keys, IP фильтрация
- **Масштабируемость**: Поддержка множественных соединений
- **Интеграция с БД**: PostgreSQL, MongoDB, SQLAlchemy
- **Кеширование**: Для снижения нагрузки на БД
- **Мониторинг**: Статус соединений, метрики

## Установка и настройка

### 1. Добавление в существующий проект

```python
# app/main.py
from app.api.v1.sse_endpoints import router as sse_router

app.include_router(sse_router)
```

### 2. Переменные окружения

```env
# .env
DATABASE_URL=postgresql://user:password@localhost/mcp_restaurant
DATABASE_TYPE=postgresql
SSE_CACHE_TTL=30
JWT_SECRET_KEY=your-secret-key
ENVIRONMENT=production
```

### 3. Конфигурация Nginx

```nginx
# /etc/nginx/sites-available/mcp.madlen.space
server {
    listen 443 ssl http2;
    server_name mcp.madlen.space;
    
    ssl_certificate /etc/letsencrypt/live/mcp.madlen.space/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp.madlen.space/privkey.pem;
    
    # Основное приложение
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Специальная конфигурация для SSE
    location /api/v1/mcp/sse {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Критические настройки для SSE
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        
        # Увеличенные таймауты
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # SSE заголовки
        add_header Cache-Control 'no-cache, no-store, must-revalidate';
        add_header Pragma 'no-cache';
        add_header Expires '0';
        add_header X-Accel-Buffering 'no';
        
        # CORS
        add_header Access-Control-Allow-Origin '*';
        add_header Access-Control-Allow-Methods 'GET, OPTIONS';
        add_header Access-Control-Allow-Headers 'Authorization, Content-Type';
    }
}
```

## API Endpoints

### 1. Основной SSE поток

```
GET /api/v1/mcp/sse
```

**Параметры:**
- `department_id` (optional): UUID подразделения
- `interval` (optional): Интервал между событиями (1-60 секунд)

**Авторизация:**
- Внутренние запросы: без авторизации
- Внешние запросы: Bearer token

**Пример подключения:**
```javascript
const eventSource = new EventSource('https://mcp.madlen.space/api/v1/mcp/sse?department_id=4cb558ca-a8bc-4b81-871e-043f65218c50&interval=5');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Event:', data.type, data.data);
};
```

### 2. Статус сервиса

```
GET /api/v1/mcp/sse/status
```

**Ответ:**
```json
{
    "status": "active",
    "active_connections": 15,
    "service": "MCP Restaurant SSE",
    "version": "1.0.0"
}
```

### 3. Отключение клиента

```
POST /api/v1/mcp/sse/disconnect/{client_id}
```

## Типы событий

### 1. Продажи (sales)

```json
{
    "type": "sales",
    "timestamp": "2025-07-11T10:00:00Z",
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "data": {
        "total_sales": 150000.0,
        "total_transactions": 120,
        "average_check": 1250.0,
        "period": "last_hour",
        "currency": "RUB",
        "top_dishes": [
            {"name": "Борщ", "count": 15},
            {"name": "Салат Цезарь", "count": 12}
        ]
    }
}
```

### 2. Бронирования (bookings)

```json
{
    "type": "bookings",
    "timestamp": "2025-07-11T10:00:05Z",
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "data": {
        "total_bookings_today": 45,
        "confirmed_bookings": 40,
        "pending_bookings": 3,
        "cancelled_bookings": 2,
        "next_booking_time": "2025-07-11T12:30:00Z",
        "average_party_size": 3.2
    }
}
```

### 3. Загрузка зала (occupancy)

```json
{
    "type": "occupancy",
    "timestamp": "2025-07-11T10:00:10Z",
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "data": {
        "current_occupancy_percent": 75.5,
        "total_tables": 45,
        "occupied_tables": 34,
        "available_tables": 11,
        "waiting_queue": 3,
        "average_visit_duration": 85
    }
}
```

### 4. Смены сотрудников (shifts)

```json
{
    "type": "shifts",
    "timestamp": "2025-07-11T10:00:15Z",
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "data": {
        "total_staff_today": 15,
        "currently_working": 12,
        "on_break": 2,
        "departments": {
            "kitchen": {"working": 4, "planned": 5},
            "service": {"working": 6, "planned": 7},
            "bar": {"working": 2, "planned": 2}
        }
    }
}
```

## Интеграция с базой данных

### 1. Активация режима БД

```python
# app/services/sse_service.py
class SSEService:
    def __init__(self):
        # Для продакшена установить False
        self._demo_mode = False
        
        # Настройка провайдера БД
        self._db_provider = CachedDatabaseSSEProvider(
            db_url=settings.database_url,
            db_type=settings.database_type,
            cache_ttl=30
        )
```

### 2. Структура таблиц PostgreSQL

```sql
-- Продажи
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    department_id UUID NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    order_items JSONB
);

-- Бронирования
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    department_id UUID NOT NULL,
    booking_date DATE NOT NULL,
    booking_time TIME NOT NULL,
    party_size INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Столы
CREATE TABLE tables (
    id SERIAL PRIMARY KEY,
    department_id UUID NOT NULL,
    table_number INTEGER NOT NULL,
    seats INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'available',
    zone VARCHAR(50)
);

-- Смены
CREATE TABLE shifts (
    id SERIAL PRIMARY KEY,
    department_id UUID NOT NULL,
    employee_id UUID NOT NULL,
    shift_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME,
    position VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active'
);
```

### 3. Замена демо-данных на реальные

```python
# app/services/sse_service.py
async def _get_sales_event(self, department_id: str) -> Dict:
    """Получение реальных данных о продажах"""
    if self._db_provider:
        return await self._db_provider.get_real_sales_data(department_id)
    
    # Fallback на внешнее API
    async with HTTPClient() as client:
        data = await client.get_aqniet("sales/hourly", {...})
        return self._format_sales_data(data)
```

## Безопасность

### 1. Настройка авторизации

```python
# app/api/v1/sse_endpoints.py
async def validate_sse_access(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    if settings.environment == "production":
        if not credentials and not _is_internal_request(request):
            raise HTTPException(401, "Authentication required")
        
        if credentials:
            # Проверка JWT токена
            await validate_jwt_token(credentials.credentials)
    
    return {"authenticated": True}
```

### 2. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/sse")
@limiter.limit("10/minute")
async def stream_restaurant_data(request: Request, ...):
    # ...
```

### 3. IP Whitelist

```python
ALLOWED_IPS = [
    "192.168.1.0/24",  # Внутренняя сеть
    "10.0.0.0/8",      # Приватные IP
    "127.0.0.1",       # Localhost
]

def is_ip_allowed(ip: str) -> bool:
    return any(ipaddress.ip_address(ip) in ipaddress.ip_network(allowed) 
              for allowed in ALLOWED_IPS)
```

## Мониторинг и производительность

### 1. Метрики

```python
# Количество активных соединений
active_connections = sse_service.get_active_connections_count()

# Использование памяти
import psutil
memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB

# Время отклика БД
start_time = time.time()
await db_provider.get_sales_data(department_id)
db_response_time = time.time() - start_time
```

### 2. Логирование

```python
# app/services/sse_service.py
logger.info(f"SSE соединение: client_id={client_id}, IP={client_ip}")
logger.warning(f"Высокая нагрузка: {active_connections} соединений")
logger.error(f"Ошибка БД: {error}")
```

### 3. Алерты

```python
# Настройка алертов
if active_connections > 100:
    send_alert("Высокая нагрузка на SSE сервис")

if db_response_time > 5.0:
    send_alert("Медленные запросы к БД")
```

## Развертывание

### 1. Systemd сервис

```ini
# /etc/systemd/system/mcp-sse.service
[Unit]
Description=MCP Restaurant Optimizer SSE Service
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/mcp-restaurant-optimizer
Environment=PATH=/opt/mcp-restaurant-optimizer/venv/bin
ExecStart=/opt/mcp-restaurant-optimizer/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Запуск в продакшене

```bash
# Активация сервиса
sudo systemctl enable mcp-sse
sudo systemctl start mcp-sse

# Проверка статуса
sudo systemctl status mcp-sse

# Логи
sudo journalctl -u mcp-sse -f
```

### 3. Балансировка нагрузки

```nginx
# Upstream для нескольких инстансов
upstream mcp_backend {
    least_conn;
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

location /api/v1/mcp/sse {
    proxy_pass http://mcp_backend;
    # ... остальные настройки
}
```

## Тестирование

### 1. Функциональное тестирование

```bash
# Проверка доступности
curl -I https://mcp.madlen.space/api/v1/mcp/sse/status

# Тест SSE потока
curl -H "Accept: text/event-stream" https://mcp.madlen.space/api/v1/mcp/sse

# Тест с авторизацией
curl -H "Authorization: Bearer your-token" \
     -H "Accept: text/event-stream" \
     https://mcp.madlen.space/api/v1/mcp/sse
```

### 2. Нагрузочное тестирование

```python
# test_sse_load.py
import asyncio
import aiohttp

async def test_concurrent_connections():
    """Тест множественных SSE соединений"""
    sessions = []
    
    for i in range(100):
        session = aiohttp.ClientSession()
        sessions.append(session)
        
        async with session.get('https://mcp.madlen.space/api/v1/mcp/sse') as resp:
            async for line in resp.content:
                if line:
                    print(f"Session {i}: {line.decode()}")
                    break
    
    for session in sessions:
        await session.close()

asyncio.run(test_concurrent_connections())
```

### 3. Интеграционное тестирование

```python
# tests/test_sse_integration.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_sse_with_real_data():
    """Тест SSE с реальными данными"""
    async with AsyncClient() as client:
        async with client.stream("GET", "http://localhost:8000/api/v1/mcp/sse") as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "text/event-stream; charset=utf-8"
            
            event_count = 0
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    event_count += 1
                    if event_count >= 3:
                        break
            
            assert event_count >= 3
```

## Заключение

Данное решение предоставляет:

✅ **Готовый к продакшену SSE endpoint** на `https://mcp.madlen.space/api/v1/mcp/sse`
✅ **Интеграцию с основным приложением** без отдельных портов
✅ **Полную совместимость с nginx** и domain-based routing
✅ **Безопасность и авторизацию** для внешних запросов
✅ **Интеграцию с базой данных** для реальных данных
✅ **Масштабируемость** для множественных соединений
✅ **Мониторинг и алерты** для продакшена

Решение полностью готово к интеграции в существующую инфраструктуру MCP и может быть развернуто на основном домене без дополнительных микросервисов.
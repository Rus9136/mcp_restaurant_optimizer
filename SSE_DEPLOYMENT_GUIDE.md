# SSE Endpoint для MCP Restaurant Optimizer

## Обзор

Данный проект содержит полнофункциональный SSE (Server-Sent Events) endpoint для потоковой передачи данных ресторанной аналитики в реальном времени.

## Архитектура

### Основные компоненты:

1. **SSEService** (`app/services/sse_service.py`) - Основной сервис для генерации SSE потока
2. **SSE Endpoints** (`app/api/v1/sse_endpoints.py`) - FastAPI endpoint'ы для SSE
3. **Database Integration** (`app/services/database_integration.py`) - Интеграция с базой данных
4. **Nginx Configuration** (`nginx_sse_config.conf`) - Конфигурация nginx для SSE

## Установка и настройка

### 1. Зависимости

```bash
# Основные зависимости
pip install fastapi uvicorn[standard] httpx loguru

# Для интеграции с базой данных (выберите нужное)
pip install asyncpg                    # PostgreSQL
pip install sqlalchemy asyncpg        # SQLAlchemy + PostgreSQL
pip install motor                     # MongoDB

# Для кеширования
pip install redis aioredis
```

### 2. Переменные окружения

Добавьте в `.env` файл:

```env
# Основные настройки
ENVIRONMENT=production
DEBUG=False

# База данных (опционально)
DATABASE_URL=postgresql://user:password@localhost/mcp_restaurant
DATABASE_TYPE=postgresql
SSE_CACHE_TTL=30

# Безопасность
JWT_SECRET_KEY=your-secret-key
API_KEY_HEADER=X-API-Key
```

### 3. Настройка конфигурации

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = True
    
    # База данных
    database_url: str = None
    database_type: str = "postgresql"
    sse_cache_ttl: int = 30
    
    # Безопасность
    jwt_secret_key: str = "your-secret-key"
    api_key_header: str = "X-API-Key"
    
    class Config:
        env_file = ".env"
```

## Использование

### 1. Базовое подключение к SSE

```javascript
// Подключение к SSE потоку
const eventSource = new EventSource('https://mcp.madlen.space/api/v1/mcp/sse');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
    
    switch(data.type) {
        case 'sales':
            updateSalesChart(data.data);
            break;
        case 'bookings':
            updateBookingsTable(data.data);
            break;
        case 'occupancy':
            updateOccupancyMeter(data.data);
            break;
        case 'shifts':
            updateShiftsBoard(data.data);
            break;
    }
};

eventSource.onerror = function(error) {
    console.error('SSE error:', error);
};
```

### 2. Подключение с авторизацией

```javascript
// Для внешних запросов нужна авторизация
const eventSource = new EventSource('https://mcp.madlen.space/api/v1/mcp/sse', {
    headers: {
        'Authorization': 'Bearer your-jwt-token'
    }
});
```

### 3. Подключение с параметрами

```javascript
// Подключение с фильтрацией по подразделению
const eventSource = new EventSource(
    'https://mcp.madlen.space/api/v1/mcp/sse?department_id=4cb558ca-a8bc-4b81-871e-043f65218c50&interval=10'
);
```

## Интеграция с базой данных

### 1. PostgreSQL

```python
# Структура таблиц
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    department_id UUID NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    department_id UUID NOT NULL,
    booking_date DATE NOT NULL,
    booking_time TIME NOT NULL,
    party_size INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tables (
    id SERIAL PRIMARY KEY,
    department_id UUID NOT NULL,
    table_number INTEGER NOT NULL,
    seats INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'available'
);
```

### 2. Активация интеграции с БД

```python
# app/services/sse_service.py
sse_service = SSEService()

# Для перевода в продакшен режим
sse_service._demo_mode = False
```

## Настройка Nginx

### 1. Базовая конфигурация

```nginx
# /etc/nginx/sites-available/mcp.madlen.space
server {
    listen 80;
    listen 443 ssl http2;
    server_name mcp.madlen.space;
    
    # SSL настройки
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
    
    # SSE endpoint
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

### 2. Перезапуск nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Мониторинг и отладка

### 1. Проверка статуса SSE

```bash
# Статус сервиса
curl https://mcp.madlen.space/api/v1/mcp/sse/status

# Тестирование SSE потока
curl -H "Accept: text/event-stream" https://mcp.madlen.space/api/v1/mcp/sse
```

### 2. Логирование

```python
# Включение подробных логов
import logging
logging.basicConfig(level=logging.DEBUG)

# Или через loguru
from loguru import logger
logger.add("sse_debug.log", level="DEBUG")
```

### 3. Мониторинг активных соединений

```python
# Получение количества активных соединений
active_connections = sse_service.get_active_connections_count()
print(f"Active SSE connections: {active_connections}")
```

## Безопасность

### 1. Авторизация

```python
# Для внешних запросов требуется токен
headers = {
    'Authorization': 'Bearer your-jwt-token'
}

# Или API ключ
headers = {
    'X-API-Key': 'your-api-key'
}
```

### 2. Rate Limiting

```python
# Добавьте в sse_endpoints.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.get("/sse")
@limiter.limit("10/minute")
async def stream_restaurant_data(request: Request, ...):
    # ...
```

### 3. IP фильтрация

```python
# В validate_sse_access функции
ALLOWED_IPS = ["192.168.1.0/24", "10.0.0.0/8"]

def is_ip_allowed(ip: str) -> bool:
    # Проверка IP адреса
    return ip in ALLOWED_IPS
```

## Производительность

### 1. Кеширование

```python
# Используйте CachedDatabaseSSEProvider
from app.services.database_integration import CachedDatabaseSSEProvider

db_provider = CachedDatabaseSSEProvider(
    db_url="postgresql://...",
    cache_ttl=30  # секунды
)
```

### 2. Пулинг соединений

```python
# PostgreSQL
import asyncpg

async def create_pool():
    return await asyncpg.create_pool(
        database_url,
        min_size=5,
        max_size=20
    )
```

### 3. Мониторинг ресурсов

```bash
# Мониторинг памяти и CPU
htop

# Мониторинг сетевых соединений
ss -tuln | grep :8000

# Логи nginx
tail -f /var/log/nginx/mcp_access.log
```

## Примеры событий

### 1. Событие продаж

```json
{
    "type": "sales",
    "timestamp": "2025-07-11T10:00:00",
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

### 2. Событие бронирований

```json
{
    "type": "bookings",
    "timestamp": "2025-07-11T10:00:05",
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "data": {
        "total_bookings_today": 45,
        "confirmed_bookings": 40,
        "pending_bookings": 3,
        "cancelled_bookings": 2,
        "next_booking_time": "2025-07-11T12:30:00",
        "average_party_size": 3.2
    }
}
```

### 3. Событие загрузки

```json
{
    "type": "occupancy",
    "timestamp": "2025-07-11T10:00:10",
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

## Устранение неполадок

### 1. SSE не работает

```bash
# Проверить nginx конфигурацию
sudo nginx -t

# Проверить, что FastAPI работает
curl http://localhost:8000/health

# Проверить SSE локально
curl -H "Accept: text/event-stream" http://localhost:8000/api/v1/mcp/sse
```

### 2. Соединения разрываются

```nginx
# Увеличить таймауты в nginx
proxy_connect_timeout 600s;
proxy_send_timeout 600s;
proxy_read_timeout 600s;
```

### 3. Высокая нагрузка

```python
# Увеличить интервал между событиями
interval = 30  # секунды

# Использовать кеширование
cache_ttl = 60  # секунды

# Ограничить количество соединений
MAX_CONNECTIONS = 100
```

## Заключение

Данный SSE endpoint предоставляет полнофункциональную систему потоковой передачи данных для ресторанной аналитики. Он готов к использованию в продакшене с правильной настройкой безопасности, мониторинга и производительности.
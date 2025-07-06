# MCP Restaurant Optimizer

FastAPI сервер для предоставления ИИ доступа к данным для оптимизации графика сотрудников ресторана через MCP (Model Context Protocol) интерфейс.

## Описание

Сервер интегрируется с двумя внешними API:
- **aqniet.site** - для получения прогнозов продаж и аналитики
- **madlen.space** - для получения данных о ФОТ и информации о подразделениях

## Установка

1. Клонируйте репозиторий:
```bash
cd /root/projects/mcp_restaurant_optimizer
```

2. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения в файле `.env` (уже создан)

## Запуск

### Для разработки:
```bash
python run.py
```

### Для продакшена:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8003
```

Сервер запустится на http://localhost:8003

## API Документация

После запуска сервера документация доступна по адресам:
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

## Тестовые данные

Для тестирования API используйте следующий UUID подразделения:
- **department_id**: `4cb558ca-a8bc-4b81-871e-043f65218c50` (филиал "11мкр/MG")
- **Рекомендуемый период**: с `2025-07-01` по `2025-07-31`

## Эндпоинты

### 1. Прогноз продаж
```http
POST /api/v1/mcp/forecast
Content-Type: application/json

{
  "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
  "date_start": "2025-07-01",
  "date_end": "2025-07-31"
}
```

**Пример ответа:**
```json
{
  "data": [
    {
      "date": "2025-07-01",
      "predicted_sales": 297126.04
    },
    {
      "date": "2025-07-02",
      "predicted_sales": 325627.02
    }
    // ... остальные дни
  ]
}
```

### 2. Почасовые продажи
```http
POST /api/v1/mcp/hourly_sales
Content-Type: application/json

{
  "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
  "date_start": "2025-07-01",
  "date_end": "2025-07-03"
}
```

**Пример ответа:**
```json
{
  "data": [
    {
      "date": "2025-07-03",
      "hour": 9,
      "sales_amount": 6113.0
    },
    {
      "date": "2025-07-03",
      "hour": 10,
      "sales_amount": 12720.0
    }
    // ... остальные часы
  ]
}
```

### 3. План vs Факт
```http
POST /api/v1/mcp/plan_vs_fact
Content-Type: application/json

{
  "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
  "date_start": "2025-07-01",
  "date_end": "2025-07-05"
}
```

**Пример ответа:**
```json
{
  "data": [
    {
      "date": "2025-07-01",
      "predicted_sales": 297126.04,
      "actual_sales": 206780.0,
      "error": 90346.04,
      "error_percentage": 43.69
    }
    // ... остальные дни
  ]
}
```

### 4. ФОТ и график работы
```http
POST /api/v1/mcp/payroll
Content-Type: application/json

{
  "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
  "date_start": "2025-07-01",
  "date_end": "2025-07-05"
}
```

**Пример ответа:**
```json
{
  "success": true,
  "data": [
    {
      "employee_name": "Турдалиева Шахноза Даниярoвна",
      "payroll_total": 201721.0,
      "shifts": [
        {
          "date": "2025-07-01",
          "payroll_for_shift": 100860.5,
          "schedule_name": "09:00-22:00/11мкр 1 смена",
          "work_hours": 12.0
        }
      ]
    }
  ]
}
```

### 5. Информация о подразделении
```http
POST /api/v1/mcp/department_info
Content-Type: application/json

{
  "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"
}
```

**Пример ответа:**
```json
{
  "object_name": "11мкр/MG",
  "object_company": "ТОО Madlen Group",
  "hall_area": null,
  "kitchen_area": null,
  "seats_count": null
}
```

## Примеры использования

### Python (httpx)
```python
import httpx
import asyncio

async def get_forecast():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8003/api/v1/mcp/forecast",
            json={
                "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
                "date_start": "2025-07-01",
                "date_end": "2025-07-31"
            }
        )
        return response.json()

# Запуск
data = asyncio.run(get_forecast())
print(data)
```

### cURL
```bash
curl -X POST "http://localhost:8003/api/v1/mcp/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "date_start": "2025-07-01",
    "date_end": "2025-07-31"
  }'
```

## Формат ошибок

Все ошибки возвращаются в едином формате:
```json
{
  "error": {
    "type": "external_api_error",
    "message": "Ошибка при обращении к aqniet.site",
    "details": {
      "status_code": 500,
      "endpoint": "https://aqniet.site/api/forecast/batch",
      "timeout": false
    }
  }
}
```

## Кэширование

- Прогнозы, продажи и план/факт кэшируются на 30 минут
- Информация о подразделении кэшируется на 1 час
- ФОТ и графики НЕ кэшируются (всегда актуальные данные)

## Деплой

Для деплоя на VPS:

1. Установите зависимости системы:
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx
```

2. Настройте systemd сервис:
```bash
sudo nano /etc/systemd/system/mcp-restaurant.service
```

```ini
[Unit]
Description=MCP Restaurant Optimizer API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/projects/mcp_restaurant_optimizer
Environment="PATH=/root/projects/mcp_restaurant_optimizer/venv/bin"
ExecStart=/root/projects/mcp_restaurant_optimizer/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

3. Настройте Nginx:
```nginx
server {
    listen 80;
    server_name madlen.space www.madlen.space;
    
    location /api/v1/mcp {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. Запустите сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-restaurant
sudo systemctl start mcp-restaurant
sudo systemctl status mcp-restaurant
```

## Мониторинг

Просмотр логов:
```bash
sudo journalctl -u mcp-restaurant -f
```

## Безопасность

- API токен для aqniet.site хранится в переменных окружения
- В продакшене настройте CORS для конкретных доменов
- Используйте HTTPS через Nginx

## Лицензия

Proprietary
# Руководство по тестированию MCP Restaurant Optimizer

## Быстрый старт

1. Убедитесь, что сервер запущен на порту 8003:
```bash
./start_dev.sh
```

2. Запустите автоматические тесты:
```bash
./test_api.py
```

## Тестовые данные

### Основное подразделение для тестов
- **UUID**: `4cb558ca-a8bc-4b81-871e-043f65218c50`
- **Название**: "11мкр/MG"
- **Компания**: "ТОО Madlen Group"

### Рекомендуемые периоды
- **Полный месяц**: с `2025-07-01` по `2025-07-31`
- **Неделя**: с `2025-07-01` по `2025-07-07`
- **Несколько дней**: с `2025-07-01` по `2025-07-03`

## Примеры запросов для каждого эндпоинта

### 1. Прогноз продаж (кэшируется на 30 минут)

```bash
# Прогноз на месяц
curl -X POST "http://localhost:8003/api/v1/mcp/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "date_start": "2025-07-01",
    "date_end": "2025-07-31"
  }' | python3 -m json.tool

# Прогноз на неделю
curl -X POST "http://localhost:8003/api/v1/mcp/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "date_start": "2025-07-01",
    "date_end": "2025-07-07"
  }' | python3 -m json.tool
```

### 2. Почасовые продажи (кэшируется на 30 минут)

```bash
# Почасовые продажи за 3 дня
curl -X POST "http://localhost:8003/api/v1/mcp/hourly_sales" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "date_start": "2025-07-01",
    "date_end": "2025-07-03"
  }' | python3 -m json.tool
```

### 3. Сравнение план/факт (кэшируется на 30 минут)

```bash
# Анализ точности прогноза за неделю
curl -X POST "http://localhost:8003/api/v1/mcp/plan_vs_fact" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "date_start": "2025-07-01",
    "date_end": "2025-07-07"
  }' | python3 -m json.tool
```

### 4. ФОТ и графики (НЕ кэшируется)

```bash
# ФОТ за 5 дней
curl -X POST "http://localhost:8003/api/v1/mcp/payroll" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "date_start": "2025-07-01",
    "date_end": "2025-07-05"
  }' | python3 -m json.tool
```

### 5. Информация о подразделении (кэшируется на 1 час)

```bash
curl -X POST "http://localhost:8003/api/v1/mcp/department_info" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50"
  }' | python3 -m json.tool
```

## Тестирование ошибок

### Неверный UUID
```bash
curl -X POST "http://localhost:8003/api/v1/mcp/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "invalid-uuid",
    "date_start": "2025-07-01",
    "date_end": "2025-07-31"
  }' | python3 -m json.tool
```

### Неверный диапазон дат
```bash
curl -X POST "http://localhost:8003/api/v1/mcp/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "date_start": "2025-07-31",
    "date_end": "2025-07-01"
  }' | python3 -m json.tool
```

### Несуществующее подразделение
```bash
curl -X POST "http://localhost:8003/api/v1/mcp/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "00000000-0000-0000-0000-000000000000",
    "date_start": "2025-07-01",
    "date_end": "2025-07-31"
  }' | python3 -m json.tool
```

## Проверка кэширования

Чтобы проверить работу кэша:

1. Выполните запрос к любому кэшируемому эндпоинту
2. Запомните время выполнения
3. Повторите тот же запрос - он должен выполниться мгновенно
4. Проверьте логи сервера на наличие сообщений о cache hit/miss

## Полезные команды

### Просмотр логов в реальном времени
```bash
tail -f server_8003.log
```

### Проверка статуса сервера
```bash
curl http://localhost:8003/health
```

### Открыть Swagger документацию
```bash
open http://localhost:8003/docs  # macOS
xdg-open http://localhost:8003/docs  # Linux
```

## Интеграция с Postman

Вы можете импортировать следующую коллекцию в Postman:

```json
{
  "info": {
    "name": "MCP Restaurant Optimizer",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Forecast",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"department_id\": \"4cb558ca-a8bc-4b81-871e-043f65218c50\",\n  \"date_start\": \"2025-07-01\",\n  \"date_end\": \"2025-07-31\"\n}"
        },
        "url": {
          "raw": "http://localhost:8003/api/v1/mcp/forecast",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8003",
          "path": ["api", "v1", "mcp", "forecast"]
        }
      }
    }
  ]
}
```

## Метрики производительности

При тестировании обратите внимание на:

1. **Время ответа первого запроса** (без кэша):
   - Forecast: ~1-2 секунды
   - Hourly Sales: ~1-3 секунды (зависит от периода)
   - Plan vs Fact: ~1-2 секунды
   - Payroll: ~0.5-1 секунда
   - Department Info: ~0.3-0.5 секунды

2. **Время ответа повторного запроса** (из кэша):
   - Все кэшируемые эндпоинты: <50ms

## Отладка

### Включить подробные логи
Установите `DEBUG=True` в файле `.env` (уже установлено по умолчанию).

### Проверить версию API
```bash
curl http://localhost:8003/
```

### Проверить доступные эндпоинты
Откройте http://localhost:8003/docs в браузере для просмотра интерактивной документации.
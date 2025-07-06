# 🚀 Быстрый старт MCP Restaurant Optimizer

## Статус проекта: ✅ ГОТОВ К ИСПОЛЬЗОВАНИЮ

- **Сервер**: Запущен на http://localhost:8003
- **Документация**: http://localhost:8003/docs
- **Все эндпоинты**: Протестированы и работают
- **Кэширование**: Активно
- **Ошибки**: Обрабатываются корректно

## Тестовые данные

```json
{
  "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
  "date_start": "2025-07-01",
  "date_end": "2025-07-31"
}
```

## Быстрый тест

```bash
curl -X POST "http://localhost:8003/api/v1/mcp/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "date_start": "2025-07-01",
    "date_end": "2025-07-31"
  }'
```

## Доступные эндпоинты

1. **POST** `/api/v1/mcp/forecast` - Прогноз продаж ✅
2. **POST** `/api/v1/mcp/hourly_sales` - Почасовые продажи ✅  
3. **POST** `/api/v1/mcp/plan_vs_fact` - Сравнение план/факт ✅
4. **POST** `/api/v1/mcp/payroll` - ФОТ и графики ✅
5. **POST** `/api/v1/mcp/department_info` - Информация о подразделении ✅

## Для Deep Research API

Используйте URL: `http://madlen.space/api/v1/mcp/...` после деплоя на сервер.

## Команды

- **Запуск**: `./start_dev.sh`
- **Тестирование**: `./test_api.py`
- **Логи**: `tail -f server_8003.log`
- **Остановка**: `pkill -f "uvicorn app.main:app"`
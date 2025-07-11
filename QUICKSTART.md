# ⚡ MCP Restaurant Optimizer - Быстрый старт

## 🚀 Доступ к API

**Продакшн сервер**: https://mcp.madlen.space/

### Основные эндпоинты
- **Health Check**: `GET /health`
- **API Docs**: `GET /docs` 
- **OpenAPI**: `GET /openapi.json`
- **MCP API**: `POST /api/v1/*`

---

## 🧪 Быстрое тестирование

### 1. Health Check
```bash
curl https://mcp.madlen.space/health
# Ответ: {"status":"healthy","service":"mcp-restaurant-optimizer"}
```

### 2. Информация о сервисе
```bash
curl https://mcp.madlen.space/
# Ответ: {"service":"MCP Restaurant Optimizer","version":"1.0.0",...}
```

### 3. API документация
Откройте в браузере: https://mcp.madlen.space/docs

---

## 📱 Использование API

### Пример POST запроса (через curl)
```bash
curl -X POST "https://mcp.madlen.space/api/v1/mcp/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
    "date_start": "2025-07-01",
    "date_end": "2025-07-31"
  }'
```

### Пример POST запроса (Python)
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "https://mcp.madlen.space/api/v1/mcp/forecast",
        json={
            "department_id": "4cb558ca-a8bc-4b81-871e-043f65218c50",
            "date_start": "2025-07-01",
            "date_end": "2025-07-31"
        }
    )
    print(response.json())
```

---

## 🔧 Управление сервисом

### Systemd команды
```bash
# Статус
sudo systemctl status mcp-restaurant.service

# Перезапуск
sudo systemctl restart mcp-restaurant.service

# Логи
journalctl -u mcp-restaurant.service -f
```

### Nginx команды  
```bash
# Статус
docker ps | grep nginx

# Перезагрузка конфигурации
docker exec hr-nginx nginx -s reload

# Логи
docker logs hr-nginx
```

---

## 🚨 Troubleshooting

### Проблема: 502 Bad Gateway
```bash
# 1. Проверить сервис
systemctl status mcp-restaurant.service

# 2. Перезапустить
systemctl restart mcp-restaurant.service

# 3. Проверить
curl https://mcp.madlen.space/health
```

### Проблема: Медленный ответ
```bash
# Проверить прямое подключение
curl http://localhost:8003/health

# Проверить логи
journalctl -u mcp-restaurant.service --tail 20
```

---

## 📖 Дополнительная информация

- **[README.md](README.md)** - Полная документация
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Руководство по развертыванию
- **[test_api.py](test_api.py)** - Скрипт для тестирования API

---

**🎉 Готово! Система полностью настроена и готова к использованию.**
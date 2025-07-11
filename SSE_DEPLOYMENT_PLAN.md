# 🎯 План работ: Развертывание SSE endpoint на https://mcp.madlen.space

## 📋 Текущий статус

✅ **Завершено:**
- SSE endpoint полностью реализован и протестирован локально
- Все необходимые файлы созданы и готовы к деплою
- Документация и примеры использования подготовлены
- Git коммит создан с полным описанием изменений

❌ **Требует выполнения:**
- Развертывание на продакшн сервере https://mcp.madlen.space
- Интеграция с реальной базой данных
- Настройка nginx для SSE

---

## 🚀 План выполнения

### Этап 1: Развертывание кода на продакшн сервере

**Где выполнять:** На сервере где развернут https://mcp.madlen.space

#### 1.1 Обновление кода
```bash
# На продакшн сервере
cd /root/projects/mcp_restaurant_optimizer
git pull origin main
```

#### 1.2 Установка новых зависимостей
```bash
# Если есть новые зависимости в requirements.txt
pip install -r requirements.txt
```

#### 1.3 Перезапуск сервиса
```bash
# Перезапуск MCP сервиса
sudo systemctl restart mcp-restaurant.service

# Проверка статуса
sudo systemctl status mcp-restaurant.service
```

**Ожидаемый результат:** 
- Новый SSE endpoint доступен по адресу `/api/v1/mcp/sse`
- Можно проверить: `curl https://mcp.madlen.space/api/v1/mcp/sse/status`

---

### Этап 2: Настройка Nginx для SSE

**Где выполнять:** На продакшн сервере в конфигурации nginx

#### 2.1 Найти текущую конфигурацию nginx
```bash
# Поиск конфигурации для mcp.madlen.space
find /etc/nginx -name "*.conf" -exec grep -l "mcp.madlen.space" {} \;
# ИЛИ
docker exec hr-nginx cat /etc/nginx/nginx.conf | grep -A 20 "mcp.madlen.space"
```

#### 2.2 Добавить специальную локацию для SSE
Добавить в конфигурацию nginx:
```nginx
# Специальная конфигурация для SSE endpoint
location /api/v1/mcp/sse {
    proxy_pass http://127.0.0.1:8003;  # или актуальный порт MCP сервера
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Критические настройки для SSE
    proxy_buffering off;
    proxy_cache off;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    
    # Увеличенные таймауты для длительных соединений
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    
    # Заголовки для SSE
    add_header Cache-Control 'no-cache, no-store, must-revalidate';
    add_header Pragma 'no-cache';
    add_header Expires '0';
    add_header X-Accel-Buffering 'no';
    
    # CORS заголовки для SSE
    add_header Access-Control-Allow-Origin '*';
    add_header Access-Control-Allow-Methods 'GET, OPTIONS';
    add_header Access-Control-Allow-Headers 'Authorization, Content-Type, Cache-Control';
}
```

#### 2.3 Перезагрузить nginx
```bash
# Проверить конфигурацию
nginx -t
# ИЛИ для Docker
docker exec hr-nginx nginx -t

# Перезагрузить
nginx -s reload  
# ИЛИ для Docker
docker exec hr-nginx nginx -s reload
```

**Ожидаемый результат:**
- SSE endpoint работает через nginx без буферизации
- Длительные соединения не разрываются
- CORS заголовки правильно настроены

---

### Этап 3: Интеграция с реальной базой данных

**Где выполнять:** В коде приложения на продакшн сервере

#### 3.1 Настроить переменные окружения
Добавить в `.env` файл:
```env
# Database configuration
DATABASE_URL=postgresql://user:password@localhost/mcp_restaurant
DATABASE_TYPE=postgresql
SSE_CACHE_TTL=30

# Или для существующей базы
DATABASE_URL=postgresql://existing_user:password@db_host/existing_db
```

#### 3.2 Установить драйверы БД
```bash
# Для PostgreSQL
pip install asyncpg sqlalchemy[asyncio]

# Для MongoDB (если нужно)
pip install motor
```

#### 3.3 Активировать режим БД в коде
Изменить в `app/services/sse_service.py`:
```python
# Строка 40: изменить с True на False
self._demo_mode = False  # Переключить на реальные данные
```

#### 3.4 Создать таблицы БД (если нужны новые)
```sql
-- Выполнить SQL из файла database_integration.py
-- Или интегрировать с существующими таблицами
```

**Ожидаемый результат:**
- SSE endpoint получает данные из реальной БД
- Кеширование работает для снижения нагрузки
- Демо-данные больше не используются

---

### Этап 4: Тестирование и мониторинг

**Где выполнять:** С клиентских машин и на сервере

#### 4.1 Функциональное тестирование
```bash
# Проверка статуса
curl https://mcp.madlen.space/api/v1/mcp/sse/status

# Тест SSE потока
curl -H "Accept: text/event-stream" https://mcp.madlen.space/api/v1/mcp/sse

# Тест с параметрами  
curl -H "Accept: text/event-stream" \
  'https://mcp.madlen.space/api/v1/mcp/sse?department_id=4cb558ca-a8bc-4b81-871e-043f65218c50&interval=5'
```

#### 4.2 Тестирование в браузере
```javascript
// Открыть в браузере JavaScript консоль
const eventSource = new EventSource('https://mcp.madlen.space/api/v1/mcp/sse');
eventSource.onmessage = function(event) {
    console.log('SSE Event:', JSON.parse(event.data));
};
```

#### 4.3 Нагрузочное тестирование
```bash
# Использовать тестовый клиент
python test_sse_client.py
```

**Ожидаемый результат:**
- SSE endpoint отвечает с кодом 200
- События приходят каждые 3-5 секунд
- Данные корректно форматированы в JSON
- Соединения стабильны

---

### Этап 5: Настройка безопасности (опционально)

**Где выполнять:** В конфигурации приложения

#### 5.1 Добавить авторизацию (если нужна)
```python
# В sse_endpoints.py раскомментировать проверки токенов
```

#### 5.2 Настроить rate limiting
```bash
# Установить дополнительные зависимости
pip install slowapi
```

#### 5.3 Настроить IP фильтрацию
```python
# Настроить ALLOWED_IPS в sse_endpoints.py
```

---

## 📍 Ключевые файлы для изменения

### На продакшн сервере:
1. **`/root/projects/mcp_restaurant_optimizer/`** - основная директория проекта
2. **`.env`** - переменные окружения для БД
3. **Nginx конфигурация** - добавить SSE location
4. **`app/services/sse_service.py:40`** - переключить `_demo_mode = False`

### Конфигурационные файлы:
- **`nginx_sse_config.conf`** - готовая конфигурация nginx
- **`app/services/database_integration.py`** - примеры интеграции с БД
- **`PRODUCTION_SSE_SOLUTION.md`** - полная документация

---

## 🔍 Проверочные команды

### После каждого этапа:
```bash
# 1. Проверка сервиса
curl https://mcp.madlen.space/health

# 2. Проверка SSE статуса  
curl https://mcp.madlen.space/api/v1/mcp/sse/status

# 3. Проверка SSE потока
timeout 10 curl -H "Accept: text/event-stream" https://mcp.madlen.space/api/v1/mcp/sse

# 4. Проверка логов
journalctl -u mcp-restaurant.service --tail 20

# 5. Проверка nginx
docker logs hr-nginx --tail 20
```

---

## ⚠️ Возможные проблемы и решения

### Проблема: 502 Bad Gateway при обращении к /sse
**Решение:** Проверить, что MCP сервис запущен на правильном порту
```bash
systemctl status mcp-restaurant.service
netstat -tlnp | grep 8003  # или актуальный порт
```

### Проблема: SSE соединения разрываются
**Решение:** Убедиться, что nginx настроен с правильными заголовками для SSE

### Проблема: Данные не приходят из БД
**Решение:** Проверить переменные окружения и строки подключения к БД

### Проблема: CORS ошибки в браузере
**Решение:** Убедиться, что CORS заголовки настроены в nginx

---

## 🎯 Критерии успешного завершения

✅ **SSE endpoint доступен** по адресу https://mcp.madlen.space/api/v1/mcp/sse
✅ **Статус endpoint работает** и возвращает информацию о соединениях  
✅ **События приходят** в формате SSE каждые несколько секунд
✅ **Данные реальные** (из БД или внешних API, не демо)
✅ **CORS работает** - можно подключиться из браузера
✅ **Nginx оптимизирован** для SSE (без буферизации)
✅ **Мониторинг настроен** - логи и статус соединений

---

## 📞 Следующие шаги после завершения

1. **Документировать** финальную конфигурацию
2. **Создать мониторинг** для отслеживания SSE соединений
3. **Настроить алерты** при проблемах с SSE
4. **Оптимизировать производительность** при необходимости
5. **Интегрировать с Deep Research** для аналитических задач

---

**📝 План создан:** 2025-07-11  
**👤 Исполнитель:** DevOps/Backend разработчик  
**⏱️ Ожидаемое время:** 2-4 часа  
**🔧 Сложность:** Средняя
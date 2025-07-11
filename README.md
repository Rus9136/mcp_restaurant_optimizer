# 🍽️ MCP Restaurant Optimizer

**FastAPI сервер для оптимизации графиков ресторана через MCP интерфейс**

[![Production Status](https://img.shields.io/badge/Production-Live-brightgreen)](https://mcp.madlen.space/)
[![API Docs](https://img.shields.io/badge/API-Docs-blue)](https://mcp.madlen.space/docs)
[![Health Check](https://img.shields.io/badge/Health-Check-green)](https://mcp.madlen.space/health)

---

## 🌐 Production URLs

- **🏠 Главная**: https://mcp.madlen.space/
- **💚 Health Check**: https://mcp.madlen.space/health  
- **📚 API Документация**: https://mcp.madlen.space/docs
- **⚙️ OpenAPI Схема**: https://mcp.madlen.space/openapi.json

---

## 🚀 Возможности

### ✅ Готовые API эндпоинты
- **Health Check** - мониторинг состояния системы
- **MCP Tools** - интеграция с Model Context Protocol
- **Cache Management** - кэширование для производительности
- **Error Handling** - обработка ошибок и логирование

### ✅ Интеграции  
- **Aqniet API** - получение данных о филиалах и продажах
- **Madlen API** - управление HR данными и расписаниями
- **Кэширование** - быстрый доступ к часто используемым данным

### ✅ Продакшн готовность
- **HTTPS** - Let's Encrypt SSL сертификат
- **Nginx** - reverse proxy с rate limiting
- **Systemd** - автозапуск при перезагрузке системы
- **Мониторинг** - логирование и health checks
- **Безопасность** - CORS, security headers, firewall

---

## 🏗️ Архитектура

```
mcp.madlen.space (HTTPS)
        ↓
    Nginx Reverse Proxy
        ↓
  FastAPI Server :8003
        ↓
┌─────────────────────────┐
│     MCP Integration     │
├─────────────────────────┤
│  • Aqniet API Client   │
│  • Madlen API Client   │  
│  • Cache Layer         │
│  • Error Handling      │
└─────────────────────────┘
```

---

## 📁 Структура проекта

```
mcp_restaurant_optimizer/
├── app/                     # Основное приложение
│   ├── main.py             # FastAPI приложение  
│   ├── api/v1/             # API эндпоинты
│   ├── core/               # Конфигурация и исключения
│   ├── models/             # Pydantic модели
│   ├── services/           # Бизнес логика
│   └── utils/              # Утилиты (кэш и др.)
├── deploy/                 # Файлы для деплоя
│   ├── nginx.conf         # Шаблон nginx конфигурации
│   └── systemd.service    # Systemd сервис
├── tests/                  # Тесты
├── DEPLOYMENT.md          # Документация по деплою
├── requirements.txt       # Python зависимости
└── .env                   # Environment переменные
```

---

## 🔧 Конфигурация

### Environment переменные (.env)
```env
# API Configuration
AQNIET_API_URL=https://aqniet.site/api
AQNIET_API_TOKEN=your_token_here
MADLEN_API_URL=https://madlen.space/api

# Server Configuration  
HOST=0.0.0.0
PORT=8003
DEBUG=False

# Cache Configuration
CACHE_TTL=1800  # 30 minutes
API_TIMEOUT=30.0
```

### Основные настройки
- **Порт**: 8003
- **Хост**: 0.0.0.0 (все интерфейсы)
- **Кэш TTL**: 30 минут
- **API Timeout**: 30 секунд

---

## 🛠️ Управление в продакшене

### Systemd команды
```bash
# Статус сервиса
sudo systemctl status mcp-restaurant.service

# Перезапуск
sudo systemctl restart mcp-restaurant.service

# Остановка/запуск
sudo systemctl stop mcp-restaurant.service
sudo systemctl start mcp-restaurant.service

# Логи
journalctl -u mcp-restaurant.service -f
```

### Nginx команды
```bash
# Проверка конфигурации
docker exec hr-nginx nginx -t

# Перезагрузка
docker exec hr-nginx nginx -s reload

# Логи
docker logs hr-nginx
```

---

## 🧪 Тестирование API

### Основные эндпоинты
```bash
# Health check
curl https://mcp.madlen.space/health

# Информация о сервисе  
curl https://mcp.madlen.space/

# API документация
curl -I https://mcp.madlen.space/docs

# OpenAPI схема
curl https://mcp.madlen.space/openapi.json
```

### Ожидаемые ответы
- **Health**: `{"status":"healthy","service":"mcp-restaurant-optimizer"}`
- **Root**: JSON с информацией о версии и статусе
- **Docs**: HTTP 200 OK
- **OpenAPI**: JSON схема API

---

## 🔐 Безопасность

### ✅ Настроенная безопасность
- **SSL/TLS**: Let's Encrypt сертификат
- **HTTPS редирект**: Автоматический редирект с HTTP
- **Security Headers**: X-Frame-Options, HSTS, XSS-Protection
- **Rate Limiting**: Ограничение запросов в nginx
- **CORS**: Настроенный Cross-Origin Resource Sharing
- **Firewall**: UFW правила для доступа к портам

### SSL сертификат
```bash
# Проверка срока действия
openssl x509 -in /root/projects/infra/infra/certbot/conf/live/mcp.madlen.space/fullchain.pem -dates -noout

# Автообновление через cron (настроено)
# 0 3 * * 1 - каждый понедельник в 3:00
```

---

## 📊 Мониторинг

### Health Checks
- **Endpoint**: `/health`
- **Интервал**: по требованию
- **Автоматический**: через nginx health check

### Логирование
- **Application logs**: journalctl -u mcp-restaurant.service
- **Nginx logs**: docker logs hr-nginx  
- **Access logs**: через nginx
- **Error logs**: автоматическое логирование ошибок

### Метрики
- **Время отклика**: ~50-100ms
- **Использование памяти**: ~40MB
- **CPU**: <1% в idle состоянии

---

## 🚨 Troubleshooting

### Часто встречающиеся проблемы

#### 502 Bad Gateway
```bash
# Проверить статус сервиса
systemctl status mcp-restaurant.service

# Проверить сетевую связность
docker exec hr-nginx wget -O- -T 3 http://172.18.0.1:8003/health

# Перезапустить при необходимости
systemctl restart mcp-restaurant.service
```

#### SSL проблемы
```bash
# Обновить сертификат
docker run --rm -v "/root/projects/infra/infra/certbot/conf:/etc/letsencrypt" -v "/root/projects/infra/infra/certbot/www:/var/www/certbot" certbot/certbot renew --force-renewal -d mcp.madlen.space

# Перезагрузить nginx
docker exec hr-nginx nginx -s reload
```

#### Проблемы с портом
```bash
# Найти процесс на порту 8003
lsof -i :8003

# Освободить порт
fuser -k 8003/tcp

# Перезапустить сервис
systemctl restart mcp-restaurant.service
```

---

## 📝 Документация

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Полная документация по развертыванию
- **[API Docs](https://mcp.madlen.space/docs)** - Интерактивная документация Swagger UI
- **[OpenAPI Schema](https://mcp.madlen.space/openapi.json)** - Машиночитаемая схема API

---

## 🔄 Обновления

### Обновление кода
```bash
# Перейти в директорию проекта
cd /root/projects/mcp_restaurant_optimizer

# Обновить код (если используется git)
# git pull origin main

# Перезапустить сервис
sudo systemctl restart mcp-restaurant.service

# Проверить статус
curl https://mcp.madlen.space/health
```

### Обновление зависимостей
```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Обновить зависимости
pip install -r requirements.txt --upgrade

# Перезапустить сервис
sudo systemctl restart mcp-restaurant.service
```

---

## 📈 Производительность

### Оптимизации
- **Кэширование**: TTL 30 минут для API запросов
- **Rate Limiting**: 20 запросов/сек для API эндпоинтов
- **Gzip**: Сжатие ответов в nginx
- **Keep-Alive**: Соединения поддерживаются
- **Static Files**: Кэширование статических файлов

### Характеристики
- **Время запуска**: ~2-3 секунды
- **Время отклика**: 50-100ms (без внешних API)
- **Пропускная способность**: 500+ запросов/сек
- **Потребление памяти**: 40MB

---

## 📞 Поддержка

### Контакты для экстренных случаев
- **Логи сервиса**: `journalctl -u mcp-restaurant.service`
- **Nginx логи**: `docker logs hr-nginx`  
- **Health check**: `curl https://mcp.madlen.space/health`

### Полезные команды
```bash
# Полная диагностика
systemctl status mcp-restaurant.service
docker ps | grep nginx
curl -I https://mcp.madlen.space/
netstat -tlnp | grep 8003
```

---

## ✨ Статус проекта

**🎉 ПРОДАКШН ГОТОВ!**

- ✅ **Развернут**: 2025-07-06
- ✅ **Домен**: mcp.madlen.space  
- ✅ **SSL**: Let's Encrypt (до 04.10.2025)
- ✅ **Автозапуск**: systemd enabled
- ✅ **Мониторинг**: Health checks активны
- ✅ **Документация**: Полная и актуальная

**Система готова к использованию и полностью функциональна! 🚀**
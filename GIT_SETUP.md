# 🚀 Инструкции по отправке в Git репозиторий

## ✅ Подготовка завершена!

Git репозиторий инициализирован и готов к отправке в:
**https://github.com/Rus9136/mcp_restaurant_optimizer.git**

## 🔒 Безопасность

Все конфиденциальные данные защищены:
- ✅ `.env` файл исключен из Git
- ✅ `*.log` файлы исключены
- ✅ Создан `.env.example` шаблон
- ✅ Токены API не попадают в репозиторий

## 📤 Отправка в удаленный репозиторий

Выполните одну из команд для настройки аутентификации:

### Вариант 1: SSH (рекомендуется)
```bash
# Измените URL на SSH
git remote set-url origin git@github.com:Rus9136/mcp_restaurant_optimizer.git
git push -u origin main
```

### Вариант 2: HTTPS с токеном
```bash
# Используйте Personal Access Token вместо пароля
git push -u origin main
# Когда появится запрос, введите:
# Username: Rus9136
# Password: your_github_token
```

### Вариант 3: Настроить Git Credential Manager
```bash
git config --global credential.helper store
git push -u origin main
```

## 📋 Что уже сделано

- ✅ `git init` - инициализирован репозиторий
- ✅ `git add -A` - добавлены все файлы
- ✅ `git commit` - создан первый коммит
- ✅ `git remote add origin` - добавлен удаленный репозиторий
- ✅ `git branch -M main` - переименована ветка в main

## 📁 Файлы в репозитории

**Будут отправлены (30 файлов):**
- Весь код приложения (`app/`)
- Документация (`docs/`)
- Конфигурации деплоя (`deploy/`)
- Скрипты запуска и тестирования
- `.env.example` (шаблон без токенов)

**НЕ будут отправлены:**
- `.env` (содержит реальные токены)
- `*.log` файлы
- `venv/` (виртуальное окружение)
- `__pycache__/` (кэш Python)

## 🎯 После успешной отправки

1. Репозиторий будет доступен по адресу:
   https://github.com/Rus9136/mcp_restaurant_optimizer

2. Клонирование для других разработчиков:
   ```bash
   git clone https://github.com/Rus9136/mcp_restaurant_optimizer.git
   cd mcp_restaurant_optimizer
   cp .env.example .env
   # Отредактировать .env с реальными токенами
   ./start_dev.sh
   ```

## 🔄 Команды для обновления

После внесения изменений:
```bash
git add .
git commit -m "Описание изменений"
git push
```

## 🆘 Если возникли проблемы

1. **Проблемы с аутентификацией:**
   - Используйте SSH ключи или Personal Access Token
   - Не используйте пароль GitHub (устарело)

2. **Репозиторий не существует:**
   - Убедитесь, что репозиторий создан на GitHub
   - Проверьте права доступа

3. **Ошибки push:**
   ```bash
   git pull origin main --rebase
   git push
   ```
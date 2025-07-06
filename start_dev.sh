#!/bin/bash

# Скрипт для запуска сервера в режиме разработки

echo "🚀 Запуск MCP Restaurant Optimizer в режиме разработки..."

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Установка/обновление зависимостей
echo "📦 Установка зависимостей..."
pip install -r requirements.txt

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "Скопируйте .env.example в .env и настройте переменные окружения"
    exit 1
fi

# Запуск сервера
echo "✅ Запуск сервера на http://localhost:8003"
echo "📚 Документация доступна на http://localhost:8003/docs"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

python run.py
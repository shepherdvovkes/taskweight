#!/bin/bash

echo "🚀 Запуск TaskWeight Backend MVP..."

# Переходим в директорию сервера
cd server

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Устанавливаем зависимости
echo "📚 Установка зависимостей..."
pip install -r requirements.txt

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден!"
    echo "📝 Создайте файл .env на основе env.example"
    echo "🔑 Добавьте ваш OpenAI API ключ"
    exit 1
fi

# Запускаем сервер
echo "🌐 Запуск FastAPI сервера..."
echo "📍 Сервер будет доступен по адресу: http://localhost:8000"
echo "📖 API документация: http://localhost:8000/docs"
echo "🛑 Для остановки нажмите Ctrl+C"
echo ""

python -m app.main

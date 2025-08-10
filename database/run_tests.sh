#!/bin/bash

# TaskWeight Database Test Runner
# Скрипт для запуска тестов базы данных

set -e

echo "🚀 Запуск тестов базы данных TaskWeight..."
echo "=================================================="

# Проверяем, что Docker контейнеры запущены
echo "🔍 Проверка состояния контейнеров..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Контейнеры не запущены. Запускаем..."
    docker-compose up -d
    echo "⏳ Ждем готовности базы данных..."
    sleep 10
fi

# Проверяем здоровье PostgreSQL
echo "🔍 Проверка здоровья PostgreSQL..."
until docker exec taskweight_postgres pg_isready -U taskweight_user -d taskweight; do
    echo "⏳ PostgreSQL еще не готов..."
    sleep 2
done
echo "✅ PostgreSQL готов"

# Проверяем здоровье Redis
echo "🔍 Проверка здоровья Redis..."
until docker exec taskweight_redis redis-cli --raw incr ping > /dev/null 2>&1; do
    echo "⏳ Redis еще не готов..."
    sleep 2
done
echo "✅ Redis готов"

# Устанавливаем зависимости Python если нужно
if [ ! -d "venv" ]; then
    echo "🔧 Создание виртуального окружения Python..."
    python3 -m venv venv
fi

echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

echo "📦 Установка зависимостей..."
pip install -r requirements.txt

echo "🧪 Запуск тестов..."
python test_database.py

# Сохраняем код выхода
EXIT_CODE=$?

echo "=================================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "🎉 Тесты завершены успешно!"
else
    echo "❌ Тесты завершены с ошибками (код: $EXIT_CODE)"
fi

# Деактивируем виртуальное окружение
deactivate

exit $EXIT_CODE

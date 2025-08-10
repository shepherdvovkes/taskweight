#!/bin/bash

# TaskWeight Quick Database Check
# Быстрая проверка состояния базы данных

echo "🔍 Быстрая проверка базы данных TaskWeight..."

# Проверяем статус контейнеров
echo "📊 Статус контейнеров:"
docker-compose ps

echo -e "\n🔍 Проверка подключения к PostgreSQL..."
if docker exec taskweight_postgres psql -U taskweight_user -d taskweight -c "SELECT version();" > /dev/null 2>&1; then
    echo "✅ PostgreSQL доступен"
else
    echo "❌ PostgreSQL недоступен"
    exit 1
fi

echo -e "\n🔍 Проверка подключения к Redis..."
if docker exec taskweight_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis доступен"
else
    echo "❌ Redis недоступен"
    exit 1
fi

echo -e "\n🔍 Проверка таблиц..."
TABLE_COUNT=$(docker exec taskweight_postgres psql -U taskweight_user -d taskweight -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
echo "✅ Найдено таблиц: $TABLE_COUNT"

echo -e "\n🔍 Проверка тестовых данных..."
USER_COUNT=$(docker exec taskweight_postgres psql -U taskweight_user -d taskweight -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
PROJECT_COUNT=$(docker exec taskweight_postgres psql -U taskweight_user -d taskweight -t -c "SELECT COUNT(*) FROM projects;" | tr -d ' ')
TASK_COUNT=$(docker exec taskweight_postgres psql -U taskweight_user -d taskweight -t -c "SELECT COUNT(*) FROM tasks;" | tr -d ' ')

echo "✅ Пользователей: $USER_COUNT"
echo "✅ Проектов: $PROJECT_COUNT"
echo "✅ Задач: $TASK_COUNT"

echo -e "\n🎉 База данных работает корректно!"

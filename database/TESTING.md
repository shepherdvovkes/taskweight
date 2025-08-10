# TaskWeight Database Testing

Данный документ описывает процесс тестирования базы данных TaskWeight после развертывания.

## 🚀 Быстрый старт

### 1. Быстрая проверка
```bash
./quick_check.sh
```
Этот скрипт быстро проверяет:
- Статус Docker контейнеров
- Подключение к PostgreSQL и Redis
- Количество таблиц и тестовых данных

### 2. Полное тестирование
```bash
./run_tests.sh
```
Этот скрипт запускает полный набор тестов, включая:
- Структуру таблиц
- Расширения PostgreSQL
- Функции и представления
- Триггеры и индексы
- Целостность данных
- Производительность
- Redis операции

## 📋 Требования

- Docker и Docker Compose
- Python 3.7+
- Доступ к портам 5433 (PostgreSQL) и 6380 (Redis)

## 🔧 Установка зависимостей

```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

## 🧪 Запуск тестов вручную

```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем тесты
python test_database.py
```

## 📊 Что тестируется

### Структура базы данных
- ✅ Наличие всех необходимых таблиц (18 таблиц)
- ✅ Правильность схемы таблиц
- ✅ Наличие расширений PostgreSQL (uuid-ossp, pg_trgm, btree_gin)

### Функциональность
- ✅ Функции базы данных
- ✅ Представления (views)
- ✅ Триггеры для автоматического обновления
- ✅ Индексы для оптимизации

### Данные
- ✅ Наличие тестовых данных
- ✅ Целостность связей между таблицами
- ✅ Корректность внешних ключей

### Производительность
- ✅ Скорость выполнения запросов
- ✅ Работа с Redis
- ✅ Общая отзывчивость системы

## 🐳 Docker команды для диагностики

### Проверка статуса
```bash
docker-compose ps
```

### Логи PostgreSQL
```bash
docker logs taskweight_postgres
```

### Логи Redis
```bash
docker logs taskweight_redis
```

### Подключение к PostgreSQL
```bash
docker exec -it taskweight_postgres psql -U taskweight_user -d taskweight
```

### Подключение к Redis
```bash
docker exec -it taskweight_redis redis-cli
```

## 🔍 Ручная проверка таблиц

```sql
-- Список всех таблиц
\dt

-- Структура конкретной таблицы
\d users

-- Количество записей
SELECT COUNT(*) FROM users;

-- Проверка связей
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

## 📈 Интерпретация результатов

### 100% успех
🎉 База данных полностью готова к работе

### 80-99% успех
⚠️ Есть незначительные проблемы, но система работоспособна

### <80% успех
❌ Критические проблемы, требуется диагностика

## 🚨 Устранение неполадок

### Проблема: Контейнеры не запускаются
```bash
# Остановить все контейнеры
docker-compose down

# Удалить volumes (осторожно!)
docker-compose down -v

# Пересоздать и запустить
docker-compose up -d --build
```

### Проблема: База данных недоступна
```bash
# Проверить логи
docker logs taskweight_postgres

# Проверить порты
netstat -an | grep 5433

# Перезапустить PostgreSQL
docker restart taskweight_postgres
```

### Проблема: Redis недоступен
```bash
# Проверить логи
docker logs taskweight_redis

# Проверить порты
netstat -an | grep 6380

# Перезапустить Redis
docker restart taskweight_redis
```

## 📝 Логи тестирования

Все результаты тестов выводятся в консоль с подробной информацией о каждом тесте. Для автоматизации можно перенаправить вывод в файл:

```bash
./run_tests.sh > test_results.log 2>&1
```

## 🔄 Автоматизация

Для автоматического запуска тестов можно использовать cron:

```bash
# Добавить в crontab
0 */6 * * * cd /path/to/taskweight/database && ./run_tests.sh >> /var/log/taskweight_tests.log 2>&1
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи Docker контейнеров
2. Убедитесь, что порты не заняты другими сервисами
3. Проверьте права доступа к файлам
4. Убедитесь, что Docker имеет достаточно ресурсов

# TaskWeight Server

Серверная часть приложения TaskWeight для интеллектуальной оценки задач с использованием AI.

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.8+
- Docker и Docker Compose
- Git

### Установка и запуск

1. **Клонируйте репозиторий**
   ```bash
   git clone <repository-url>
   cd taskweight/server
   ```

2. **Создайте виртуальное окружение**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   venv\Scripts\activate     # Windows
   ```

3. **Установите зависимости**
   ```bash
   pip install -r requirements.txt
   ```

4. **Запустите базу данных**
   ```bash
   chmod +x scripts/*.sh
   ./scripts/start-db.sh
   ```

5. **Запустите сервер**
   ```bash
   ./scripts/start-server.sh
   ```

Сервер будет доступен по адресу: http://localhost:8000

## 🗄️ База данных

### Структура

Проект использует PostgreSQL с автоматическими миграциями через Alembic.

**Основные таблицы:**
- `users` - пользователи системы
- `projects` - проекты
- `tasks` - задачи
- `estimation_results` - результаты оценок
- `integrations` - интеграции с внешними сервисами
- `webhooks` - вебхуки для уведомлений

### Управление миграциями

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Описание изменений"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# Просмотреть историю
alembic history
```

### Доступ к базе данных

- **PostgreSQL**: localhost:5432
- **pgAdmin**: http://localhost:5050
  - Email: admin@taskweight.com
  - Password: admin

## 🔧 Разработка

### Структура проекта

```
server/
├── app/
│   ├── db/           # Модели и подключение к БД
│   ├── logic/        # Бизнес-логика
│   ├── models/       # Pydantic модели
│   └── main.py       # Основное приложение
├── alembic/          # Миграции БД
├── scripts/          # Скрипты для разработки
├── tests/            # Тесты
└── requirements.txt  # Зависимости
```

### Полезные команды

```bash
# Запуск тестов
pytest

# Проверка кода
flake8 app/
black app/

# Запуск только базы данных
./scripts/start-db.sh

# Остановка базы данных
./scripts/stop-db.sh

# Просмотр логов
docker-compose -f docker-compose.dev.yml logs -f
```

### Переменные окружения

Создайте файл `config.env` на основе `env.example`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4

# Database Configuration
DATABASE_URL=postgresql://taskweight_user:taskweight_password@localhost:5432/taskweight

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск тестов с покрытием
pytest --cov=app

# Запуск конкретного теста
pytest tests/test_api.py::test_estimate_task
```

## 📚 API Документация

После запуска сервера доступна автоматическая документация:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 Отладка

### Логи базы данных

```bash
docker-compose -f docker-compose.dev.yml logs postgres
```

### Логи Redis

```bash
docker-compose -f docker-compose.dev.yml logs redis
```

### Подключение к базе данных

```bash
docker exec -it taskweight_postgres_dev psql -U taskweight_user -d taskweight
```

## 🚀 Развертывание

### Продакшн

1. Обновите переменные окружения
2. Используйте production Docker Compose
3. Настройте SSL сертификаты
4. Настройте мониторинг

### Docker

```bash
# Сборка образа
docker build -t taskweight-server .

# Запуск
docker run -p 8000:8000 taskweight-server
```

## 🤝 Вклад в проект

1. Создайте feature branch
2. Внесите изменения
3. Добавьте тесты
4. Создайте Pull Request

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи
2. Убедитесь, что база данных запущена
3. Проверьте переменные окружения
4. Создайте issue в репозитории

# 🚀 TaskWeight Quick Start

## Быстрый запуск за 5 минут

### 1. Предварительные требования
- Docker и Docker Compose
- Python 3.8+

### 2. Запуск всего проекта
```bash
cd server
./start-dev.sh
```

### 3. Запуск только базы данных
```bash
cd server
./scripts/start-db.sh
```

### 4. Запуск сервера
```bash
cd server
./scripts/start-server.sh
```

## 📊 Доступные сервисы

После запуска будут доступны:
- **API Server**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379  
- **pgAdmin**: http://localhost:5050

## 🔑 Учетные данные

- **Database**: taskweight_user / taskweight_password
- **pgAdmin**: admin@taskweight.com / admin

## 📚 Полезные команды

```bash
# Просмотр всех команд
make help

# Проверка состояния
./scripts/health-check.sh

# Просмотр логов
docker-compose -f docker-compose.dev.yml logs -f

# Остановка базы
./scripts/stop-db.sh
```

## 🧪 Тестирование API

Откройте файл `examples/api-examples.http` в VS Code с расширением REST Client или используйте Swagger UI: http://localhost:8000/docs

## 🆘 Если что-то не работает

1. Проверьте, что Docker запущен
2. Запустите `./scripts/health-check.sh`
3. Проверьте логи: `docker-compose -f docker-compose.dev.yml logs -f`
4. Перезапустите: `./scripts/stop-db.sh && ./scripts/start-db.sh`

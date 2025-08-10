# TaskWeight Database

## Overview
База данных TaskWeight построена на PostgreSQL с Redis для кэширования. Система поддерживает управление проектами, задачами, пользователями и интеграции с внешними сервисами.

## Quick Start

### 1. Environment Setup
```bash
# Copy environment file
cp env.example .env

# Edit .env with your settings
nano .env
```

### 2. Start Database
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Run Migrations
```bash
# Run all migrations
./scripts/migrate.sh

# Or with sample data
LOAD_SAMPLE_DATA=true ./scripts/migrate.sh
```

### 4. Access Services
- **PostgreSQL**: localhost:5432
- **PgAdmin**: http://localhost:8080
- **Redis**: localhost:6379

## Database Structure

### Core Tables
- `users` - Пользователи системы
- `projects` - Проекты
- `tasks` - Задачи
- `task_categories` - Категории задач
- `estimation_results` - Результаты AI-оценок
- `integrations` - Интеграции с внешними сервисами
- `user_settings` - Настройки пользователей
- `audit_logs` - Логи изменений

### Advanced Features
- `webhooks` - Система вебхуков для интеграций
- `metrics` - Метрики и аналитика системы
- `notifications` - Система уведомлений
- `task_dependencies` - Зависимости между задачами
- `time_entries` - Учет времени по задачам
- `performance_metrics` - Метрики производительности
- `user_activity_logs` - Логи активности пользователей

### Views
- `task_details` - Детали задач
- `project_stats` - Статистика проектов
- `user_workload` - Нагрузка пользователей
- `estimation_analytics` - Аналитика оценок

### Functions
- `get_user_stats()` - Статистика пользователя
- `search_tasks()` - Поиск задач
- `get_project_timeline()` - Временная линия проекта
- `get_estimation_accuracy()` - Точность оценок

## Scripts

### Migration Script
```bash
./scripts/migrate.sh
```
Выполняет все миграции в правильном порядке.

### Backup Script
```bash
./scripts/backup.sh
```
Создает резервную копию базы данных.

### Restore Script
```bash
./scripts/restore.sh <backup_file>
```
Восстанавливает базу из резервной копии.

### Health Check
```bash
./scripts/health-check.sh
```
Проверяет состояние всех сервисов.

### Schema Verification
```bash
./scripts/verify-schema.sh
```
Проверяет целостность и полноту схемы базы данных.

## Configuration

### Environment Variables
- `POSTGRES_DB` - Имя базы данных
- `POSTGRES_USER` - Пользователь PostgreSQL
- `POSTGRES_PASSWORD` - Пароль PostgreSQL
- `POSTGRES_PORT` - Порт PostgreSQL
- `PGADMIN_EMAIL` - Email для PgAdmin
- `PGADMIN_PASSWORD` - Пароль для PgAdmin
- `REDIS_PASSWORD` - Пароль Redis

### Docker Compose
- **PostgreSQL**: Основная база данных
- **PgAdmin**: Веб-интерфейс для управления БД
- **Redis**: Кэширование и сессии

## Monitoring

### Prometheus & Grafana
```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### Health Checks
Все сервисы имеют встроенные health checks для мониторинга.

## Development

### Adding New Tables
1. Создайте SQL файл в `postgres/init/`
2. Добавьте таблицу в основной скрипт или создайте миграцию
3. Обновите документацию в `DATABASE_SCHEMA.md`

### Sample Data
Тестовые данные находятся в `03-sample-data.sql` и загружаются при `LOAD_SAMPLE_DATA=true`.

## Backup & Recovery

### Automatic Backups
Настроены автоматические резервные копии через cron (см. `backup/crontab`).

### Manual Backup
```bash
./scripts/backup.sh
```

### Restore
```bash
./scripts/restore.sh backup_20240101_120000.sql
```

## Troubleshooting

### Common Issues
1. **Port conflicts**: Измените порты в `.env`
2. **Permission errors**: Проверьте права на папки
3. **Connection refused**: Убедитесь, что Docker запущен

### Logs
```bash
# PostgreSQL logs
docker-compose logs postgres

# Redis logs
docker-compose logs redis

# PgAdmin logs
docker-compose logs pgadmin
```

## Security

### Best Practices
- Используйте сильные пароли
- Ограничьте доступ к базе данных
- Регулярно обновляйте образы Docker
- Включите SSL в продакшене

### Network Isolation
Все сервисы изолированы в сети `taskweight_network` с фиксированными IP адресами.

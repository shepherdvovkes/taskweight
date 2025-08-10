# TaskWeight Database Schema

## Overview
TaskWeight использует PostgreSQL в качестве основной базы данных с Redis для кэширования и сессий.

## Tables

### users
Основная таблица пользователей системы.
- `id` - UUID первичный ключ
- `username` - уникальное имя пользователя
- `email` - уникальный email
- `password_hash` - хеш пароля
- `created_at`, `updated_at` - временные метки

### projects
Проекты, над которыми работают пользователи.
- `id` - UUID первичный ключ
- `name` - название проекта
- `description` - описание проекта
- `owner_id` - ссылка на владельца (users.id)
- `created_at`, `updated_at` - временные метки

### tasks
Задачи в рамках проектов.
- `id` - UUID первичный ключ
- `title` - заголовок задачи
- `description` - описание задачи
- `project_id` - ссылка на проект
- `assignee_id` - ссылка на исполнителя
- `status` - статус задачи (todo, in_progress, completed)
- `priority` - приоритет (low, medium, high)
- `estimated_hours` - оценка в часах
- `actual_hours` - фактическое время выполнения
- `category_id` - ссылка на категорию
- `created_at`, `updated_at` - временные метки

### task_categories
Категории задач для лучшей организации.
- `id` - UUID первичный ключ
- `name` - название категории
- `description` - описание категории
- `color` - цвет для UI
- `project_id` - ссылка на проект
- `created_at`, `updated_at` - временные метки

### estimation_results
Результаты AI-оценок задач.
- `id` - UUID первичный ключ
- `card_id` - ID карточки из внешней системы
- `task_description` - описание задачи
- `repo_url` - ссылка на репозиторий
- `estimated_hours` - оценка в часах
- `actual_hours` - фактическое время
- `status` - статус оценки
- `error_message` - сообщение об ошибке
- `created_at`, `updated_at`, `completed_at` - временные метки

### integrations
Настройки интеграций с внешними сервисами.
- `id` - UUID первичный ключ
- `user_id` - ссылка на пользователя
- `service_type` - тип сервиса (trello, jira, github)
- `service_name` - название сервиса
- `api_key`, `api_secret` - ключи API
- `access_token`, `refresh_token` - токены доступа
- `webhook_url` - URL для webhook'ов
- `is_active` - активна ли интеграция
- `settings` - дополнительные настройки в JSON
- `created_at`, `updated_at` - временные метки

### user_settings
Персональные настройки пользователей.
- `id` - UUID первичный ключ
- `user_id` - ссылка на пользователя
- `timezone` - часовой пояс
- `language` - язык интерфейса
- `notification_email` - email уведомления
- `notification_push` - push уведомления
- `theme` - тема интерфейса
- `estimation_preferences` - настройки оценок в JSON
- `created_at`, `updated_at` - временные метки

### audit_logs
Логи изменений для аудита.
- `id` - UUID первичный ключ
- `user_id` - ссылка на пользователя
- `action` - действие (create, update, delete)
- `table_name` - название таблицы
- `record_id` - ID записи
- `old_values`, `new_values` - старые и новые значения в JSON
- `ip_address` - IP адрес
- `user_agent` - User Agent браузера
- `created_at` - временная метка

### webhooks
Система webhook'ов для внешних интеграций.
- `id` - UUID первичный ключ
- `name` - название webhook'а
- `url` - URL для отправки webhook'ов
- `events` - массив типов событий
- `integration_id` - ссылка на интеграцию
- `is_active` - активен ли webhook
- `secret_key` - секретный ключ для подписи
- `retry_count` - количество попыток повторной отправки
- `timeout_seconds` - таймаут в секундах
- `created_at`, `updated_at` - временные метки

### webhook_deliveries
Отслеживание попыток доставки webhook'ов.
- `id` - UUID первичный ключ
- `webhook_id` - ссылка на webhook
- `event_type` - тип события
- `payload` - данные события в JSON
- `response_status` - HTTP статус ответа
- `response_body` - тело ответа
- `error_message` - сообщение об ошибке
- `attempt_count` - количество попыток
- `next_retry_at` - время следующей попытки
- `delivered_at` - время успешной доставки
- `created_at` - временная метка

### metrics
Система сбора метрик.
- `id` - UUID первичный ключ
- `metric_name` - название метрики
- `metric_value` - значение метрики
- `metric_unit` - единица измерения
- `tags` - дополнительные теги в JSON
- `timestamp` - временная метка
- `source` - источник метрики

### performance_metrics
Метрики производительности задач.
- `id` - UUID первичный ключ
- `task_id` - ссылка на задачу
- `metric_type` - тип метрики
- `metric_value` - значение метрики
- `baseline_value` - базовое значение
- `improvement_percentage` - процент улучшения
- `measured_at` - время измерения
- `notes` - дополнительные заметки

### user_activity_logs
Логи активности пользователей.
- `id` - UUID первичный ключ
- `user_id` - ссылка на пользователя
- `activity_type` - тип активности
- `activity_data` - данные активности в JSON
- `ip_address` - IP адрес
- `user_agent` - User Agent браузера
- `session_id` - ID сессии
- `created_at` - временная метка

### estimation_accuracy_history
История точности оценок пользователей.
- `id` - UUID первичный ключ
- `user_id` - ссылка на пользователя
- `period_start`, `period_end` - период
- `total_estimations` - общее количество оценок
- `accurate_estimations` - точные оценки
- `overestimated_count` - переоцененные
- `underestimated_count` - недооцененные
- `average_accuracy_percentage` - средняя точность
- `improvement_trend` - тренд улучшения
- `created_at` - временная метка

### notification_templates
Шаблоны уведомлений.
- `id` - UUID первичный ключ
- `name` - название шаблона
- `type` - тип уведомления
- `subject` - тема (для email)
- `body_template` - шаблон тела
- `variables` - переменные шаблона в JSON
- `is_active` - активен ли шаблон
- `created_at`, `updated_at` - временные метки

### notifications
Уведомления пользователей.
- `id` - UUID первичный ключ
- `user_id` - ссылка на пользователя
- `template_id` - ссылка на шаблон
- `type` - тип уведомления
- `title` - заголовок
- `message` - сообщение
- `data` - дополнительные данные в JSON
- `priority` - приоритет
- `status` - статус доставки
- `scheduled_at` - запланированное время
- `sent_at`, `delivered_at`, `read_at` - временные метки
- `error_message` - сообщение об ошибке
- `retry_count`, `max_retries` - счетчики попыток
- `created_at`, `updated_at` - временные метки

### notification_preferences
Настройки уведомлений пользователей.
- `id` - UUID первичный ключ
- `user_id` - ссылка на пользователя
- `email_enabled`, `push_enabled`, `in_app_enabled`, `webhook_enabled` - включенные типы
- `quiet_hours_start`, `quiet_hours_end` - тихие часы
- `timezone` - часовой пояс
- `categories` - настройки категорий в JSON
- `created_at`, `updated_at` - временные метки

### notification_logs
Логи доставки уведомлений.
- `id` - UUID первичный ключ
- `notification_id` - ссылка на уведомление
- `attempt_number` - номер попытки
- `delivery_method` - метод доставки
- `status` - статус доставки
- `response_data` - данные ответа в JSON
- `error_message` - сообщение об ошибке
- `attempted_at` - время попытки

### task_dependencies
Зависимости между задачами.
- `id` - UUID первичный ключ
- `dependent_task_id` - зависимая задача
- `prerequisite_task_id` - предварительная задача
- `dependency_type` - тип зависимости
- `created_at` - временная метка

### time_entries
Записи времени работы над задачами.
- `id` - UUID первичный ключ
- `task_id` - ссылка на задачу
- `user_id` - ссылка на пользователя
- `start_time`, `end_time` - время начала и окончания
- `duration_minutes` - продолжительность в минутах
- `description` - описание работы
- `is_billable` - оплачиваемое время
- `created_at`, `updated_at` - временные метки

## Views

### task_details
Детальная информация о задачах с данными проекта и исполнителя.

### project_stats
Статистика по проектам (количество задач, время).

### user_workload
Нагрузка пользователей (количество назначенных задач).

### estimation_analytics
Аналитика по оценкам задач.

## Functions

### get_user_stats(user_uuid)
Возвращает статистику пользователя.

### search_tasks(search_term)
Поиск задач по тексту.

### get_project_timeline(project_uuid)
Возвращает временную линию проекта.

### get_estimation_accuracy()
Рассчитывает точность оценок.

### record_metric(metric_name, metric_value, metric_unit, tags, source)
Записывает новую метрику.

### get_metrics(metric_name, start_time, end_time, aggregation)
Получает метрики за период с агрегацией.

### calculate_user_performance_score(user_id, period_days)
Рассчитывает оценку производительности пользователя.

### get_system_health_metrics()
Получает метрики здоровья системы.

### create_notification(user_id, template_name, type, data, priority, scheduled_at)
Создает новое уведомление.

### get_pending_notifications(user_id, limit)
Получает ожидающие уведомления пользователя.

### mark_notification_sent(notification_id, delivery_method, response_data)
Отмечает уведомление как отправленное.

### mark_notification_failed(notification_id, delivery_method, error_message, response_data)
Отмечает уведомление как неудачное.

### get_notification_stats(user_id, days)
Получает статистику уведомлений пользователя.

### register_webhook_delivery(webhook_id, event_type, payload)
Регистрирует доставку webhook'а.

### get_pending_webhook_deliveries()
Получает ожидающие webhook'и для доставки.

### mark_webhook_delivered(delivery_id, response_status, response_body)
Отмечает webhook как доставленный.

### mark_webhook_failed(delivery_id, error_message, next_retry_at)
Отмечает webhook как неудачный.

### calculate_task_duration(task_id)
Рассчитывает продолжительность задачи на основе записей времени.

## Indexes
Созданы индексы для оптимизации запросов по:
- Email и username пользователей
- ID проектов и исполнителей
- Статусам задач
- ID карточек оценок
- Типам интеграций
- Webhook'ам и их статусам
- Метрикам и времени
- Уведомлениям и их статусам
- Зависимостям задач
- Записям времени

## Triggers
Автоматическое обновление поля `updated_at` при изменении записей во всех таблицах.

## Extensions
- `uuid-ossp` - для генерации UUID
- `pg_trgm` - для триграммного поиска
- `btree_gin` - для GIN индексов

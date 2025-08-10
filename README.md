# TaskWeight - Интеллектуальная система оценки задач

TaskWeight - это AI-система для оценки сложности и времени выполнения задач, интегрированная с популярными таск-трекерами (Trello, Jira).

## 🚀 Возможности

- **AI-оценка задач**: Автоматическая оценка времени выполнения с использованием OpenAI GPT
- **Интеграция с Trello**: Power-Up плагин для seamless работы
- **Контур обратной связи**: Пост-анализ завершенных задач для улучшения точности
- **Статистика по разработчикам**: Отслеживание точности оценок

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Trello/Jira   │    │  TaskWeight     │    │    OpenAI      │
│   Плагины       │◄──►│  Backend API    │◄──►│     API        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Структура проекта

```
taskweight/
├── server/                 # Backend сервер (FastAPI)
│   ├── app/
│   │   ├── logic/         # Бизнес-логика и AI
│   │   ├── db/            # Хранилище данных
│   │   ├── models/        # Pydantic модели
│   │   └── main.py        # FastAPI приложение
│   ├── requirements.txt    # Python зависимости
│   ├── env.example        # Пример переменных окружения
│   └── Dockerfile         # Docker контейнер
├── plugins/                # Frontend плагины
│   ├── trello/            # Trello Power-Up
│   │   ├── index.html     # Основной интерфейс
│   │   ├── connector.html # Trello интеграция
│   │   ├── script.js      # JavaScript логика
│   │   └── style.css      # Стили
│   └── jira/              # Jira плагин (будущее)
└── README.md
```

## 🛠️ Установка и запуск

### Этап 1: Backend MVP

#### Предварительные требования
- Python 3.10+
- OpenAI API ключ

#### Установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd taskweight
```

2. **Настройте переменные окружения:**
```bash
cd server
cp env.example .env
# Отредактируйте .env файл, добавив ваш OpenAI API ключ
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Запустите сервер:**
```bash
python -m app.main
```

Сервер будет доступен по адресу: http://localhost:8000

#### Проверка работоспособности

- **API документация**: http://localhost:8000/docs
- **Корневой эндпоинт**: http://localhost:8000/
- **Отладка**: http://localhost:8000/api/v1/debug/estimations

### Этап 2: Trello Plugin MVP

#### Локальное тестирование

1. **Запустите локальный сервер** (см. Этап 1)

2. **Откройте плагин в браузере:**
```
file:///path/to/taskweight/plugins/trello/index.html
```

3. **Протестируйте функциональность:**
   - Введите GitHub URL репозитория
   - Опишите задачу
   - Нажмите "Оценить задачу"
   - Дождитесь результата от AI

#### Интеграция с Trello

1. **Создайте Power-Up в Trello:**
   - Перейдите в [Trello Power-Ups](https://trello.com/power-ups/admin)
   - Создайте новый Power-Up
   - Укажите URL к `connector.html`

2. **Настройте домены:**
   - Добавьте ваш домен в список разрешенных
   - Убедитесь, что CORS настроен правильно

## 🔧 API Endpoints

### POST /api/v1/estimate
Запускает оценку задачи.

**Request:**
```json
{
  "cardId": "trello_card_id",
  "taskDescription": "Описание задачи",
  "repoUrl": "https://github.com/user/repo"
}
```

**Response:**
```json
{
  "status": "processing",
  "message": "Оценка задачи запущена",
  "cardId": "trello_card_id"
}
```

### GET /api/v1/estimate/{card_id}
Получает статус оценки.

**Response:**
```json
{
  "id": "estimation_id",
  "cardId": "trello_card_id",
  "status": "estimated",
  "estimatedHours": 8.5,
  "createdAt": "2025-01-10T12:00:00Z"
}
```

### POST /api/v1/webhooks/trello
Webhook для получения уведомлений от Trello.

## 🎯 Пользовательские сценарии

### Сценарий 1: Первоначальная оценка
1. Создайте карточку в Trello
2. Добавьте ссылку на GitHub репозиторий в описание
3. Нажмите кнопку "Оценить задачу"
4. Дождитесь результата от AI
5. Получите прогноз времени выполнения

### Сценарий 2: Завершение задачи (будущее)
1. Перед перемещением в "Done" добавьте комментарии:
   - Ссылку на финальный PR/коммит
   - Реальное затраченное время в формате `time: 8.5h`
2. Переместите карточку в "Done"
3. Система автоматически проведет пост-анализ
4. Бейдж обновится, показывая прогноз и факт

## 🐳 Docker

Для запуска в Docker:

```bash
cd server
docker build -t taskweight .
docker run -p 8000:8000 --env-file .env taskweight
```

## 🔮 Планы развития

- [ ] **Этап 3**: Интеграция с PostgreSQL + SQLAlchemy
- [ ] **Этап 4**: Реализация контура обратной связи
- [ ] **Этап 5**: Jira плагин
- [ ] **Этап 6**: Расширенная аналитика и метрики
- [ ] **Этап 7**: Машинное обучение для улучшения точности

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

MIT License

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**TaskWeight v1.0** - Умная оценка задач для умных команд! 🚀

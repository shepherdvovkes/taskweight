# 🚀 Быстрый старт TaskWeight

## ⚡ За 5 минут к работающему AI-оценщику задач!

### 1️⃣ Клонирование и настройка
```bash
git clone <your-repo>
cd taskweight
```

### 2️⃣ Настройка OpenAI API
```bash
cd server
cp env.example .env
# Отредактируйте .env, добавив ваш OpenAI API ключ
```

### 3️⃣ Запуск Backend
```bash
# Способ 1: Автоматический скрипт
./start.sh

# Способ 2: Ручной запуск
cd server
python3 -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
python -m app.main
```

### 4️⃣ Тестирование API
- **Сервер**: http://localhost:8000
- **Документация**: http://localhost:8000/docs
- **Отладка**: http://localhost:8000/api/v1/debug/estimations

### 5️⃣ Тестирование плагина
Откройте в браузере: `plugins/trello/demo.html`

## 🧪 Тестовый запрос
```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "cardId": "test123",
    "taskDescription": "Создать REST API",
    "repoUrl": "https://github.com/user/repo"
  }'
```

## ✅ Готово!
Теперь у вас есть:
- ✅ Работающий FastAPI сервер
- ✅ AI-оценщик задач с OpenAI
- ✅ In-memory хранилище данных
- ✅ Trello плагин (демо версия)
- ✅ Полная API документация

## 🔮 Следующие шаги
1. **Этап 3**: Интеграция с PostgreSQL
2. **Этап 4**: Контур обратной связи
3. **Этап 5**: Jira плагин

---

**Вопросы?** Смотрите [README.md](README.md) или создавайте Issues!

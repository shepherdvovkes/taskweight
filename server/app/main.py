import os
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .models.estimation import EstimationRequest, EstimationResponse, EstimationResult
from .models.webhook import TrelloWebhook
from .db.storage import InMemoryStorage
from .logic.ai_estimator import AIEstimator

# Загружаем переменные окружения
load_dotenv()

app = FastAPI(
    title="TaskWeight API",
    description="Интеллектуальная система оценки задач с использованием AI",
    version="1.0.0"
)

# Настройка CORS для плагинов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить доменами плагинов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация хранилища и AI оценщика
storage = InMemoryStorage()
ai_estimator = AIEstimator(storage)

@app.get("/")
async def root():
    """Корневой эндпоинт для проверки работоспособности"""
    return {
        "message": "TaskWeight API работает!",
        "version": "1.0.0",
        "status": "active"
    }

@app.post("/api/v1/estimate", response_model=EstimationResponse)
async def estimate_task(
    request: EstimationRequest,
    background_tasks: BackgroundTasks
):
    """
    Запускает оценку задачи в фоновом режиме
    """
    try:
        # Создаем запись в хранилище
        estimation = storage.create_estimation(request.cardId)
        
        # Запускаем оценку в фоновом режиме
        background_tasks.add_task(
            ai_estimator.estimate_task,
            request.cardId,
            request.taskDescription,
            request.repoUrl
        )
        
        return EstimationResponse(
            status="processing",
            message="Оценка задачи запущена",
            cardId=request.cardId
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/estimate/{card_id}", response_model=EstimationResult)
async def get_estimation(card_id: str):
    """
    Получает текущий статус и результаты оценки по ID карточки
    """
    estimation = storage.get_estimation_by_card_id(card_id)
    if not estimation:
        raise HTTPException(status_code=404, detail="Оценка не найдена")
    
    return estimation

@app.post("/api/v1/webhooks/trello")
async def trello_webhook(webhook: TrelloWebhook):
    """
    Обрабатывает webhook'и от Trello
    """
    try:
        # Пока что просто логируем webhook
        print(f"Получен webhook от Trello: {webhook.action.get('type', 'unknown')}")
        
        # TODO: В будущем здесь будет логика обработки завершения задач
        
        return {"status": "ok", "message": "Webhook обработан"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/debug/estimations")
async def debug_estimations():
    """
    Отладочный эндпоинт для просмотра всех оценок
    """
    return {
        "total": len(storage.get_all_estimations()),
        "estimations": storage.get_all_estimations()
    }

if __name__ == "__main__":
    import uvicorn
    
    # Проверяем наличие API ключа OpenAI
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  ВНИМАНИЕ: OPENAI_API_KEY не установлен!")
        print("   Создайте файл .env и добавьте ваш API ключ OpenAI")
    
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )

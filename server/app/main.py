import os
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime

from .models.estimation import (
    EstimationRequest, EstimationResponse, EstimationResult, 
    EstimationInsights, EstimationFeedback, EstimationHistory,
    BatchEstimationRequest, BatchEstimationResponse, UserPerformanceUpdate,
    UserPerformanceStats, ProjectStats, EstimationStatus, TrelloEstimationRequest
)
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
        "status": "active",
        "features": [
            "AI-оценка задач",
            "Batch estimation",
            "User performance tracking",
            "Project statistics",
            "Детальная аналитика",
            "История оценок",
            "Обратная связь",
            "Инсайты и рекомендации"
        ]
    }

@app.get("/health")
async def health_check():
    """Проверка состояния сервера"""
    return {
        "status": "healthy",
        "timestamp": "2025-01-10T12:00:00Z",
        "services": {
            "api": "running",
            "storage": "running",
            "ai_estimator": "available"
        }
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
        estimation = storage.create_estimation(
            request.cardId,
            user_id=getattr(request, 'userId', None),
            team_id=getattr(request, 'teamId', None),
            project_id=getattr(request, 'projectId', None)
        )
        
        # Запускаем оценку в фоновом режиме
        background_tasks.add_task(
            ai_estimator.estimate_task,
            request.cardId,
            request.taskDescription,
            request.repoUrl,
            request.priority,
            request.complexity,
            getattr(request, 'userId', None),
            getattr(request, 'teamId', None),
            getattr(request, 'projectId', None)
        )
        
        return EstimationResponse(
            status="processing",
            message="Оценка задачи запущена",
            cardId=request.cardId
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/estimate/batch", response_model=BatchEstimationResponse)
async def estimate_batch_tasks(
    request: BatchEstimationRequest,
    background_tasks: BackgroundTasks
):
    """
    Запускает batch estimation для множества задач
    """
    try:
        # Запускаем batch estimation в фоновом режиме
        background_tasks.add_task(
            ai_estimator.estimate_batch_tasks,
            request
        )
        
        # Создаем batch response
        batch = storage.create_batch_estimation(
            request.tasks,
            request.userId,
            request.teamId,
            request.projectId
        )
        
        return batch
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/estimate/batch/{batch_id}", response_model=BatchEstimationResponse)
async def get_batch_status(batch_id: str):
    """
    Получает статус batch estimation
    """
    try:
        batch = storage.get_batch_status(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch estimation не найден")
        return batch
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при получении статуса batch {batch_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении статуса batch")

@app.get("/api/v1/trello/batch/{batch_id}/status")
async def get_trello_batch_status(batch_id: str):
    """
    Получает детальный статус batch оценки Trello карточек
    """
    try:
        batch = storage.get_batch_status(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch estimation не найден")
        
        # Получаем детальную информацию о каждой карточке в batch
        card_details = []
        for task in batch.tasks if hasattr(batch, 'tasks') else []:
            card_id = task.get('card_id') if isinstance(task, dict) else str(task)
            if card_id:
                estimation = storage.get_estimation_by_card_id(card_id)
                if estimation:
                    card_details.append({
                        "cardId": card_id,
                        "status": estimation.status,
                        "estimatedHours": estimation.estimatedHours,
                        "confidence": estimation.confidence,
                        "error": estimation.error_message if hasattr(estimation, 'error_message') else None
                    })
        
        return {
            "batchId": batch_id,
            "status": batch.status,
            "totalTasks": batch.totalTasks,
            "completedTasks": batch.completedTasks,
            "failedTasks": batch.failedTasks,
            "processingTasks": batch.processingTasks,
            "cardDetails": card_details,
            "createdAt": batch.createdAt,
            "lastUpdated": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при получении статуса Trello batch {batch_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении статуса batch")
    """
    Получает статус batch estimation
    """
    try:
        batch = storage.get_batch_status(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch estimation не найден")
        return batch
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/estimate/{card_id}/performance")
async def update_user_performance(
    card_id: str,
    performance_update: UserPerformanceUpdate
):
    """
    Обновляет производительность пользователя и улучшает будущие оценки
    """
    try:
        # Получаем estimation по card_id
        estimation = storage.get_estimation_by_card_id(card_id)
        if not estimation:
            raise HTTPException(status_code=404, detail="Оценка не найдена")
        
        # Обновляем performance_update с правильным estimation_id
        performance_update.estimationId = estimation.id
        
        # Обновляем производительность
        updated_estimation = await ai_estimator.update_user_performance(performance_update)
        
        return {
            "message": "Производительность пользователя обновлена",
            "estimation": updated_estimation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/users/{user_id}/performance", response_model=UserPerformanceStats)
async def get_user_performance_stats(user_id: str):
    """
    Получает статистику производительности пользователя
    """
    try:
        stats = storage.get_user_performance_stats(user_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/users/{user_id}/estimations")
async def get_user_estimations(user_id: str):
    """
    Получает все оценки пользователя
    """
    try:
        estimations = storage.get_estimations_by_user(user_id)
        return {
            "userId": user_id,
            "totalEstimations": len(estimations),
            "estimations": estimations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(project_id: str):
    """
    Получает статистику проекта
    """
    try:
        stats = storage.get_project_stats(project_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/projects/{project_id}/estimations")
async def get_project_estimations(project_id: str):
    """
    Получает все оценки проекта
    """
    try:
        estimations = storage.get_estimations_by_project(project_id)
        return {
            "projectId": project_id,
            "totalEstimations": len(estimations),
            "estimations": estimations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/teams/{team_id}/estimations")
async def get_team_estimations(team_id: str):
    """
    Получает все оценки команды
    """
    try:
        estimations = storage.get_estimations_by_team(team_id)
        return {
            "teamId": team_id,
            "totalEstimations": len(estimations),
            "estimations": estimations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/estimate/{card_id}", response_model=EstimationResult)
async def get_estimation(card_id: str):
    """
    Получает текущий статус и результаты оценки по ID карточки
    """
    try:
        estimation = storage.get_estimation_by_card_id(card_id)
        if not estimation:
            raise HTTPException(status_code=404, detail="Оценка не найдена")
        return estimation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/estimate/{card_id}/history", response_model=EstimationHistory)
async def get_estimation_history(card_id: str):
    """
    Получает историю оценок для карточки
    """
    try:
        history = storage.get_estimation_history(card_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/estimate/{card_id}/insights", response_model=EstimationInsights)
async def get_estimation_insights(card_id: str):
    """
    Получает AI инсайты и рекомендации для оценки
    """
    try:
        estimation = storage.get_estimation_by_card_id(card_id)
        if not estimation:
            raise HTTPException(status_code=404, detail="Оценка не найдена")
        
        insights = ai_estimator.get_estimation_insights(estimation)
        
        return EstimationInsights(
            accuracyScore=insights['accuracy_score'],
            complexityLevel=insights['complexity_level'],
            riskFactors=insights['risk_factors'],
            recommendations=insights['recommendations']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/estimate/{card_id}/feedback")
async def submit_feedback(card_id: str, feedback: EstimationFeedback):
    """
    Отправляет обратную связь по оценке
    """
    try:
        # Получаем estimation по card_id
        estimation = storage.get_estimation_by_card_id(card_id)
        if not estimation:
            raise HTTPException(status_code=404, detail="Оценка не найдена")
        
        # Обновляем feedback с правильным estimation_id
        feedback.estimationId = estimation.id
        
        # Добавляем feedback
        added_feedback = storage.add_feedback(feedback)
        
        return {
            "message": "Обратная связь добавлена",
            "feedback": added_feedback
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/estimate/{card_id}/refine")
async def refine_estimation(card_id: str, feedback: EstimationFeedback):
    """
    Улучшает оценку на основе обратной связи
    """
    try:
        # Получаем estimation по card_id
        estimation = storage.get_estimation_by_card_id(card_id)
        if not estimation:
            raise HTTPException(status_code=404, detail="Оценка не найдена")
        
        # Обновляем feedback с правильным estimation_id
        feedback.estimationId = estimation.id
        
        # Улучшаем оценку
        refined_estimation = await ai_estimator.refine_estimation(
            estimation.id, feedback.feedback
        )
        
        return {
            "message": "Оценка улучшена на основе обратной связи",
            "estimation": refined_estimation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/estimate/{card_id}/statistics")
async def get_estimation_statistics(card_id: str):
    """
    Получает статистику точности и распределения оценок
    """
    try:
        # Получаем статистику точности
        accuracy_stats = storage.get_accuracy_statistics(card_id)
        
        # Получаем распределение по сложности
        complexity_dist = storage.get_complexity_distribution(card_id)
        
        # Получаем распределение по приоритету
        priority_dist = storage.get_priority_distribution(card_id)
        
        return {
            "cardId": card_id,
            "accuracy": accuracy_stats,
            "complexityDistribution": complexity_dist,
            "priorityDistribution": priority_dist
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/webhooks/trello")
async def trello_webhook(webhook: TrelloWebhook):
    """
    Обрабатывает webhook'и от Trello
    """
    try:
        # TODO: Реализовать обработку webhook'ов
        return {
            "message": "Webhook получен",
            "action": webhook.action.type,
            "cardId": webhook.action.data.card.id if webhook.action.data.card else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/trello/card/{card_id}/stats")
async def get_trello_card_stats(card_id: str):
    """
    Получает детальную статистику по карточке Trello
    """
    try:
        # Получаем основную оценку
        estimation = storage.get_estimation_by_card_id(card_id)
        if not estimation:
            raise HTTPException(status_code=404, detail="Оценка не найдена")
        
        # Получаем историю
        history = storage.get_estimation_history(card_id)
        
        # Получаем статистику точности
        accuracy_stats = storage.get_accuracy_statistics(card_id)
        
        # Получаем распределения
        complexity_dist = storage.get_complexity_distribution(card_id)
        priority_dist = storage.get_priority_distribution(card_id)
        
        # Получаем feedback
        feedback_list = storage.get_feedback_for_estimation(estimation.id)
        
        return {
            "cardId": card_id,
            "estimation": estimation,
            "history": history,
            "accuracy": accuracy_stats,
            "complexityDistribution": complexity_dist,
            "priorityDistribution": priority_dist,
            "feedback": feedback_list,
            "lastUpdated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/trello/card/{card_id}/estimate")
async def estimate_trello_card(
    card_id: str, 
    request: TrelloEstimationRequest,
    background_tasks: BackgroundTasks
):
    """
    Запускает оценку Trello карточки с использованием AI
    """
    try:
        # Валидация входных данных
        if not request.task_description:
            raise HTTPException(status_code=400, detail="Описание задачи обязательно")
        
        if not request.repo_url:
            raise HTTPException(status_code=400, detail="URL репозитория обязателен")
        
        # Валидация приоритета и сложности
        valid_priorities = ["low", "medium", "high", "critical"]
        valid_complexities = ["simple", "medium", "complex", "very_complex"]
        
        if request.priority not in valid_priorities:
            raise HTTPException(status_code=400, detail=f"Неверный приоритет. Допустимые значения: {', '.join(valid_priorities)}")
        
        if request.complexity not in valid_complexities:
            raise HTTPException(status_code=400, detail=f"Неверная сложность. Допустимые значения: {', '.join(valid_complexities)}")
        
        # Создаем запись в хранилище
        estimation = storage.create_estimation(
            card_id,
            user_id=request.user_id,
            team_id=request.team_id,
            project_id=request.project_id
        )
        
        # Запускаем оценку в фоновом режиме
        background_tasks.add_task(
            ai_estimator.estimate_trello_task,
            card_id,
            request.trello_card_data.dict() if request.trello_card_data else {},
            request.repo_url,
            request.priority,
            request.complexity,
            request.user_id,
            request.team_id,
            request.project_id
        )
        
        return {
            "status": "processing",
            "message": "Оценка Trello карточки запущена",
            "cardId": card_id,
            "estimationId": estimation.id,
            "estimatedCompletionTime": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при оценке Trello карточки {card_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при оценке карточки")

@app.post("/api/v1/trello/card/{card_id}/reestimate")
async def reestimate_trello_card(card_id: str, reason: str = "Запрос пользователя"):
    """
    Переоценивает Trello карточку
    """
    try:
        result = await ai_estimator.reestimate_trello_task(card_id, reason)
        return {
            "message": "Переоценка запущена",
            "cardId": card_id,
            "estimation": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/trello/card/{card_id}/metadata")
async def update_trello_card_metadata(card_id: str, metadata: dict):
    """
    Обновляет метаданные карточки Trello
    """
    try:
        estimation = storage.get_estimation_by_card_id(card_id)
        if not estimation:
            raise HTTPException(status_code=404, detail="Оценка не найдена")
        
        # Обновляем метаданные
        updated_estimation = storage.update_estimation(
            estimation.id,
            metadata={**estimation.metadata, **metadata}
        )
        
        return {
            "message": "Метаданные обновлены",
            "cardId": card_id,
            "metadata": updated_estimation.metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/trello/card/{card_id}/details")
async def get_trello_card_details(card_id: str):
    """
    Получает детальную информацию о Trello карточке с оценкой
    """
    try:
        # Получаем основную оценку
        estimation = storage.get_estimation_by_card_id(card_id)
        if not estimation:
            raise HTTPException(status_code=404, detail="Оценка не найдена")
        
        # Получаем историю оценок
        history = storage.get_estimation_history(card_id)
        
        # Получаем статистику точности
        accuracy_stats = storage.get_accuracy_statistics(card_id)
        
        # Получаем распределения
        complexity_dist = storage.get_complexity_distribution(card_id)
        priority_dist = storage.get_priority_distribution(card_id)
        
        # Получаем feedback
        feedback_list = storage.get_feedback_for_estimation(estimation.id)
        
        # Получаем метаданные карточки
        card_metadata = estimation.metadata or {}
        
        return {
            "cardId": card_id,
            "estimation": estimation,
            "history": history,
            "accuracy": accuracy_stats,
            "complexityDistribution": complexity_dist,
            "priorityDistribution": priority_dist,
            "feedback": feedback_list,
            "cardMetadata": card_metadata,
            "lastUpdated": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при получении деталей карточки {card_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении деталей карточки")

@app.get("/api/v1/trello/board/{board_id}/stats")
async def get_trello_board_stats(board_id: str):
    """
    Получает статистику по доске Trello
    """
    try:
        # Получаем все оценки для доски (по project_id)
        estimations = storage.get_estimations_by_project(board_id)
        
        if not estimations:
            return {
                "boardId": board_id,
                "totalCards": 0,
                "totalEstimatedHours": 0,
                "averageAccuracy": 0,
                "complexityBreakdown": {},
                "priorityBreakdown": {},
                "recentEstimations": []
            }
        
        # Вычисляем статистику
        total_hours = sum(est.estimatedHours or 0 for est in estimations)
        completed_estimations = [est for est in estimations if est.status == EstimationStatus.COMPLETED]
        
        # Разбивка по сложности
        complexity_breakdown = {}
        for est in estimations:
            if est.metadata and 'complexity' in est.metadata:
                complexity = est.metadata['complexity']
                complexity_breakdown[complexity] = complexity_breakdown.get(complexity, 0) + 1
        
        # Разбивка по приоритету
        priority_breakdown = {}
        for est in estimations:
            if est.metadata and 'priority' in est.metadata:
                priority = est.metadata['priority']
                priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1
        
        # Последние оценки
        recent_estimations = sorted(
            estimations, 
            key=lambda x: x.createdAt, 
            reverse=True
        )[:10]
        
        return {
            "boardId": board_id,
            "totalCards": len(estimations),
            "totalEstimatedHours": round(total_hours, 2),
            "averageAccuracy": round(
                sum(est.confidence or 0 for est in estimations) / len(estimations), 2
            ) if estimations else 0,
            "complexityBreakdown": complexity_breakdown,
            "priorityBreakdown": priority_breakdown,
            "recentEstimations": recent_estimations,
            "lastUpdated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/trello/board/{board_id}/estimate-batch")
async def estimate_board_cards_batch(
    board_id: str,
    request: dict,
    background_tasks: BackgroundTasks
):
    """
    Запускает массовую оценку всех карточек на доске Trello
    """
    try:
        # Валидация входных данных
        if not request.get('card_ids'):
            raise HTTPException(status_code=400, detail="Список ID карточек обязателен")
        
        if not request.get('repo_url'):
            raise HTTPException(status_code=400, detail="URL репозитория обязателен")
        
        card_ids = request['card_ids']
        repo_url = request['repo_url']
        priority = request.get('priority', 'medium')
        complexity = request.get('complexity', 'medium')
        user_id = request.get('user_id')
        team_id = request.get('team_id')
        
        # Валидация приоритета и сложности
        valid_priorities = ["low", "medium", "high", "critical"]
        valid_complexities = ["simple", "medium", "complex", "very_complex"]
        
        if priority not in valid_priorities:
            raise HTTPException(status_code=400, detail=f"Неверный приоритет. Допустимые значения: {', '.join(valid_priorities)}")
        
        if complexity not in valid_complexities:
            raise HTTPException(status_code=400, detail=f"Неверная сложность. Допустимые значения: {', '.join(valid_complexities)}")
        
        # Создаем batch estimation
        batch = storage.create_batch_estimation(
            [{"card_id": cid} for cid in card_ids],
            user_id,
            team_id,
            board_id
        )
        
        # Запускаем оценку каждой карточки в фоновом режиме
        for card_id in card_ids:
            background_tasks.add_task(
                ai_estimator.estimate_trello_task,
                card_id,
                {},  # Пустые данные карточки для batch оценки
                repo_url,
                priority,
                complexity,
                user_id,
                team_id,
                board_id
            )
        
        return {
            "status": "processing",
            "message": f"Массовая оценка {len(card_ids)} карточек запущена",
            "boardId": board_id,
            "batchId": batch.batchId,
            "totalCards": len(card_ids),
            "estimatedCompletionTime": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при массовой оценке карточек доски {board_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при массовой оценке")

@app.post("/api/v1/trello/webhook/process")
async def process_trello_webhook(webhook_data: dict):
    """
    Обрабатывает webhook от Trello и обновляет соответствующие данные
    """
    try:
        action = webhook_data.get('action', {})
        action_type = action.get('type')
        card_data = action.get('data', {}).get('card', {})
        card_id = card_data.get('id')
        
        if not card_id:
            return {"message": "Webhook получен, но ID карточки не найден"}
        
        # Обрабатываем различные типы действий
        if action_type == 'updateCard':
            # Карточка обновлена
            await _handle_card_update(card_id, card_data)
        elif action_type == 'addAttachmentToCard':
            # Добавлено вложение
            await _handle_attachment_added(card_id, action.get('data', {}))
        elif action_type == 'commentCard':
            # Добавлен комментарий
            await _handle_comment_added(card_id, action.get('data', {}))
        
        return {
            "message": "Webhook обработан",
            "actionType": action_type,
            "cardId": card_id,
            "processed": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _handle_card_update(card_id: str, card_data: dict):
    """Обрабатывает обновление карточки"""
    # Обновляем метаданные если есть оценка
    estimation = storage.get_estimation_by_card_id(card_id)
    if estimation:
        metadata = estimation.metadata or {}
        metadata['last_trello_update'] = datetime.now().isoformat()
        metadata['trello_data'] = {
            'name': card_data.get('name'),
            'desc': card_data.get('desc'),
            'labels': card_data.get('labels', []),
            'due': card_data.get('due')
        }
        
        storage.update_estimation(estimation.id, metadata=metadata)

async def _handle_attachment_added(card_id: str, data: dict):
    """Обрабатывает добавление вложения"""
    attachment = data.get('attachment', {})
    if attachment.get('url') and 'github.com' in attachment.get('url', ''):
        # GitHub вложение - возможно, стоит переоценить задачу
        estimation = storage.get_estimation_by_card_id(card_id)
        if estimation:
            metadata = estimation.metadata or {}
            metadata['github_attachments'] = metadata.get('github_attachments', [])
            metadata['github_attachments'].append({
                'url': attachment.get('url'),
                'name': attachment.get('name'),
                'added_at': datetime.now().isoformat()
            })
            
            storage.update_estimation(estimation.id, metadata=metadata)

async def _handle_comment_added(card_id: str, data: dict):
    """Обрабатывает добавление комментария"""
    comment = data.get('text', '')
    if comment and any(keyword in comment.lower() for keyword in ['estimate', 'оценка', 'время', 'часы']):
        # Комментарий связан с оценкой
        estimation = storage.get_estimation_by_card_id(card_id)
        if estimation:
            metadata = estimation.metadata or {}
            metadata['estimation_comments'] = metadata.get('estimation_comments', [])
            metadata['estimation_comments'].append({
                'text': comment,
                'added_at': datetime.now().isoformat()
            })
            
            storage.update_estimation(estimation.id, metadata=metadata)

# Debug endpoints
@app.get("/api/v1/debug/estimations")
async def debug_estimations():
    """
    Получает все оценки для отладки
    """
    try:
        estimations = storage.get_all_estimations()
        return {
            "total": len(estimations),
            "estimations": estimations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/debug/cleanup")
async def cleanup_old_estimations(days_old: int = 90):
    """
    Очищает старые оценки
    """
    try:
        cleaned_count = storage.cleanup_old_estimations(days_old)
        return {
            "message": f"Очищено {cleaned_count} старых оценок",
            "cleanedCount": cleaned_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from ..models.estimation import (
    EstimationResult, EstimationStatus, EstimationInsights, EstimationFeedback, 
    EstimationHistory, UserPerformanceUpdate, UserPerformanceStats, ProjectStats,
    BatchEstimationResponse
)
from .models import (
    User, Project, Task, EstimationResult as DBEstimationResult,
    Integration, EstimationFeedback as DBEstimationFeedback,
    BatchEstimation, Webhook, Metric
)

class PostgreSQLStorage:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_estimation(self, card_id: str, user_id: Optional[str] = None, 
                               team_id: Optional[str] = None, project_id: Optional[str] = None,
                               batch_id: Optional[str] = None) -> EstimationResult:
        """Создает новую запись оценки в PostgreSQL"""
        try:
            # Сначала создаем запись в таблице tasks
            task = Task(
                id=uuid.uuid4(),
                title=f"Task for card {card_id}",
                description="Task created for estimation",
                status="pending",
                priority="medium",
                project_id=uuid.UUID(project_id) if project_id else None,
                assignee_id=uuid.UUID(user_id) if user_id else None
            )
            
            self.session.add(task)
            await self.session.flush()  # Получаем ID задачи
            
            # Создаем запись в базе данных
            db_estimation = DBEstimationResult(
                task_id=task.id,  # Используем ID созданной задачи
                estimated_hours=0,  # Обязательное поле
                status="processing",
                user_id=uuid.UUID(user_id) if user_id else None,
                team_id=team_id,
                project_id=project_id,
                batch_id=batch_id,
                task_metadata={"card_id": card_id}  # Сохраняем card_id в metadata
            )
            
            self.session.add(db_estimation)
            await self.session.commit()
            await self.session.refresh(db_estimation)
            
            # Создаем или обновляем историю
            await self._update_history(card_id, db_estimation)
            
            # Обновляем статистику пользователя
            if user_id:
                await self._update_user_performance(user_id, db_estimation)
            
            # Обновляем статистику проекта
            if project_id:
                await self._update_project_stats(project_id, db_estimation)
            
            # Конвертируем в модель ответа
            return self._convert_db_to_response(db_estimation)
            
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Ошибка создания оценки: {e}")
    
    async def create_batch_estimation(self, tasks: List, user_id: Optional[str] = None,
                                     team_id: Optional[str] = None, project_id: Optional[str] = None) -> BatchEstimationResponse:
        """Создает batch estimation для множества задач"""
        try:
            batch_id = str(uuid.uuid4())
            batch = BatchEstimation(
                batch_id=batch_id,
                total_tasks=len(tasks),
                processing_tasks=len(tasks),
                completed_tasks=0,
                failed_tasks=0,
                status="processing",
                user_id=uuid.UUID(user_id) if user_id else None,
                team_id=team_id,
                project_id=project_id
            )
            
            self.session.add(batch)
            await self.session.commit()
            await self.session.refresh(batch)
            
            return BatchEstimationResponse(
                batchId=batch_id,
                totalTasks=len(tasks),
                processingTasks=len(tasks),
                completedTasks=0,
                failedTasks=0,
                status="processing",
                createdAt=batch.created_at
            )
            
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Ошибка создания batch estimation: {e}")
    
    async def update_batch_status(self, batch_id: str, completed: int = 0, failed: int = 0):
        """Обновляет статус batch estimation"""
        try:
            stmt = select(BatchEstimation).where(BatchEstimation.batch_id == batch_id)
            result = await self.session.execute(stmt)
            batch = result.scalar_one_or_none()
            
            if batch:
                batch.completed_tasks += completed
                batch.failed_tasks += failed
                batch.processing_tasks = batch.total_tasks - batch.completed_tasks - batch.failed_tasks
                
                if batch.processing_tasks == 0:
                    batch.status = "completed" if batch.failed_tasks == 0 else "completed_with_errors"
                
                await self.session.commit()
                
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Ошибка обновления batch статуса: {e}")
    
    async def get_batch_status(self, batch_id: str) -> Optional[BatchEstimationResponse]:
        """Получает статус batch estimation"""
        try:
            stmt = select(BatchEstimation).where(BatchEstimation.batch_id == batch_id)
            result = await self.session.execute(stmt)
            batch = result.scalar_one_or_none()
            
            if batch:
                return BatchEstimationResponse(
                    batchId=batch.batch_id,
                    totalTasks=batch.total_tasks,
                    processingTasks=batch.processing_tasks,
                    completedTasks=batch.completed_tasks,
                    failedTasks=batch.failed_tasks,
                    status=batch.status,
                    createdAt=batch.created_at
                )
            return None
            
        except Exception as e:
            raise Exception(f"Ошибка получения batch статуса: {e}")
    
    async def update_user_performance(self, estimation_id: str, actual_hours: float, 
                                     user_id: str, notes: Optional[str] = None,
                                     difficulty: Optional[int] = None, blockers: Optional[List[str]] = None):
        """Обновляет производительность пользователя на основе фактического времени"""
        try:
            # Получаем оценку
            estimation = await self.get_estimation(estimation_id)
            if not estimation:
                return None
            
            # Обновляем оценку
            await self.update_estimation(
                estimation_id,
                actual_hours=actual_hours,
                completed_at=datetime.now(),
                status="completed"
            )
            
            # Обновляем статистику пользователя
            await self._update_user_performance_stats(user_id, estimation, actual_hours)
            
            # Обновляем статистику проекта
            if estimation.projectId:
                await self._update_project_completion_stats(estimation.projectId, estimation, actual_hours)
            
            return await self.get_estimation(estimation_id)
            
        except Exception as e:
            raise Exception(f"Ошибка обновления производительности: {e}")
    
    async def get_user_performance_stats(self, user_id: str) -> UserPerformanceStats:
        """Получает статистику производительности пользователя"""
        try:
            # Получаем все оценки пользователя
            stmt = select(DBEstimationResult).where(DBEstimationResult.user_id == uuid.UUID(user_id))
            result = await self.session.execute(stmt)
            estimations = result.scalars().all()
            
            total_tasks = len(estimations)
            completed_tasks = len([e for e in estimations if e.status == "completed"])
            
            # Вычисляем среднюю точность
            completed_with_actual = [e for e in estimations if e.status == "completed" and e.actual_hours and e.estimated_hours]
            if completed_with_actual:
                accuracies = []
                for est in completed_with_actual:
                    accuracy = min(est.estimated_hours / est.actual_hours, est.actual_hours / est.estimated_hours)
                    accuracies.append(accuracy * 100)
                average_accuracy = sum(accuracies) / len(accuracies)
            else:
                average_accuracy = 0.0
            
            # Вычисляем bias
            if completed_with_actual:
                biases = [est.estimated_hours - est.actual_hours for est in completed_with_actual]
                estimation_bias = sum(biases) / len(biases)
            else:
                estimation_bias = 0.0
            
            # Анализируем предпочтения по сложности
            complexity_preference = {}
            for est in estimations:
                if est.task_metadata and 'complexity' in est.task_metadata:
                    complexity = est.task_metadata['complexity']
                    complexity_preference[complexity] = complexity_preference.get(complexity, 0) + 1
            
            return UserPerformanceStats(
                userId=user_id,
                totalTasks=total_tasks,
                completedTasks=completed_tasks,
                averageAccuracy=round(average_accuracy, 2),
                estimationBias=round(estimation_bias, 2),
                complexityPreference=complexity_preference,
                lastUpdated=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Ошибка получения статистики пользователя: {e}")
    
    async def get_project_stats(self, project_id: str) -> ProjectStats:
        """Получает статистику проекта"""
        try:
            # Получаем все оценки проекта
            stmt = select(DBEstimationResult).where(DBEstimationResult.project_id == project_id)
            result = await self.session.execute(stmt)
            estimations = result.scalars().all()
            
            total_tasks = len(estimations)
            completed_tasks = len([e for e in estimations if e.status == "completed"])
            
            total_estimated_hours = sum(e.estimated_hours or 0 for e in estimations)
            total_actual_hours = sum(e.actual_hours or 0 for e in estimations)
            
            # Вычисляем среднюю точность
            completed_with_actual = [e for e in estimations if e.status == "completed" and e.actual_hours and e.estimated_hours]
            if completed_with_actual:
                accuracies = []
                for est in completed_with_actual:
                    accuracy = min(est.estimated_hours / est.actual_hours, est.actual_hours / est.estimated_hours)
                    accuracies.append(accuracy * 100)
                average_accuracy = sum(accuracies) / len(accuracies)
            else:
                average_accuracy = 0.0
            
            # Вычисляем эффективность
            efficiency = total_estimated_hours / total_actual_hours if total_actual_hours > 0 else 0.0
            
            return ProjectStats(
                projectId=project_id,
                totalTasks=total_tasks,
                completedTasks=completed_tasks,
                averageAccuracy=round(average_accuracy, 2),
                totalEstimatedHours=round(total_estimated_hours, 2),
                totalActualHours=round(total_actual_hours, 2),
                efficiency=round(efficiency, 2),
                lastUpdated=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Ошибка получения статистики проекта: {e}")
    
    async def get_estimations_by_user(self, user_id: str) -> List[EstimationResult]:
        """Получает все оценки пользователя"""
        try:
            stmt = select(DBEstimationResult).where(DBEstimationResult.user_id == uuid.UUID(user_id))
            result = await self.session.execute(stmt)
            db_estimations = result.scalars().all()
            
            return [self._convert_db_to_response(est) for est in db_estimations]
            
        except Exception as e:
            raise Exception(f"Ошибка получения оценок пользователя: {e}")
    
    async def get_estimations_by_project(self, project_id: str) -> List[EstimationResult]:
        """Получает все оценки проекта"""
        try:
            stmt = select(DBEstimationResult).where(DBEstimationResult.project_id == project_id)
            result = await self.session.execute(stmt)
            db_estimations = result.scalars().all()
            
            return [self._convert_db_to_response(est) for est in db_estimations]
            
        except Exception as e:
            raise Exception(f"Ошибка получения оценок проекта: {e}")
    
    async def get_estimations_by_team(self, team_id: str) -> List[EstimationResult]:
        """Получает все оценки команды"""
        try:
            stmt = select(DBEstimationResult).where(DBEstimationResult.team_id == team_id)
            result = await self.session.execute(stmt)
            db_estimations = result.scalars().all()
            
            return [self._convert_db_to_response(est) for est in db_estimations]
            
        except Exception as e:
            raise Exception(f"Ошибка получения оценок команды: {e}")
    
    async def get_estimation_by_card_id(self, card_id: str) -> Optional[EstimationResult]:
        """Получает оценку по ID карточки Trello"""
        try:
            stmt = select(DBEstimationResult).where(DBEstimationResult.card_id == card_id)
            result = await self.session.execute(stmt)
            db_estimation = result.scalar_one_or_none()
            
            if db_estimation:
                return self._convert_db_to_response(db_estimation)
            return None
            
        except Exception as e:
            raise Exception(f"Ошибка получения оценки по card_id: {e}")
    
    async def get_estimation(self, estimation_id: str) -> Optional[EstimationResult]:
        """Получает оценку по ID"""
        try:
            stmt = select(DBEstimationResult).where(DBEstimationResult.id == uuid.UUID(estimation_id))
            result = await self.session.execute(stmt)
            db_estimation = result.scalar_one_or_none()
            
            if db_estimation:
                return self._convert_db_to_response(db_estimation)
            return None
            
        except Exception as e:
            raise Exception(f"Ошибка получения оценки: {e}")
    
    async def update_estimation(self, estimation_id: str, **kwargs) -> Optional[EstimationResult]:
        """Обновляет оценку"""
        try:
            stmt = select(DBEstimationResult).where(DBEstimationResult.id == uuid.UUID(estimation_id))
            result = await self.session.execute(stmt)
            db_estimation = result.scalar_one_or_none()
            
            if not db_estimation:
                return None
            
            # Обновляем поля
            for key, value in kwargs.items():
                if hasattr(db_estimation, key):
                    setattr(db_estimation, key, value)
            
            db_estimation.updated_at = datetime.now()
            await self.session.commit()
            await self.session.refresh(db_estimation)
            
            # Обновляем историю
            await self._update_history(db_estimation.card_id, db_estimation)
            
            return self._convert_db_to_response(db_estimation)
            
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Ошибка обновления оценки: {e}")
    
    async def update_estimation_status(self, estimation_id: str, status: str, error: str = None) -> Optional[EstimationResult]:
        """Обновляет статус оценки"""
        try:
            stmt = select(DBEstimationResult).where(DBEstimationResult.id == uuid.UUID(estimation_id))
            result = await self.session.execute(stmt)
            db_estimation = result.scalar_one_or_none()
            
            if not db_estimation:
                return None
            
            db_estimation.status = status
            if error:
                db_estimation.error_message = error
            
            db_estimation.updated_at = datetime.now()
            await self.session.commit()
            await self.session.refresh(db_estimation)
            
            # Обновляем историю
            await self._update_history(db_estimation.card_id, db_estimation)
            
            return self._convert_db_to_response(db_estimation)
            
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Ошибка обновления статуса оценки: {e}")
    
    async def get_all_estimations(self) -> List[EstimationResult]:
        """Получает все оценки (для отладки)"""
        try:
            stmt = select(DBEstimationResult)
            result = await self.session.execute(stmt)
            db_estimations = result.scalars().all()
            
            return [self._convert_db_to_response(est) for est in db_estimations]
            
        except Exception as e:
            raise Exception(f"Ошибка получения всех оценок: {e}")
    
    async def get_estimations_by_card_id(self, card_id: str) -> List[EstimationResult]:
        """Получает все оценки для конкретной карточки"""
        try:
            stmt = select(DBEstimationResult).where(DBEstimationResult.card_id == card_id)
            result = await self.session.execute(stmt)
            db_estimations = result.scalars().all()
            
            return [self._convert_db_to_response(est) for est in db_estimations]
            
        except Exception as e:
            raise Exception(f"Ошибка получения оценок по card_id: {e}")
    
    async def get_estimation_history(self, card_id: str) -> EstimationHistory:
        """Получает историю оценок для карточки"""
        try:
            estimations = await self.get_estimations_by_card_id(card_id)
            
            return EstimationHistory(
                cardId=card_id,
                estimations=estimations,
                totalEstimations=len(estimations),
                lastUpdated=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Ошибка получения истории оценок: {e}")
    
    async def add_feedback(self, feedback: EstimationFeedback) -> EstimationFeedback:
        """Добавляет обратную связь к оценке"""
        try:
            db_feedback = DBEstimationFeedback(
                estimation_id=uuid.UUID(feedback.estimationId),
                feedback=feedback.feedback,
                actual_hours=feedback.actualHours,
                accuracy=feedback.accuracy,
                difficulty=feedback.difficulty,
                blockers=feedback.blockers or [],
                notes=feedback.notes
            )
            
            self.session.add(db_feedback)
            await self.session.commit()
            await self.session.refresh(db_feedback)
            
            # Обновляем оценку с фактическим временем
            if feedback.actualHours:
                await self.update_estimation(
                    feedback.estimationId,
                    actual_hours=feedback.actualHours,
                    completed_at=datetime.now()
                )
            
            # Конвертируем обратно
            feedback.id = str(db_feedback.id)
            return feedback
            
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Ошибка добавления feedback: {e}")
    
    async def get_feedback_for_estimation(self, estimation_id: str) -> List[EstimationFeedback]:
        """Получает обратную связь для оценки"""
        try:
            stmt = select(DBEstimationFeedback).where(DBEstimationFeedback.estimation_id == uuid.UUID(estimation_id))
            result = await self.session.execute(stmt)
            db_feedbacks = result.scalars().all()
            
            feedbacks = []
            for db_feedback in db_feedbacks:
                feedback = EstimationFeedback(
                    estimationId=estimation_id,
                    feedback=db_feedback.feedback,
                    actualHours=db_feedback.actual_hours,
                    accuracy=db_feedback.accuracy,
                    difficulty=db_feedback.difficulty,
                    blockers=db_feedback.blockers or [],
                    notes=db_feedback.notes
                )
                feedback.id = str(db_feedback.id)
                feedbacks.append(feedback)
            
            return feedbacks
            
        except Exception as e:
            raise Exception(f"Ошибка получения feedback: {e}")
    
    async def get_accuracy_statistics(self, card_id: str) -> Dict[str, float]:
        """Вычисляет статистику точности оценок"""
        try:
            estimations = await self.get_estimations_by_card_id(card_id)
            completed_estimations = [
                est for est in estimations
                if est.status == "completed" and est.actualHours
            ]
            
            if not completed_estimations:
                return {
                    'total_estimations': len(estimations),
                    'completed_estimations': 0,
                    'average_accuracy': 0.0,
                    'accuracy_trend': 0.0
                }
            
            # Вычисляем точность каждой оценки
            accuracies = []
            for est in completed_estimations:
                if est.estimatedHours and est.actualHours:
                    accuracy = min(est.estimatedHours / est.actualHours, est.actualHours / est.estimatedHours)
                    accuracies.append(accuracy * 100)  # В процентах
            
            if not accuracies:
                return {
                    'total_estimations': len(estimations),
                    'completed_estimations': len(completed_estimations),
                    'average_accuracy': 0.0,
                    'accuracy_trend': 0.0
                }
            
            avg_accuracy = sum(accuracies) / len(accuracies)
            
            # Простая тенденция (сравниваем первые и последние оценки)
            if len(accuracies) >= 2:
                first_half = accuracies[:len(accuracies)//2]
                second_half = accuracies[len(accuracies)//2:]
                trend = (sum(second_half) / len(second_half)) - (sum(first_half) / len(first_half))
            else:
                trend = 0.0
            
            return {
                'total_estimations': len(estimations),
                'completed_estimations': len(completed_estimations),
                'average_accuracy': round(avg_accuracy, 2),
                'accuracy_trend': round(trend, 2)
            }
            
        except Exception as e:
            raise Exception(f"Ошибка получения статистики точности: {e}")
    
    async def get_complexity_distribution(self, card_id: str) -> Dict[str, int]:
        """Получает распределение оценок по сложности"""
        try:
            estimations = await self.get_estimations_by_card_id(card_id)
            distribution = {
                'simple': 0,
                'medium': 0,
                'complex': 0,
                'very-complex': 0
            }
            
            for est in estimations:
                if est.metadata and 'complexity' in est.metadata:
                    complexity = est.metadata['complexity']
                    if complexity in distribution:
                        distribution[complexity] += 1
            
            return distribution
            
        except Exception as e:
            raise Exception(f"Ошибка получения распределения сложности: {e}")
    
    async def get_priority_distribution(self, card_id: str) -> Dict[str, int]:
        """Получает распределение оценок по приоритету"""
        try:
            estimations = await self.get_estimations_by_card_id(card_id)
            distribution = {
                'low': 0,
                'medium': 0,
                'high': 0,
                'urgent': 0
            }
            
            for est in estimations:
                if est.metadata and 'priority' in est.metadata:
                    priority = est.metadata['priority']
                    if priority in distribution:
                        distribution[priority] += 1
            
            return distribution
            
        except Exception as e:
            raise Exception(f"Ошибка получения распределения приоритета: {e}")
    
    async def cleanup_old_estimations(self, days_old: int = 90):
        """Очищает старые оценки для экономии места в базе"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Удаляем старые оценки
            stmt = delete(DBEstimationResult).where(DBEstimationResult.created_at < cutoff_date)
            result = await self.session.execute(stmt)
            deleted_count = result.rowcount
            
            # Удаляем связанные feedback
            stmt = delete(DBEstimationFeedback).where(DBEstimationFeedback.created_at < cutoff_date)
            await self.session.execute(stmt)
            
            await self.session.commit()
            return deleted_count
            
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Ошибка очистки старых оценок: {e}")
    
    async def _update_history(self, card_id: str, estimation: DBEstimationResult):
        """Обновляет историю оценок для карточки (заглушка)"""
        # В PostgreSQL версии история вычисляется динамически
        pass
    
    async def _update_user_performance(self, user_id: str, estimation: DBEstimationResult):
        """Обновляет базовую статистику пользователя при создании оценки"""
        # В PostgreSQL версии статистика вычисляется динамически
        pass
    
    async def _update_user_performance_stats(self, user_id: str, estimation: DBEstimationResult, actual_hours: float):
        """Обновляет детальную статистику пользователя при завершении задачи"""
        # В PostgreSQL версии статистика вычисляется динамически
        pass
    
    async def _update_project_stats(self, project_id: str, estimation: DBEstimationResult):
        """Обновляет статистику проекта при создании оценки"""
        # В PostgreSQL версии статистика вычисляется динамически
        pass
    
    async def _update_project_completion_stats(self, project_id: str, estimation: DBEstimationResult, actual_hours: float):
        """Обновляет статистику проекта при завершении задачи"""
        # В PostgreSQL версии статистика вычисляется динамически
        pass
    
    def _convert_db_to_response(self, db_estimation: DBEstimationResult) -> EstimationResult:
        """Конвертирует DB модель в модель ответа"""
        return EstimationResult(
            card_id=db_estimation.task_metadata.get('card_id', str(db_estimation.task_id)),
            status=db_estimation.status,
            estimated_hours=db_estimation.estimated_hours,
            confidence_score=db_estimation.confidence_score,
            priority=db_estimation.task_metadata.get('priority', 'medium') if db_estimation.task_metadata else 'medium',
            complexity=db_estimation.task_metadata.get('complexity', 'medium') if db_estimation.task_metadata else 'medium',
            error_message=None,  # В SQLAlchemy модели нет этого поля
            metadata=db_estimation.task_metadata or {},
            created_at=db_estimation.created_at
        )

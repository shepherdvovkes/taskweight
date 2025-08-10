import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from ..models.estimation import (
    EstimationResult, EstimationStatus, EstimationInsights, EstimationFeedback, 
    EstimationHistory, UserPerformanceUpdate, UserPerformanceStats, ProjectStats,
    BatchEstimationResponse
)

class InMemoryStorage:
    def __init__(self):
        self._estimations: Dict[str, EstimationResult] = {}
        self._feedback: Dict[str, EstimationFeedback] = {}
        self._history: Dict[str, EstimationHistory] = {}
        self._user_performance: Dict[str, UserPerformanceStats] = {}
        self._project_stats: Dict[str, ProjectStats] = {}
        self._batch_estimations: Dict[str, BatchEstimationResponse] = {}
    
    def create_estimation(self, card_id: str, user_id: Optional[str] = None, 
                         team_id: Optional[str] = None, project_id: Optional[str] = None,
                         batch_id: Optional[str] = None) -> EstimationResult:
        """Создает новую запись оценки"""
        estimation_id = str(uuid.uuid4())
        estimation = EstimationResult(
            id=estimation_id,
            cardId=card_id,
            status=EstimationStatus.PROCESSING,
            createdAt=datetime.now(),
            userId=user_id,
            teamId=team_id,
            projectId=project_id,
            batchId=batch_id
        )
        self._estimations[estimation_id] = estimation
        
        # Создаем или обновляем историю
        self._update_history(card_id, estimation)
        
        # Обновляем статистику пользователя
        if user_id:
            self._update_user_performance(user_id, estimation)
        
        # Обновляем статистику проекта
        if project_id:
            self._update_project_stats(project_id, estimation)
        
        return estimation
    
    def create_batch_estimation(self, tasks: List, user_id: Optional[str] = None,
                               team_id: Optional[str] = None, project_id: Optional[str] = None) -> BatchEstimationResponse:
        """Создает batch estimation для множества задач"""
        batch_id = str(uuid.uuid4())
        batch = BatchEstimationResponse(
            batchId=batch_id,
            totalTasks=len(tasks),
            processingTasks=len(tasks),
            completedTasks=0,
            failedTasks=0,
            status="processing",
            createdAt=datetime.now()
        )
        self._batch_estimations[batch_id] = batch
        return batch
    
    def update_batch_status(self, batch_id: str, completed: int = 0, failed: int = 0):
        """Обновляет статус batch estimation"""
        if batch_id in self._batch_estimations:
            batch = self._batch_estimations[batch_id]
            batch.completedTasks += completed
            batch.failedTasks += failed
            batch.processingTasks = batch.totalTasks - batch.completedTasks - batch.failedTasks
            
            if batch.processingTasks == 0:
                batch.status = "completed" if batch.failedTasks == 0 else "completed_with_errors"
    
    def get_batch_status(self, batch_id: str) -> Optional[BatchEstimationResponse]:
        """Получает статус batch estimation"""
        return self._batch_estimations.get(batch_id)
    
    def update_user_performance(self, estimation_id: str, actual_hours: float, 
                               user_id: str, notes: Optional[str] = None,
                               difficulty: Optional[int] = None, blockers: Optional[List[str]] = None):
        """Обновляет производительность пользователя на основе фактического времени"""
        estimation = self.get_estimation(estimation_id)
        if not estimation:
            return None
        
        # Обновляем оценку
        self.update_estimation(
            estimation_id,
            actualHours=actual_hours,
            completedAt=datetime.now(),
            status=EstimationStatus.COMPLETED
        )
        
        # Обновляем статистику пользователя
        self._update_user_performance_stats(user_id, estimation, actual_hours)
        
        # Обновляем статистику проекта
        if estimation.projectId:
            self._update_project_completion_stats(estimation.projectId, estimation, actual_hours)
        
        return estimation
    
    def get_user_performance_stats(self, user_id: str) -> UserPerformanceStats:
        """Получает статистику производительности пользователя"""
        if user_id not in self._user_performance:
            self._user_performance[user_id] = UserPerformanceStats(
                userId=user_id,
                totalTasks=0,
                completedTasks=0,
                averageAccuracy=0.0,
                estimationBias=0.0,
                complexityPreference={},
                lastUpdated=datetime.now()
            )
        return self._user_performance[user_id]
    
    def get_project_stats(self, project_id: str) -> ProjectStats:
        """Получает статистику проекта"""
        if project_id not in self._project_stats:
            self._project_stats[project_id] = ProjectStats(
                projectId=project_id,
                totalTasks=0,
                completedTasks=0,
                averageAccuracy=0.0,
                totalEstimatedHours=0.0,
                totalActualHours=0.0,
                efficiency=0.0,
                lastUpdated=datetime.now()
            )
        return self._project_stats[project_id]
    
    def get_estimations_by_user(self, user_id: str) -> List[EstimationResult]:
        """Получает все оценки пользователя"""
        return [
            estimation for estimation in self._estimations.values()
            if estimation.userId == user_id
        ]
    
    def get_estimations_by_project(self, project_id: str) -> List[EstimationResult]:
        """Получает все оценки проекта"""
        return [
            estimation for estimation in self._estimations.values()
            if estimation.projectId == project_id
        ]
    
    def get_estimations_by_team(self, team_id: str) -> List[EstimationResult]:
        """Получает все оценки команды"""
        return [
            estimation for estimation in self._estimations.values()
            if estimation.teamId == team_id
        ]

    def get_estimation_by_card_id(self, card_id: str) -> Optional[EstimationResult]:
        """Получает оценку по ID карточки Trello"""
        for estimation in self._estimations.values():
            if estimation.cardId == card_id:
                return estimation
        return None
    
    def get_estimation(self, estimation_id: str) -> Optional[EstimationResult]:
        """Получает оценку по ID"""
        return self._estimations.get(estimation_id)
    
    def update_estimation(self, estimation_id: str, **kwargs) -> Optional[EstimationResult]:
        """Обновляет оценку"""
        if estimation_id not in self._estimations:
            return None
        
        estimation = self._estimations[estimation_id]
        for key, value in kwargs.items():
            if hasattr(estimation, key):
                setattr(estimation, key, value)
        
        # Обновляем историю
        self._update_history(estimation.cardId, estimation)
        
        return estimation
    
    def update_estimation_status(self, estimation_id: str, status: str, error: str = None) -> Optional[EstimationResult]:
        """Обновляет статус оценки"""
        if estimation_id not in self._estimations:
            return None
        
        estimation = self._estimations[estimation_id]
        estimation.status = status
        if error:
            estimation.error = error
        
        # Обновляем историю
        self._update_history(estimation.cardId, estimation)
        
        return estimation
    
    def get_all_estimations(self) -> List[EstimationResult]:
        """Получает все оценки (для отладки)"""
        return list(self._estimations.values())
    
    def get_estimations_by_card_id(self, card_id: str) -> List[EstimationResult]:
        """Получает все оценки для конкретной карточки"""
        return [
            estimation for estimation in self._estimations.values()
            if estimation.cardId == card_id
        ]
    
    def get_estimation_history(self, card_id: str) -> EstimationHistory:
        """Получает историю оценок для карточки"""
        if card_id not in self._history:
            # Создаем историю на основе существующих оценок
            estimations = self.get_estimations_by_card_id(card_id)
            self._history[card_id] = EstimationHistory(
                cardId=card_id,
                estimations=estimations,
                totalEstimations=len(estimations),
                lastUpdated=datetime.now()
            )
        
        return self._history[card_id]
    
    def add_feedback(self, feedback: EstimationFeedback) -> EstimationFeedback:
        """Добавляет обратную связь к оценке"""
        feedback_id = str(uuid.uuid4())
        feedback.id = feedback_id
        self._feedback[feedback_id] = feedback
        
        # Обновляем оценку с фактическим временем
        if feedback.actualHours:
            estimation = self.get_estimation(feedback.estimationId)
            if estimation:
                self.update_estimation(
                    feedback.estimationId,
                    actualHours=feedback.actualHours,
                    completedAt=datetime.now()
                )
        
        return feedback
    
    def get_feedback_for_estimation(self, estimation_id: str) -> List[EstimationFeedback]:
        """Получает обратную связь для оценки"""
        return [
            feedback for feedback in self._feedback.values()
            if feedback.estimationId == estimation_id
        ]
    
    def get_accuracy_statistics(self, card_id: str) -> Dict[str, float]:
        """Вычисляет статистику точности оценок"""
        estimations = self.get_estimations_by_card_id(card_id)
        completed_estimations = [
            est for est in estimations
            if est.status == EstimationStatus.COMPLETED and est.actualHours
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
    
    def get_complexity_distribution(self, card_id: str) -> Dict[str, int]:
        """Получает распределение оценок по сложности"""
        estimations = self.get_estimations_by_card_id(card_id)
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
    
    def get_priority_distribution(self, card_id: str) -> Dict[str, int]:
        """Получает распределение оценок по приоритету"""
        estimations = self.get_estimations_by_card_id(card_id)
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
    
    def _update_history(self, card_id: str, estimation: EstimationResult):
        """Обновляет историю оценок для карточки"""
        if card_id not in self._history:
            self._history[card_id] = EstimationHistory(
                cardId=card_id,
                estimations=[],
                totalEstimations=0,
                lastUpdated=datetime.now()
            )
        
        history = self._history[card_id]
        
        # Добавляем новую оценку или обновляем существующую
        existing_index = None
        for i, existing_est in enumerate(history.estimations):
            if existing_est.id == estimation.id:
                existing_index = i
                break
        
        if existing_index is not None:
            history.estimations[existing_index] = estimation
        else:
            history.estimations.append(estimation)
        
        # Обновляем статистику
        history.totalEstimations = len(history.estimations)
        history.lastUpdated = datetime.now()
        
        # Вычисляем среднюю точность
        stats = self.get_accuracy_statistics(card_id)
        history.averageAccuracy = stats['average_accuracy']
    
    def _update_user_performance(self, user_id: str, estimation: EstimationResult):
        """Обновляет базовую статистику пользователя при создании оценки"""
        if user_id not in self._user_performance:
            self._user_performance[user_id] = UserPerformanceStats(
                userId=user_id,
                totalTasks=0,
                completedTasks=0,
                averageAccuracy=0.0,
                estimationBias=0.0,
                complexityPreference={},
                lastUpdated=datetime.now()
            )
        
        stats = self._user_performance[user_id]
        stats.totalTasks += 1
        stats.lastUpdated = datetime.now()
    
    def _update_user_performance_stats(self, user_id: str, estimation: EstimationResult, actual_hours: float):
        """Обновляет детальную статистику пользователя при завершении задачи"""
        stats = self.get_user_performance_stats(user_id)
        stats.completedTasks += 1
        
        if estimation.estimatedHours:
            # Вычисляем bias (разницу между оценкой и реальностью)
            bias = estimation.estimatedHours - actual_hours
            if stats.completedTasks == 1:
                stats.estimationBias = bias
            else:
                # Обновляем средний bias
                total_bias = stats.estimationBias * (stats.completedTasks - 1) + bias
                stats.estimationBias = total_bias / stats.completedTasks
            
            # Обновляем точность
            accuracy = min(estimation.estimatedHours / actual_hours, actual_hours / estimation.estimatedHours)
            if stats.completedTasks == 1:
                stats.averageAccuracy = accuracy * 100
            else:
                total_accuracy = stats.averageAccuracy * (stats.completedTasks - 1) + (accuracy * 100)
                stats.averageAccuracy = total_accuracy / stats.completedTasks
        
        # Обновляем предпочтения по сложности
        if estimation.metadata and 'complexity' in estimation.metadata:
            complexity = estimation.metadata['complexity']
            if complexity not in stats.complexityPreference:
                stats.complexityPreference[complexity] = 0
            stats.complexityPreference[complexity] += 1
        
        stats.lastUpdated = datetime.now()
    
    def _update_project_stats(self, project_id: str, estimation: EstimationResult):
        """Обновляет статистику проекта при создании оценки"""
        if project_id not in self._project_stats:
            self._project_stats[project_id] = ProjectStats(
                projectId=project_id,
                totalTasks=0,
                completedTasks=0,
                averageAccuracy=0.0,
                totalEstimatedHours=0.0,
                totalActualHours=0.0,
                efficiency=0.0,
                lastUpdated=datetime.now()
            )
        
        stats = self._project_stats[project_id]
        stats.totalTasks += 1
        if estimation.estimatedHours:
            stats.totalEstimatedHours += estimation.estimatedHours
        stats.lastUpdated = datetime.now()
    
    def _update_project_completion_stats(self, project_id: str, estimation: EstimationResult, actual_hours: float):
        """Обновляет статистику проекта при завершении задачи"""
        stats = self._project_stats[project_id]
        stats.completedTasks += 1
        stats.totalActualHours += actual_hours
        
        if estimation.estimatedHours:
            # Обновляем точность
            accuracy = min(estimation.estimatedHours / actual_hours, actual_hours / estimation.estimatedHours)
            if stats.completedTasks == 1:
                stats.averageAccuracy = accuracy * 100
            else:
                total_accuracy = stats.averageAccuracy * (stats.completedTasks - 1) + (accuracy * 100)
                stats.averageAccuracy = total_accuracy / stats.completedTasks
        
        # Обновляем эффективность
        if stats.totalEstimatedHours > 0 and stats.totalActualHours > 0:
            stats.efficiency = stats.totalEstimatedHours / stats.totalActualHours
        
        stats.lastUpdated = datetime.now()
    
    def update_card_metadata(self, card_id: str, metadata: Dict[str, Any]) -> bool:
        """Обновляет метаданные карточки"""
        try:
            # Здесь должна быть логика обновления метаданных
            # Пока возвращаем заглушку
            print(f"Метаданные карточки {card_id} обновлены: {metadata}")
            return True
        except Exception as e:
            print(f"Ошибка обновления метаданных карточки {card_id}: {e}")
            return False

    def create_reestimation(self, card_id: str, reason: str, user_id: Optional[str] = None) -> EstimationResult:
        """Создает новую оценку для переоценки"""
        try:
            # Здесь должна быть логика создания переоценки
            # Пока возвращаем заглушку
            estimation = EstimationResult(
                card_id=card_id,
                status="processing",
                priority="medium",
                complexity="medium",
                metadata={"reestimation_reason": reason}
            )
            self.logger.info(f"Создана переоценка для карточки {card_id}: {reason}")
            return estimation
        except Exception as e:
            self.logger.error(f"Ошибка создания переоценки для карточки {card_id}: {e}")
            raise

    def get_card_statistics(self, card_id: str) -> Dict[str, Any]:
        """Получает полную статистику по карточке"""
        try:
            # Получаем все необходимые данные
            estimation = self.get_estimation_by_card_id(card_id)
            history = self.get_estimation_history(card_id)
            accuracy = self.get_accuracy_statistics(card_id)
            complexity_dist = self.get_complexity_distribution(card_id)
            priority_dist = self.get_priority_distribution(card_id)
            
            # Формируем статистику
            stats = {
                "card_id": card_id,
                "total_estimations": history.total_estimations if hasattr(history, 'total_estimations') else 0,
                "average_estimated_hours": 0.0,
                "average_actual_hours": None,
                "average_accuracy": accuracy.get("average_accuracy"),
                "complexity_distribution": complexity_dist,
                "priority_distribution": priority_dist,
                "status_distribution": {"processing": 0, "estimated": 0, "completed": 0, "failed": 0},
                "recent_estimations": history.estimations if hasattr(history, 'estimations') else [],
                "accuracy_trend": accuracy.get("accuracy_trend")
            }
            
            self.logger.info(f"Статистика карточки {card_id} получена")
            return stats
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики карточки {card_id}: {e}")
            # Возвращаем пустую статистику в случае ошибки
            return {
                "card_id": card_id,
                "total_estimations": 0,
                "average_estimated_hours": 0.0,
                "complexity_distribution": {"low": 0, "medium": 0, "high": 0},
                "priority_distribution": {"low": 0, "medium": 0, "high": 0},
                "status_distribution": {"processing": 0, "estimated": 0, "completed": 0, "failed": 0},
                "recent_estimations": []
            }

    def cleanup_old_estimations(self, days_old: int = 90):
        """Очищает старые оценки для экономии памяти"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        old_ids = []
        for est_id, estimation in self._estimations.items():
            if estimation.createdAt < cutoff_date:
                old_ids.append(est_id)
        
        for est_id in old_ids:
            del self._estimations[est_id]
        
        # Очищаем историю
        for card_id in list(self._history.keys()):
            history = self._history[card_id]
            history.estimations = [
                est for est in history.estimations
                if est.createdAt >= cutoff_date
            ]
            if not history.estimations:
                del self._history[card_id]
            else:
                history.totalEstimations = len(history.estimations)
        
        return len(old_ids)

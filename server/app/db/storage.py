import uuid
from datetime import datetime
from typing import Dict, Optional
from ..models.estimation import EstimationResult, EstimationStatus

class InMemoryStorage:
    def __init__(self):
        self._estimations: Dict[str, EstimationResult] = {}
    
    def create_estimation(self, card_id: str) -> EstimationResult:
        """Создает новую запись оценки"""
        estimation_id = str(uuid.uuid4())
        estimation = EstimationResult(
            id=estimation_id,
            cardId=card_id,
            status=EstimationStatus.PROCESSING,
            createdAt=datetime.now()
        )
        self._estimations[estimation_id] = estimation
        return estimation
    
    def get_estimation_by_card_id(self, card_id: str) -> Optional[EstimationResult]:
        """Получает оценку по ID карточки Trello"""
        for estimation in self._estimations.values():
            if estimation.cardId == card_id:
                return estimation
        return None
    
    def update_estimation(self, estimation_id: str, **kwargs) -> Optional[EstimationResult]:
        """Обновляет оценку"""
        if estimation_id not in self._estimations:
            return None
        
        estimation = self._estimations[estimation_id]
        for key, value in kwargs.items():
            if hasattr(estimation, key):
                setattr(estimation, key, value)
        
        return estimation
    
    def get_all_estimations(self) -> list[EstimationResult]:
        """Получает все оценки (для отладки)"""
        return list(self._estimations.values())

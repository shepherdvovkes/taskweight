from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class EstimationStatus(str, Enum):
    PROCESSING = "processing"
    ESTIMATED = "estimated"
    COMPLETED = "completed"
    FAILED = "failed"

class EstimationRequest(BaseModel):
    cardId: str = Field(..., description="Trello card ID")
    taskDescription: str = Field(..., description="Task description")
    repoUrl: str = Field(..., description="GitHub repository URL")

class EstimationResponse(BaseModel):
    status: EstimationStatus
    message: str
    cardId: str
    estimatedHours: Optional[float] = None
    error: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.now)

class EstimationResult(BaseModel):
    id: str
    cardId: str
    status: EstimationStatus
    estimatedHours: Optional[float] = None
    actualHours: Optional[float] = None
    createdAt: datetime
    completedAt: Optional[datetime] = None
    error: Optional[str] = None

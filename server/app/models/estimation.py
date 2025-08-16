from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
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
    priority: Optional[str] = Field("medium", description="Task priority")
    complexity: Optional[str] = Field("medium", description="Expected complexity")

class BatchEstimationRequest(BaseModel):
    tasks: List[EstimationRequest] = Field(..., description="List of tasks to estimate")
    userId: Optional[str] = Field(None, description="User ID for tracking")
    teamId: Optional[str] = Field(None, description="Team ID for tracking")
    projectId: Optional[str] = Field(None, description="Project ID for tracking")

class BatchEstimationResponse(BaseModel):
    batchId: str = Field(..., description="Unique batch ID")
    totalTasks: int = Field(..., description="Total number of tasks")
    processingTasks: int = Field(0, description="Number of tasks being processed")
    completedTasks: int = Field(0, description="Number of completed estimations")
    failedTasks: int = Field(0, description="Number of failed estimations")
    status: str = Field(..., description="Overall batch status")
    createdAt: datetime = Field(default_factory=datetime.now)
    estimatedCompletionTime: Optional[datetime] = Field(None, description="Estimated completion time")

class EstimationResponse(BaseModel):
    status: EstimationStatus
    message: str
    cardId: str
    estimatedHours: Optional[float] = None
    confidence: Optional[int] = None
    error: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.now)

class Estimation(BaseModel):
    id: Optional[int] = None
    card_id: str
    task_description: str
    repo_url: str
    estimated_hours: Optional[float] = None
    confidence_score: Optional[float] = None
    priority: str = "medium"
    complexity: str = "medium"
    status: str = "processing"
    error_message: Optional[str] = None
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Новые поля для Trello интеграции
    trello_card_name: Optional[str] = None
    trello_card_desc: Optional[str] = None
    trello_labels: Optional[List[str]] = None
    trello_due_date: Optional[datetime] = None
    trello_members: Optional[List[str]] = None
    trello_checklists: Optional[List[Dict[str, Any]]] = None
    trello_attachments: Optional[List[Dict[str, Any]]] = None
    
    # Поля для анализа точности
    actual_hours: Optional[float] = None
    accuracy_score: Optional[float] = None
    estimation_confidence: Optional[str] = None
    
    class Config:
        from_attributes = True

class EstimationResult(BaseModel):
    card_id: str
    status: str
    estimated_hours: Optional[float] = None
    confidence_score: Optional[float] = None
    priority: str
    complexity: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
    # Trello специфичные поля
    trello_analysis: Optional[Dict[str, Any]] = None
    accuracy_metrics: Optional[Dict[str, Any]] = None

class EstimationInsights(BaseModel):
    accuracyScore: float = Field(..., description="Estimated accuracy score")
    complexityLevel: str = Field(..., description="Assessed complexity level")
    riskFactors: list[str] = Field(default_factory=list, description="Identified risk factors")
    recommendations: list[str] = Field(default_factory=list, description="Improvement recommendations")

class EstimationFeedback(BaseModel):
    estimationId: str = Field(..., description="ID of estimation to refine")
    feedback: str = Field(..., description="User feedback for refinement")
    actualHours: Optional[float] = Field(None, description="Actual time spent")
    accuracy: Optional[int] = Field(None, description="User rating of accuracy 1-10")

class UserPerformanceUpdate(BaseModel):
    estimationId: str = Field(..., description="ID of estimation to update")
    actualHours: float = Field(..., description="Actual time spent on task")
    userId: str = Field(..., description="User ID who completed the task")
    notes: Optional[str] = Field(None, description="Additional notes about completion")
    difficulty: Optional[int] = Field(None, description="User rating of difficulty 1-10")
    blockers: Optional[List[str]] = Field(None, description="List of blockers encountered")

class EstimationHistory(BaseModel):
    cardId: str = Field(..., description="Trello card ID")
    estimations: list[EstimationResult] = Field(default_factory=list, description="History of estimations")
    totalEstimations: int = Field(0, description="Total number of estimations")
    averageAccuracy: Optional[float] = Field(None, description="Average accuracy score")
    lastUpdated: datetime = Field(default_factory=datetime.now)

class UserPerformanceStats(BaseModel):
    userId: str = Field(..., description="User ID")
    totalTasks: int = Field(0, description="Total number of tasks estimated")
    completedTasks: int = Field(0, description="Number of completed tasks")
    averageAccuracy: float = Field(0.0, description="Average accuracy score")
    estimationBias: float = Field(0.0, description="Average difference between estimated and actual")
    complexityPreference: Dict[str, float] = Field(default_factory=dict, description="Preference for different complexity levels")
    lastUpdated: datetime = Field(default_factory=datetime.now)

class ProjectStats(BaseModel):
    projectId: str = Field(..., description="Project ID")
    totalTasks: int = Field(0, description="Total number of tasks")
    completedTasks: int = Field(0, description="Number of completed tasks")
    averageAccuracy: float = Field(0.0, description="Average accuracy score")
    totalEstimatedHours: float = Field(0.0, description="Total estimated hours")
    totalActualHours: float = Field(0.0, description="Total actual hours")
    efficiency: float = Field(0.0, description="Efficiency ratio (estimated/actual)")
    lastUpdated: datetime = Field(default_factory=datetime.now)

class TrelloCardData(BaseModel):
    id: str
    name: str
    desc: Optional[str] = None
    labels: Optional[List[Dict[str, Any]]] = None
    due: Optional[str] = None
    idMembers: Optional[List[str]] = None
    checklists: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    badges: Optional[Dict[str, Any]] = None

class TrelloEstimationRequest(BaseModel):
    card_id: str = Field(..., min_length=1, description="Trello card ID")
    task_description: str = Field(..., min_length=10, description="Task description (min 10 characters)")
    repo_url: str = Field(..., pattern=r"^https?://github\.com/[^/]+/[^/]+", description="GitHub repository URL")
    priority: str = Field("medium", pattern="^(low|medium|high|critical)$", description="Task priority")
    complexity: str = Field("medium", pattern="^(simple|medium|complex|very_complex)$", description="Expected complexity")
    user_id: Optional[str] = Field(None, min_length=1, description="User ID for tracking")
    team_id: Optional[str] = Field(None, min_length=1, description="Team ID for tracking")
    project_id: Optional[str] = Field(None, min_length=1, description="Project ID for tracking")
    trello_card_data: Optional[TrelloCardData] = Field(None, description="Trello card data for enhanced analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "card_id": "64f1a2b3c4d5e6f7g8h9i0j1",
                "task_description": "Implement user authentication system with JWT tokens",
                "repo_url": "https://github.com/username/project-name",
                "priority": "high",
                "complexity": "complex",
                "user_id": "user123",
                "team_id": "team456",
                "project_id": "project789"
            }
        }

class CardStatistics(BaseModel):
    card_id: str
    total_estimations: int
    average_estimated_hours: float
    average_actual_hours: Optional[float] = None
    average_accuracy: Optional[float] = None
    complexity_distribution: Dict[str, int]
    priority_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    recent_estimations: List[Estimation]
    accuracy_trend: Optional[List[float]] = None

class TrelloAnalysis(BaseModel):
    complexity_indicators: List[str]
    priority_indicators: List[str]
    label_count: int
    has_due_date: bool
    member_count: int
    checklist_count: int
    attachment_count: int
    estimated_complexity: str
    estimated_priority: str
    confidence_factors: List[str]

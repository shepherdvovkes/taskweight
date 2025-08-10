from pydantic import BaseModel
from typing import Optional, Any

class TrelloWebhook(BaseModel):
    action: dict[str, Any]
    model: dict[str, Any]
    
class TrelloAction(BaseModel):
    id: str
    type: str
    data: dict[str, Any]
    date: str

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class ConversationResponse(BaseModel):
    id: UUID
    title: str

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime

    class Config:
        from_attributes = True
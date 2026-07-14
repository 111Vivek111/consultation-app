from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
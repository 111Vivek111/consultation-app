from uuid import UUID

from pydantic import BaseModel


class ConversationResponse(BaseModel):
    id: UUID
    title: str

    class Config:
        from_attributes = True
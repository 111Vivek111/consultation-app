from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):

    id: UUID
    filename: str
    file_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
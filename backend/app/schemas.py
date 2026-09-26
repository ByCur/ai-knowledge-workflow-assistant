from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255
    )

    description: str = ""


class DocumentResponse(BaseModel):
    id: int
    name: str
    description: str
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
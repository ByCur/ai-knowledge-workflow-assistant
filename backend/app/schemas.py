from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: int
    name: str
    description: str
    original_filename: str | None
    content_type: str | None
    file_size: int | None
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class DocumentDetailResponse(DocumentResponse):
    extracted_text: str
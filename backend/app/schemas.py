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

class ChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str

    model_config = ConfigDict(
        from_attributes=True
    )


class IndexDocumentResponse(BaseModel):
    document_id: int
    chunks_created: int
    status: str

class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class SearchResult(BaseModel):
    document_id: int
    document_name: str
    chunk_index: int
    content: str
    similarity: float

class AskRequest(BaseModel):
    question: str
    


class AskResponse(BaseModel):
    answer: str
    sources: list[SearchResult]
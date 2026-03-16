import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    content: str | None = None

    model_config = {"from_attributes": True}


class PaginatedDocuments(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class ChunkResponse(BaseModel):
    id: uuid.UUID
    chunk_index: int

    model_config = {"from_attributes": True}


class TextDocumentRequest(BaseModel):
    content: str
    filename: str
    content_type: str = "text/plain"


class UpdateDocumentRequest(BaseModel):
    content: str
    filename: str | None = None


class SearchRequest(BaseModel):
    query: str
    max_results: int | None = None


class ChunkResult(BaseModel):
    chunk_id: str
    chunk_index: int
    relevance_score: float


class DocumentSearchResult(BaseModel):
    document_id: str
    filename: str
    content_type: str
    content: str | None = None
    status: str
    created_at: str
    updated_at: str | None = None
    chunks: list[ChunkResult]


class SearchResponse(BaseModel):
    query: str
    results: list[DocumentSearchResult]

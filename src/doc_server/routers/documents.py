import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from doc_server.config import settings
from doc_server.database import get_db
from doc_server.models import Chunk, Document
from doc_server.schemas import (
    ChunkResponse,
    DocumentResponse,
    PaginatedDocuments,
    TextDocumentRequest,
    UpdateDocumentRequest,
)
from doc_server.services.chunking import (
    _persist_document,
    chunk_and_embed,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile, db: AsyncSession = Depends(get_db)
) -> Document:
    content_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"

    text: str | None = None
    if content_type.startswith("text/"):
        text = content_bytes.decode("utf-8")

    doc = Document(
        filename=file.filename or "unnamed",
        content_type=content_type,
        content=text,
        status="ready",
    )
    await _persist_document(db, doc)

    if text:
        await chunk_and_embed(
            db, doc, text, settings.chunk_size, settings.chunk_overlap
        )

    return doc


@router.post("/text", response_model=DocumentResponse, status_code=201)
async def upload_text_document(
    body: TextDocumentRequest, db: AsyncSession = Depends(get_db)
) -> Document:
    doc = Document(
        filename=body.filename,
        content_type=body.content_type,
        content=body.content,
        status="ready",
    )
    await _persist_document(db, doc)

    await chunk_and_embed(
        db, doc, body.content, settings.chunk_size, settings.chunk_overlap
    )

    return doc


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    body: UpdateDocumentRequest,
    db: AsyncSession = Depends(get_db),
) -> Document:
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.content = body.content
    if body.filename:
        doc.filename = body.filename
    doc.updated_at = datetime.now(timezone.utc)

    # Delete existing chunks
    await db.execute(delete(Chunk).where(Chunk.document_id == doc.id))
    await db.flush()

    # Re-chunk and re-embed
    await chunk_and_embed(
        db, doc, body.content, settings.chunk_size, settings.chunk_overlap
    )

    return doc


@router.get("", response_model=PaginatedDocuments)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedDocuments:
    total = await db.scalar(select(func.count(Document.id)))
    offset = (page - 1) * page_size
    result = await db.scalars(
        select(Document)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    docs = result.all()
    return PaginatedDocuments(
        items=docs, total=total or 0, page=page, page_size=page_size
    )


@router.get("/{document_id}/file", response_model=None)
async def get_document_file(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> Response:
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.content is not None:
        return PlainTextResponse(doc.content, media_type=doc.content_type)

    raise HTTPException(status_code=404, detail="Document content not available")


@router.get("/{document_id}/chunks", response_model=list[ChunkResponse])
async def get_document_chunks(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[Chunk]:
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    result = await db.scalars(
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
    )
    return list(result.all())

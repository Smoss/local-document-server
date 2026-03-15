import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

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
    extract_text,
)
from doc_server.services.storage import save_file, save_text_content

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(file: UploadFile, db: Session = Depends(get_db)) -> Document:
    file_path, unique_name = await save_file(file, settings.upload_dir)

    text = extract_text(file_path, file.content_type or "application/octet-stream")

    doc = Document(
        filename=file.filename or unique_name,
        content_type=file.content_type or "application/octet-stream",
        file_path=file_path,
        content=text,
        status="ready",
    )
    await asyncio.to_thread(_persist_document, db, doc)

    if text:
        await chunk_and_embed(db, doc, text, settings.chunk_size, settings.chunk_overlap)

    return doc


@router.post("/text", response_model=DocumentResponse, status_code=201)
async def upload_text_document(
    body: TextDocumentRequest, db: Session = Depends(get_db)
) -> Document:
    file_path, unique_name = save_text_content(
        body.content, body.filename, settings.upload_dir
    )

    doc = Document(
        filename=body.filename,
        content_type=body.content_type,
        file_path=file_path,
        content=body.content,
        status="ready",
    )
    await asyncio.to_thread(_persist_document, db, doc)

    await chunk_and_embed(
        db, doc, body.content, settings.chunk_size, settings.chunk_overlap
    )

    return doc


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    body: UpdateDocumentRequest,
    db: Session = Depends(get_db),
) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.content = body.content
    if body.filename:
        doc.filename = body.filename
    doc.updated_at = datetime.now(timezone.utc)

    # Delete existing chunks
    db.query(Chunk).filter(Chunk.document_id == doc.id).delete()
    db.flush()

    # Re-chunk and re-embed
    await chunk_and_embed(
        db, doc, body.content, settings.chunk_size, settings.chunk_overlap
    )

    return doc


@router.get("", response_model=PaginatedDocuments)
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedDocuments:
    total = db.scalar(select(func.count(Document.id)))
    offset = (page - 1) * page_size
    docs = db.scalars(
        select(Document)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(page_size)
    ).all()
    return PaginatedDocuments(
        items=docs, total=total or 0, page=page, page_size=page_size
    )


@router.get("/{document_id}/file", response_model=None)
def get_document_file(
    document_id: uuid.UUID, db: Session = Depends(get_db)
) -> Response:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.file_path:
        return FileResponse(
            doc.file_path, media_type=doc.content_type, filename=doc.filename
        )

    if doc.content is not None:
        return PlainTextResponse(doc.content, media_type=doc.content_type)

    raise HTTPException(status_code=404, detail="Document content not available")


@router.get("/{document_id}/chunks", response_model=list[ChunkResponse])
def get_document_chunks(
    document_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[Chunk]:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = db.scalars(
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
    ).all()
    return list(chunks)

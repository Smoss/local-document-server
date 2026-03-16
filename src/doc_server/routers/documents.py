import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse, Response
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
from doc_server.services.chunking import chunk_and_embed
from doc_server.stores import chunk_store, document_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile, db: AsyncSession = Depends(get_db)
) -> Document:
    content_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "unnamed"
    logger.info(
        "Uploading file '%s' (%s, %d bytes)", filename, content_type, len(content_bytes)
    )

    text: str | None = None
    if content_type.startswith("text/"):
        text = content_bytes.decode("utf-8")

    doc = Document(
        filename=filename,
        content_type=content_type,
        content=text,
        status="ready",
    )
    await document_store.create_document(db, doc)

    if text:
        await chunk_and_embed(
            db, doc, text, settings.chunk_size, settings.chunk_overlap
        )

    logger.info("Created document %s (status=%s)", doc.id, doc.status)
    return doc


@router.post("/text", response_model=DocumentResponse, status_code=201)
async def upload_text_document(
    body: TextDocumentRequest, db: AsyncSession = Depends(get_db)
) -> Document:
    logger.info(
        "Uploading text document '%s' (%d chars)", body.filename, len(body.content)
    )

    doc = Document(
        filename=body.filename,
        content_type=body.content_type,
        content=body.content,
        status="ready",
    )
    await document_store.create_document(db, doc)

    await chunk_and_embed(
        db, doc, body.content, settings.chunk_size, settings.chunk_overlap
    )

    logger.info("Created text document %s (status=%s)", doc.id, doc.status)
    return doc


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    body: UpdateDocumentRequest,
    db: AsyncSession = Depends(get_db),
) -> Document:
    logger.info("Updating document %s", document_id)
    doc = await document_store.get_document(db, document_id)
    if not doc:
        logger.warning("Document %s not found for update", document_id)
        raise HTTPException(status_code=404, detail="Document not found")

    updates: dict = {"content": body.content}
    if body.filename:
        updates["filename"] = body.filename
    await document_store.update_document(db, doc, **updates)

    await chunk_store.delete_chunks_for_document(db, doc.id)

    await chunk_and_embed(
        db, doc, body.content, settings.chunk_size, settings.chunk_overlap
    )

    logger.info("Updated document %s (status=%s)", doc.id, doc.status)
    return doc


@router.get("", response_model=PaginatedDocuments)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedDocuments:
    logger.info("Listing documents (page=%d, page_size=%d)", page, page_size)
    offset = (page - 1) * page_size
    docs, total = await document_store.list_documents(db, offset, page_size)
    logger.info("Returning %d of %d documents", len(docs), total)
    return PaginatedDocuments(items=docs, total=total, page=page, page_size=page_size)


@router.get("/{document_id}/file", response_model=None)
async def get_document_file(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> Response:
    logger.info("Serving file for document %s", document_id)
    doc = await document_store.get_document(db, document_id)
    if not doc:
        logger.warning("Document %s not found", document_id)
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.content is not None:
        return PlainTextResponse(doc.content, media_type=doc.content_type)

    logger.warning("Document %s has no content", document_id)
    raise HTTPException(status_code=404, detail="Document content not available")


@router.get("/{document_id}/chunks", response_model=list[ChunkResponse])
async def get_document_chunks(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[Chunk]:
    logger.info("Fetching chunks for document %s", document_id)
    doc = await document_store.get_document(db, document_id)
    if not doc:
        logger.warning("Document %s not found", document_id)
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = await chunk_store.get_chunks_for_document(db, document_id)
    logger.info("Returning %d chunks for document %s", len(chunks), document_id)
    return chunks

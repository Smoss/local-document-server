import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
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
)
from doc_server.services.chunking import extract_text, split_into_chunks
from doc_server.services.embedding import OllamaEmbedder
from doc_server.services.storage import save_file, save_text_content

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


def _persist_document(db: Session, doc: Document) -> None:
    db.add(doc)
    db.flush()


def _save_chunks_and_commit(
    db: Session, doc: Document, chunks: list[Chunk], status: str
) -> None:
    for chunk in chunks:
        db.add(chunk)
    doc.status = status
    db.commit()
    db.refresh(doc)


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(file: UploadFile, db: Session = Depends(get_db)) -> Document:
    file_path, unique_name = await save_file(file, settings.upload_dir)

    doc = Document(
        filename=file.filename or unique_name,
        content_type=file.content_type or "application/octet-stream",
        file_path=file_path,
        status="ready",
    )
    await asyncio.to_thread(_persist_document, db, doc)

    # Extract text and create chunks
    text = extract_text(file_path, doc.content_type)
    chunks: list[Chunk] = []
    status = "ready"
    if text:
        chunk_texts = split_into_chunks(
            text, settings.chunk_size, settings.chunk_overlap
        )
        embedder = OllamaEmbedder()
        try:
            embeddings = await embedder.embed_batch(chunk_texts)
            for i, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
                chunks.append(
                    Chunk(
                        document_id=doc.id,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=embedding,
                    )
                )
            status = "embedded"
        except Exception:
            logger.info("Ollama unavailable, storing chunks without embeddings")
            for i, chunk_text in enumerate(chunk_texts):
                chunks.append(
                    Chunk(
                        document_id=doc.id,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=None,
                    )
                )
            status = "pending_embedding"
        finally:
            await embedder.close()

    await asyncio.to_thread(_save_chunks_and_commit, db, doc, chunks, status)
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
        status="ready",
    )
    await asyncio.to_thread(_persist_document, db, doc)

    chunks: list[Chunk] = []
    status = "ready"
    chunk_texts = split_into_chunks(
        body.content, settings.chunk_size, settings.chunk_overlap
    )
    if chunk_texts:
        embedder = OllamaEmbedder()
        try:
            embeddings = await embedder.embed_batch(chunk_texts)
            for i, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
                chunks.append(
                    Chunk(
                        document_id=doc.id,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=embedding,
                    )
                )
            status = "embedded"
        except Exception:
            logger.info("Ollama unavailable, storing chunks without embeddings")
            for i, chunk_text in enumerate(chunk_texts):
                chunks.append(
                    Chunk(
                        document_id=doc.id,
                        chunk_index=i,
                        content=chunk_text,
                        embedding=None,
                    )
                )
            status = "pending_embedding"
        finally:
            await embedder.close()

    await asyncio.to_thread(_save_chunks_and_commit, db, doc, chunks, status)
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


@router.get("/{document_id}/file")
def get_document_file(
    document_id: uuid.UUID, db: Session = Depends(get_db)
) -> FileResponse:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(
        doc.file_path, media_type=doc.content_type, filename=doc.filename
    )


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

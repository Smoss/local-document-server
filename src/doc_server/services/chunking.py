import asyncio
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from doc_server.models import Chunk, Document
from doc_server.services.embedding import OllamaEmbedder

logger = logging.getLogger(__name__)


def extract_text(file_path: str, content_type: str) -> str | None:
    if not content_type.startswith("text/"):
        return None
    return Path(file_path).read_text(encoding="utf-8")


def split_into_chunks(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap

    return chunks


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


async def chunk_and_embed(
    db: Session, doc: Document, text: str, chunk_size: int, chunk_overlap: int
) -> str:
    """Split text into chunks, embed via Ollama, and persist."""
    chunk_texts = split_into_chunks(text, chunk_size, chunk_overlap)
    chunks: list[Chunk] = []
    status = "ready"

    if chunk_texts:
        embedder = OllamaEmbedder()
        try:
            embeddings = await embedder.embed_batch(chunk_texts)
            for i, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
                chunks.append(
                    Chunk(
                        document_id=doc.id,
                        chunk_index=i,
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
                        embedding=None,
                    )
                )
            status = "pending_embedding"
        finally:
            await embedder.close()

    await asyncio.to_thread(_save_chunks_and_commit, db, doc, chunks, status)
    return status

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from doc_server.models import Chunk, Document
from doc_server.services.embedding import OllamaEmbedder
from doc_server.stores import chunk_store, document_store

logger = logging.getLogger(__name__)


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


async def chunk_and_embed(
    db: AsyncSession, doc: Document, text: str, chunk_size: int, chunk_overlap: int
) -> str:
    """Split text into chunks, embed via Ollama, and persist."""
    chunk_texts = split_into_chunks(text, chunk_size, chunk_overlap)
    logger.info(
        f"Split document {doc.id} into {len(chunk_texts)} chunk(s) "
        "(chunk_size={chunk_size}, overlap={chunk_overlap})"
    )
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
            logger.info(f"Embedded {len(chunks)} chunk(s) for document {doc.id}")
        except Exception:
            logger.warning(
                f"Ollama unavailable, storing {len(chunk_texts)} chunk(s) "
                "without embeddings for document {doc.id}"
            )
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

    await chunk_store.save_chunks(db, chunks)
    await document_store.update_document(db, doc, status=status)
    await document_store.commit_and_refresh(db, doc)
    logger.info(f"Persisted document {doc.id} with status '{status}'")
    return status

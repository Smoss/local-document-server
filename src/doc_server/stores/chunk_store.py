import uuid

from sqlalchemy import delete, select
from sqlalchemy import func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from doc_server.models import Chunk, Document


async def save_chunks(db: AsyncSession, chunks: list[Chunk]) -> None:
    for chunk in chunks:
        db.add(chunk)
    await db.flush()


async def delete_chunks_for_document(db: AsyncSession, document_id: uuid.UUID) -> None:
    await db.execute(delete(Chunk).where(Chunk.document_id == document_id))
    await db.flush()


async def get_chunks_for_document(
    db: AsyncSession, document_id: uuid.UUID
) -> list[Chunk]:
    result = await db.scalars(
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
    )
    return list(result.all())


async def search_similar_chunks(
    db: AsyncSession,
    query_embedding: list[float],
    threshold: float,
    max_results: int,
) -> list[tuple[Chunk, Document, float]]:
    distance_expr = Chunk.embedding.cosine_distance(query_embedding)
    distance = distance_expr.label("distance")

    best_per_doc = (
        select(
            Chunk.document_id,
            sa_func.min(distance_expr).label("best_distance"),
        )
        .where(Chunk.embedding.isnot(None))
        .where(distance_expr <= (1 - threshold))
        .group_by(Chunk.document_id)
        .order_by(sa_func.min(distance_expr))
        .limit(max_results)
        .subquery()
    )

    stmt = (
        select(Chunk, Document, distance)
        .join(Document, Chunk.document_id == Document.id)
        .join(best_per_doc, Document.id == best_per_doc.c.document_id)
        .where(Chunk.embedding.isnot(None))
        .where(distance_expr <= (1 - threshold))
        .order_by(best_per_doc.c.best_distance, distance)
    )

    result = await db.execute(stmt)
    return result.all()  # type: ignore[return-value]

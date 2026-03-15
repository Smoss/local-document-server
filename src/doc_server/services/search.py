from collections import OrderedDict
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from doc_server.models import Chunk, Document


def search_chunks(
    db: Session,
    query_embedding: list[float],
    threshold: float,
    max_results: int,
) -> list[dict[str, Any]]:
    distance_expr = Chunk.embedding.cosine_distance(query_embedding)
    distance = distance_expr.label("distance")

    # Subquery: best (minimum) distance per document, limited to top K documents
    best_per_doc = (
        select(
            Chunk.document_id,
            func.min(distance_expr).label("best_distance"),
        )
        .where(Chunk.embedding.isnot(None))
        .where(distance_expr <= (1 - threshold))
        .group_by(Chunk.document_id)
        .order_by(func.min(distance_expr))
        .limit(max_results)
        .subquery()
    )

    # Get all matching chunks for the top K documents
    stmt = (
        select(Chunk, Document, distance)
        .join(Document, Chunk.document_id == Document.id)
        .join(best_per_doc, Document.id == best_per_doc.c.document_id)
        .where(Chunk.embedding.isnot(None))
        .where(distance_expr <= (1 - threshold))
        .order_by(best_per_doc.c.best_distance, distance)
    )

    results = db.execute(stmt).all()

    # Group by document, preserving order of best match
    grouped: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for chunk, document, dist in results:
        score = 1 - dist
        doc_id = str(document.id)
        if doc_id not in grouped:
            grouped[doc_id] = {
                "document_id": doc_id,
                "filename": document.filename,
                "content_type": document.content_type,
                "content": document.content,
                "status": document.status,
                "created_at": document.created_at.isoformat(),
                "chunks": [],
            }
        grouped[doc_id]["chunks"].append(
            {
                "chunk_id": str(chunk.id),
                "chunk_index": chunk.chunk_index,
                "relevance_score": round(score, 4),
            }
        )

    return list(grouped.values())

from collections import OrderedDict
from typing import Any

from sqlalchemy import select
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
    stmt = (
        select(Chunk, Document, distance)
        .join(Document, Chunk.document_id == Document.id)
        .where(Chunk.embedding.isnot(None))
        .where(distance_expr <= (1 - threshold))
        .order_by(distance)
        .limit(max_results)
    )

    results = db.execute(stmt).all()

    # Group by document, preserving order of first appearance
    grouped: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for chunk, document, dist in results:
        score = 1 - dist
        doc_id = str(document.id)
        if doc_id not in grouped:
            grouped[doc_id] = {
                "document_id": doc_id,
                "filename": document.filename,
                "content_type": document.content_type,
                "status": document.status,
                "created_at": document.created_at.isoformat(),
                "chunks": [],
            }
        grouped[doc_id]["chunks"].append(
            {
                "chunk_id": str(chunk.id),
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "relevance_score": round(score, 4),
            }
        )

    return list(grouped.values())

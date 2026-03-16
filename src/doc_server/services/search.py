from collections import OrderedDict
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from doc_server.stores import chunk_store


async def search_documents(
    db: AsyncSession,
    query_embedding: list[float],
    threshold: float,
    max_results: int,
) -> list[dict[str, Any]]:
    results = await chunk_store.search_similar_chunks(
        db, query_embedding, threshold, max_results
    )

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

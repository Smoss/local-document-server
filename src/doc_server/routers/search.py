from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from doc_server.config import settings
from doc_server.database import get_db
from doc_server.schemas import SearchRequest, SearchResponse
from doc_server.services.embedding import OllamaEmbedder
from doc_server.services.search import search_documents

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest, db: AsyncSession = Depends(get_db)
) -> SearchResponse:
    embedder = OllamaEmbedder()
    try:
        if not await embedder.is_available():
            raise HTTPException(status_code=503, detail="Embedding service unavailable")

        query_embedding = await embedder.embed(request.query)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Embedding service unavailable")
    finally:
        await embedder.close()

    max_results = request.max_results or settings.search_max_results
    results = await search_documents(
        db,
        query_embedding,
        settings.search_similarity_threshold,
        max_results,
    )
    return SearchResponse(query=request.query, results=results)

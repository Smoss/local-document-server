import io
import random
from unittest.mock import AsyncMock, patch

import pytest

from doc_server.models import Chunk, Document


def _make_vector(seed: int) -> list[float]:
    rng = random.Random(seed)
    return [rng.random() for _ in range(768)]


@pytest.mark.asyncio
async def test_search_returns_ranked_results(client, db_session):
    # Create a doc with embedded chunks directly
    doc = Document(
        filename="search.txt",
        content_type="text/plain",
        file_path="/tmp/s.txt",
        status="embedded",
    )
    db_session.add(doc)
    db_session.flush()

    for i in range(3):
        chunk = Chunk(
            document_id=doc.id,
            chunk_index=i,
            content=f"chunk {i} content",
            embedding=_make_vector(i),
        )
        db_session.add(chunk)
    db_session.commit()

    query_vector = _make_vector(1)  # Should be most similar to chunk 1

    with patch("doc_server.routers.search.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.is_available = AsyncMock(return_value=True)
        instance.embed = AsyncMock(return_value=query_vector)
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        response = await client.post("/api/search", json={"query": "test query"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) > 0
    # First result's first chunk should have highest relevance
    first_doc = data["results"][0]
    assert first_doc["chunks"][0]["relevance_score"] >= 0.99


@pytest.mark.asyncio
async def test_search_empty_results(client, db_session):
    # No documents in db, search should return empty
    query_vector = _make_vector(42)

    with patch("doc_server.routers.search.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.is_available = AsyncMock(return_value=True)
        instance.embed = AsyncMock(return_value=query_vector)
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        response = await client.post("/api/search", json={"query": "nothing"})

    assert response.status_code == 200
    assert response.json()["results"] == []


@pytest.mark.asyncio
async def test_search_includes_metadata(client, db_session):
    doc = Document(
        filename="meta.txt",
        content_type="text/plain",
        file_path="/tmp/m.txt",
        status="embedded",
    )
    db_session.add(doc)
    db_session.flush()

    vec = _make_vector(99)
    chunk = Chunk(
        document_id=doc.id, chunk_index=0, content="metadata chunk", embedding=vec
    )
    db_session.add(chunk)
    db_session.commit()

    with patch("doc_server.routers.search.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.is_available = AsyncMock(return_value=True)
        instance.embed = AsyncMock(return_value=vec)
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        response = await client.post("/api/search", json={"query": "meta"})

    data = response.json()
    assert len(data["results"]) > 0
    result = data["results"][0]
    assert result["filename"] == "meta.txt"
    assert result["content_type"] == "text/plain"
    assert "created_at" in result


@pytest.mark.asyncio
async def test_search_grouped_by_document(client, db_session):
    doc = Document(
        filename="grouped.txt",
        content_type="text/plain",
        file_path="/tmp/g.txt",
        status="embedded",
    )
    db_session.add(doc)
    db_session.flush()

    vec = _make_vector(50)
    for i in range(3):
        chunk = Chunk(
            document_id=doc.id, chunk_index=i, content=f"group chunk {i}", embedding=vec
        )
        db_session.add(chunk)
    db_session.commit()

    with patch("doc_server.routers.search.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.is_available = AsyncMock(return_value=True)
        instance.embed = AsyncMock(return_value=vec)
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        response = await client.post("/api/search", json={"query": "group"})

    data = response.json()
    # All chunks from same doc should be grouped under one result
    doc_ids = [r["document_id"] for r in data["results"]]
    assert len(doc_ids) == len(set(doc_ids))  # No duplicate docs


@pytest.mark.asyncio
async def test_get_document_chunks(client, db_session):
    with patch("doc_server.routers.documents.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("no ollama"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        response = await client.post(
            "/api/documents",
            files={
                "file": (
                    "chunks.txt",
                    io.BytesIO(b"hello world this is a test"),
                    "text/plain",
                )
            },
        )
    doc_id = response.json()["id"]
    response = await client.get(f"/api/documents/{doc_id}/chunks")
    assert response.status_code == 200
    chunks = response.json()
    assert len(chunks) > 0
    assert chunks[0]["chunk_index"] == 0

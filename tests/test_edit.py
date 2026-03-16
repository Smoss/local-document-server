import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from doc_server.models import Chunk


# @TestID 7aa136c8-f059-4597-aa94-40929940ae05
# @SystemName Document API
# @TestType Integration
# @TestDescription PUT new content returns updated content and updated_at
@pytest.mark.asyncio
async def test_update_document_replaces_content(client):
    with patch("doc_server.services.chunking.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("no ollama"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        # Create a document first
        create_resp = await client.post(
            "/api/documents/text",
            json={
                "content": "original content here",
                "filename": "edit-test.txt",
            },
        )
        assert create_resp.status_code == 201
        doc_id = create_resp.json()["id"]

        # Update the document
        update_resp = await client.put(
            f"/api/documents/{doc_id}",
            json={"content": "updated content here"},
        )

    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["content"] == "updated content here"
    assert data["updated_at"] is not None


# @TestID 799d90e7-6cb9-41a4-ac76-828a5993b3ea
# @SystemName Document API
# @TestType Integration
# @TestDescription PUT new content replaces old chunks with new ones
@pytest.mark.asyncio
async def test_update_document_rechunks(client, db_session):
    with patch("doc_server.services.chunking.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("no ollama"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        # Create a document
        create_resp = await client.post(
            "/api/documents/text",
            json={
                "content": "word " * 100,
                "filename": "chunk-test.txt",
            },
        )
        doc_id = create_resp.json()["id"]

        # Get original chunks
        result = await db_session.scalars(
            select(Chunk).where(Chunk.document_id == doc_id)
        )
        old_chunks = result.all()
        old_chunk_ids = {str(c.id) for c in old_chunks}

        # Update with different content
        await client.put(
            f"/api/documents/{doc_id}",
            json={"content": "completely different text"},
        )

    # Verify old chunks are gone and new ones exist
    result = await db_session.scalars(select(Chunk).where(Chunk.document_id == doc_id))
    new_chunks = result.all()
    new_chunk_ids = {str(c.id) for c in new_chunks}
    assert old_chunk_ids.isdisjoint(new_chunk_ids)
    assert len(new_chunks) > 0
    assert new_chunks[0].chunk_index == 0


# @TestID 44abee18-b671-48f9-b0a9-48a17e0e2663
# @SystemName Document API
# @TestType Integration
# @TestDescription PUT to nonexistent UUID returns 404
@pytest.mark.asyncio
async def test_update_document_404(client):
    fake_id = str(uuid.uuid4())
    response = await client.put(
        f"/api/documents/{fake_id}",
        json={"content": "does not matter"},
    )
    assert response.status_code == 404


# @TestID 46d3bd15-dc1d-4bf9-85ef-1d9d597208cb
# @SystemName Document API
# @TestType Integration
# @TestDescription Mock Ollama to fail, verify status is pending_embedding after update
@pytest.mark.asyncio
async def test_update_document_pending_embedding(client):
    with patch("doc_server.services.chunking.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("no ollama"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        # Create a document
        create_resp = await client.post(
            "/api/documents/text",
            json={
                "content": "some content",
                "filename": "embed-test.txt",
            },
        )
        doc_id = create_resp.json()["id"]

        # Update it (Ollama still failing)
        update_resp = await client.put(
            f"/api/documents/{doc_id}",
            json={"content": "new content for embedding test"},
        )

    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "pending_embedding"

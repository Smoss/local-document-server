import io
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_document_file(client):
    with patch("doc_server.routers.documents.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("no ollama"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        upload = await client.post(
            "/api/documents",
            files={"file": ("serve.txt", io.BytesIO(b"serve content"), "text/plain")},
        )
    doc_id = upload.json()["id"]
    response = await client.get(f"/api/documents/{doc_id}/file")
    assert response.status_code == 200
    assert response.content == b"serve content"


@pytest.mark.asyncio
async def test_get_nonexistent_document(client):
    import uuid
    response = await client.get(f"/api/documents/{uuid.uuid4()}/file")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_documents_empty(client):
    response = await client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_documents_paginated(client):
    with patch("doc_server.routers.documents.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("no ollama"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        for i in range(3):
            await client.post(
                "/api/documents",
                files={"file": (f"page{i}.txt", io.BytesIO(f"content {i}".encode()), "text/plain")},
            )

    response = await client.get("/api/documents?page=1&page_size=2")
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2

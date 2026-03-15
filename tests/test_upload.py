import io
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_upload_file_success(client):
    with patch("doc_server.services.chunking.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("no ollama"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        response = await client.post(
            "/api/documents",
            files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["content_type"] == "text/plain"
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_missing_file(client):
    response = await client.post("/api/documents")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_duplicate_filename(client):
    with patch("doc_server.services.chunking.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("no ollama"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        file_data = io.BytesIO(b"content one")
        r1 = await client.post(
            "/api/documents",
            files={"file": ("dup.txt", file_data, "text/plain")},
        )
        file_data2 = io.BytesIO(b"content two")
        r2 = await client.post(
            "/api/documents",
            files={"file": ("dup.txt", file_data2, "text/plain")},
        )
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]


@pytest.mark.asyncio
async def test_upload_persists_metadata(client, db_session):
    with patch("doc_server.services.chunking.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("no ollama"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        response = await client.post(
            "/api/documents",
            files={"file": ("meta.txt", io.BytesIO(b"metadata test"), "text/plain")},
        )
    data = response.json()

    from doc_server.models import Document

    doc = db_session.get(Document, data["id"])
    assert doc is not None
    assert doc.filename == "meta.txt"

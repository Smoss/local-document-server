import io
from unittest.mock import AsyncMock, patch

import pytest

from doc_server.models import Document


# @TestID 2897fd56-c0ae-4513-8315-66a2e0f8e105
# @SystemName Document API
# @TestType Integration
# @TestDescription Upload a text file and verify 201 response with correct metadata
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


# @TestID 53d8fb3f-2354-47a1-b48d-e958adef4316
# @SystemName Document API
# @TestType Integration
# @TestDescription POST /documents without a file returns 422
@pytest.mark.asyncio
async def test_upload_missing_file(client):
    response = await client.post("/api/documents")
    assert response.status_code == 422


# @TestID 4351a0a9-e6fa-4e6a-b2ea-4a4f6c7a7a4e
# @SystemName Document API
# @TestType Integration
# @TestDescription Uploading two files with the same name creates two distinct documents
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


# @TestID d366805e-3501-43e8-b408-36324e22ac51
# @SystemName Document API
# @TestType Integration
# @TestDescription Uploaded document metadata is persisted correctly in the database
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

    doc = await db_session.get(Document, data["id"])
    assert doc is not None
    assert doc.filename == "meta.txt"

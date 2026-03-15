import io
from unittest.mock import AsyncMock, patch

import pytest

from doc_server.services.chunking import extract_text, split_into_chunks


# @TestID 55dcc489-1f28-4c7e-a695-9adc56fba14c
# @SystemName Document API
# @TestType Unit
# @TestDescription Verify extract_text reads text/plain files correctly
def test_text_extraction(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello, world!")
    assert extract_text(str(f), "text/plain") == "Hello, world!"


# @TestID 55fde55d-d102-4354-8d7c-3d80257fef37
# @SystemName Document API
# @TestType Unit
# @TestDescription Verify extract_text returns None for non-text content types
def test_text_extraction_non_text(tmp_path):
    f = tmp_path / "test.bin"
    f.write_bytes(b"\x00\x01\x02")
    assert extract_text(str(f), "application/octet-stream") is None


# @TestID 734ea94f-454c-4ed1-aaef-ca36904c3e89
# @SystemName Document API
# @TestType Unit
# @TestDescription Verify split_into_chunks produces correctly sized chunks
def test_chunk_splitting():
    words = " ".join(f"word{i}" for i in range(100))
    chunks = split_into_chunks(words, chunk_size=30, overlap=5)
    assert len(chunks) > 1
    # Each chunk should have at most 30 words
    for chunk in chunks:
        assert len(chunk.split()) <= 30


# @TestID 99a4f5a2-04e7-4819-b08d-fe8e72aea28f
# @SystemName Document API
# @TestType Unit
# @TestDescription Verify chunk overlap preserves expected words between chunks
def test_chunk_overlap_content():
    words = " ".join(f"w{i}" for i in range(20))
    chunks = split_into_chunks(words, chunk_size=10, overlap=3)
    assert len(chunks) == 3
    first_words = chunks[0].split()
    second_words = chunks[1].split()
    # Last 3 words of first chunk should be first 3 of second
    assert first_words[-3:] == second_words[:3]


# @TestID 381ef3b6-830d-4c04-ab78-e9b874d87618
# @SystemName Document API
# @TestType Integration
# @TestDescription Upload a text file and verify chunks are created in the database
@pytest.mark.asyncio
async def test_upload_triggers_chunking(client, db_session):
    words = " ".join(f"word{i}" for i in range(50))
    with patch("doc_server.services.chunking.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("no ollama"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        response = await client.post(
            "/api/documents",
            files={"file": ("chunk.txt", io.BytesIO(words.encode()), "text/plain")},
        )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    from sqlalchemy import select

    from doc_server.models import Chunk

    chunks = db_session.scalars(
        select(Chunk).where(Chunk.document_id == doc_id).order_by(Chunk.chunk_index)
    ).all()
    assert len(chunks) > 0
    assert chunks[0].chunk_index == 0


# @TestID da04f4b6-ac13-4afa-a9db-94e55cb739e2
# @SystemName Document API
# @TestType Integration
# @TestDescription Upload when Ollama is unavailable results in pending_embedding status
@pytest.mark.asyncio
async def test_upload_ollama_unavailable(client):
    with patch("doc_server.services.chunking.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("Connection refused"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        response = await client.post(
            "/api/documents",
            files={
                "file": ("noembed.txt", io.BytesIO(b"some text here"), "text/plain")
            },
        )
    assert response.status_code == 201
    assert response.json()["status"] == "pending_embedding"

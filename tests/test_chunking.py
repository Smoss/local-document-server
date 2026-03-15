import io
from unittest.mock import AsyncMock, patch

import pytest

from doc_server.services.chunking import extract_text, split_into_chunks


def test_text_extraction(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello, world!")
    assert extract_text(str(f), "text/plain") == "Hello, world!"


def test_text_extraction_non_text(tmp_path):
    f = tmp_path / "test.bin"
    f.write_bytes(b"\x00\x01\x02")
    assert extract_text(str(f), "application/octet-stream") is None


def test_chunk_splitting():
    words = " ".join(f"word{i}" for i in range(100))
    chunks = split_into_chunks(words, chunk_size=30, overlap=5)
    assert len(chunks) > 1
    # Each chunk should have at most 30 words
    for chunk in chunks:
        assert len(chunk.split()) <= 30


def test_chunk_overlap_content():
    words = " ".join(f"w{i}" for i in range(20))
    chunks = split_into_chunks(words, chunk_size=10, overlap=3)
    assert len(chunks) == 3
    first_words = chunks[0].split()
    second_words = chunks[1].split()
    # Last 3 words of first chunk should be first 3 of second
    assert first_words[-3:] == second_words[:3]


@pytest.mark.asyncio
async def test_upload_triggers_chunking(client, db_session):
    words = " ".join(f"word{i}" for i in range(50))
    with patch("doc_server.routers.documents.OllamaEmbedder") as MockEmbedder:
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

    from doc_server.models import Chunk
    from sqlalchemy import select
    chunks = db_session.scalars(
        select(Chunk).where(Chunk.document_id == doc_id).order_by(Chunk.chunk_index)
    ).all()
    assert len(chunks) > 0
    assert chunks[0].content.startswith("word0")


@pytest.mark.asyncio
async def test_upload_ollama_unavailable(client):
    with patch("doc_server.routers.documents.OllamaEmbedder") as MockEmbedder:
        instance = AsyncMock()
        instance.embed_batch = AsyncMock(side_effect=Exception("Connection refused"))
        instance.close = AsyncMock()
        MockEmbedder.return_value = instance

        response = await client.post(
            "/api/documents",
            files={"file": ("noembed.txt", io.BytesIO(b"some text here"), "text/plain")},
        )
    assert response.status_code == 201
    assert response.json()["status"] == "pending_embedding"

import random

import pytest
from sqlalchemy import select, text

from doc_server.models import Chunk, Document


def _make_vector(seed: int) -> list[float]:
    rng = random.Random(seed)
    return [rng.random() for _ in range(768)]


# @TestID 40ed67fa-7499-4afc-922f-0b2611f5bf1a
# @SystemName Document Store
# @TestType Integration
# @TestDescription Verify the pgvector extension is installed in the test database
def test_pgvector_extension_installed(db_engine):
    with db_engine.connect() as conn:
        result = conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        assert result.scalar() == "vector"


# @TestID 3c3bcfd4-5a54-4c74-ae18-703e5ac7defa
# @SystemName Document Store
# @TestType Integration
# @TestDescription Store a vector in a chunk and verify it round-trips correctly
@pytest.mark.asyncio
async def test_vector_column_stores_correctly(db_session):
    doc = Document(
        filename="vec.txt",
        content_type="text/plain",
        status="embedded",
    )
    db_session.add(doc)
    await db_session.flush()

    vec = _make_vector(1)
    chunk = Chunk(document_id=doc.id, chunk_index=0, embedding=vec)
    db_session.add(chunk)
    await db_session.flush()

    loaded = await db_session.get(Chunk, chunk.id)
    assert loaded is not None
    assert len(loaded.embedding) == 768
    assert abs(loaded.embedding[0] - vec[0]) < 1e-5


# @TestID b948de95-398f-444b-86f4-780b3d0a2f43
# @SystemName Document Store
# @TestType Integration
# @TestDescription Query by cosine distance and verify the closest vector ranks first
@pytest.mark.asyncio
async def test_cosine_similarity_query(db_session):
    doc = Document(
        filename="cos.txt",
        content_type="text/plain",
        status="embedded",
    )
    db_session.add(doc)
    await db_session.flush()

    vec_a = _make_vector(10)
    vec_b = _make_vector(20)
    chunk_a = Chunk(document_id=doc.id, chunk_index=0, embedding=vec_a)
    chunk_b = Chunk(document_id=doc.id, chunk_index=1, embedding=vec_b)
    db_session.add_all([chunk_a, chunk_b])
    await db_session.flush()

    # Query with vec_a — chunk_a should be closest
    distance = Chunk.embedding.cosine_distance(vec_a).label("distance")
    result = await db_session.execute(
        select(Chunk, distance).where(Chunk.embedding.isnot(None)).order_by(distance)
    )
    results = result.all()

    assert len(results) >= 2
    assert results[0][0].id == chunk_a.id
    assert results[0][1] < 0.01  # Near-zero distance for same vector


# @TestID dceb44c3-a0d9-4687-97f5-0a877a781801
# @SystemName Document Store
# @TestType Integration
# @TestDescription Verify chunks with null embeddings are excluded from vector queries
@pytest.mark.asyncio
async def test_null_embedding_excluded(db_session):
    doc = Document(
        filename="null.txt",
        content_type="text/plain",
        status="pending_embedding",
    )
    db_session.add(doc)
    await db_session.flush()

    chunk_with = Chunk(
        document_id=doc.id,
        chunk_index=0,
        embedding=_make_vector(5),
    )
    chunk_without = Chunk(document_id=doc.id, chunk_index=1, embedding=None)
    db_session.add_all([chunk_with, chunk_without])
    await db_session.flush()

    result = await db_session.scalars(
        select(Chunk).where(Chunk.embedding.isnot(None))
    )
    results = result.all()

    chunk_ids = [c.id for c in results]
    assert chunk_with.id in chunk_ids
    assert chunk_without.id not in chunk_ids

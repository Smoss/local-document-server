import random

from sqlalchemy import select, text

from doc_server.models import Chunk, Document


def _make_vector(seed: int) -> list[float]:
    rng = random.Random(seed)
    return [rng.random() for _ in range(768)]


def test_pgvector_extension_installed(db_engine):
    with db_engine.connect() as conn:
        result = conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        assert result.scalar() == "vector"


def test_vector_column_stores_correctly(db_session):
    doc = Document(
        filename="vec.txt",
        content_type="text/plain",
        file_path="/tmp/v.txt",
        status="embedded",
    )
    db_session.add(doc)
    db_session.flush()

    vec = _make_vector(1)
    chunk = Chunk(document_id=doc.id, chunk_index=0, content="test", embedding=vec)
    db_session.add(chunk)
    db_session.flush()

    loaded = db_session.get(Chunk, chunk.id)
    assert loaded is not None
    assert len(loaded.embedding) == 768
    assert abs(loaded.embedding[0] - vec[0]) < 1e-5


def test_cosine_similarity_query(db_session):
    doc = Document(
        filename="cos.txt",
        content_type="text/plain",
        file_path="/tmp/c.txt",
        status="embedded",
    )
    db_session.add(doc)
    db_session.flush()

    vec_a = _make_vector(10)
    vec_b = _make_vector(20)
    chunk_a = Chunk(
        document_id=doc.id, chunk_index=0, content="chunk a", embedding=vec_a
    )
    chunk_b = Chunk(
        document_id=doc.id, chunk_index=1, content="chunk b", embedding=vec_b
    )
    db_session.add_all([chunk_a, chunk_b])
    db_session.flush()

    # Query with vec_a — chunk_a should be closest
    distance = Chunk.embedding.cosine_distance(vec_a).label("distance")
    results = db_session.execute(
        select(Chunk, distance).where(Chunk.embedding.isnot(None)).order_by(distance)
    ).all()

    assert len(results) >= 2
    assert results[0][0].id == chunk_a.id
    assert results[0][1] < 0.01  # Near-zero distance for same vector


def test_null_embedding_excluded(db_session):
    doc = Document(
        filename="null.txt",
        content_type="text/plain",
        file_path="/tmp/n.txt",
        status="pending_embedding",
    )
    db_session.add(doc)
    db_session.flush()

    chunk_with = Chunk(
        document_id=doc.id,
        chunk_index=0,
        content="has embedding",
        embedding=_make_vector(5),
    )
    chunk_without = Chunk(
        document_id=doc.id, chunk_index=1, content="no embedding", embedding=None
    )
    db_session.add_all([chunk_with, chunk_without])
    db_session.flush()

    results = db_session.scalars(select(Chunk).where(Chunk.embedding.isnot(None))).all()

    chunk_ids = [c.id for c in results]
    assert chunk_with.id in chunk_ids
    assert chunk_without.id not in chunk_ids

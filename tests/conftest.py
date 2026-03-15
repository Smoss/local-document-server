import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Override settings before importing app modules
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://docserver:docserver@localhost:7730/docserver_test"
)

from doc_server.database import get_db
from doc_server.main import app
from doc_server.models import Base

TEST_DB_URL = "postgresql+psycopg://docserver:docserver@localhost:7730/docserver_test"


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DB_URL)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def tmp_storage(tmp_path) -> Path:
    storage = tmp_path / "storage"
    storage.mkdir()
    return storage


@pytest.fixture
async def client(db_session, tmp_storage) -> AsyncClient:
    from doc_server.config import settings

    settings.upload_dir = str(tmp_storage)
    settings.database_url = TEST_DB_URL

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_embedder():
    """Returns a mock embedder that produces deterministic 768-dim vectors."""
    embedder = AsyncMock()

    def make_vector(text: str) -> list[float]:
        """Deterministic vector based on text hash."""
        h = hash(text) % (2**32)
        import random

        rng = random.Random(h)
        return [rng.random() for _ in range(768)]

    async def embed(text: str) -> list[float]:
        return make_vector(text)

    async def embed_batch(texts: list[str]) -> list[list[float]]:
        return [make_vector(t) for t in texts]

    embedder.embed = embed
    embedder.embed_batch = embed_batch
    embedder.is_available = AsyncMock(return_value=True)
    embedder.close = AsyncMock()

    return embedder

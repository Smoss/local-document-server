import os
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Override settings before importing app modules
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://docserver:docserver@localhost:7730/docserver_test"
)

from doc_server.database import get_db
from doc_server.main import app
from doc_server.models import Base

TEST_DB_URL = "postgresql+psycopg://docserver:docserver@localhost:7730/docserver_test"


def _alembic_config() -> Config:
    ini_path = Path(__file__).resolve().parents[1] / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    return cfg


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DB_URL)
    # Drop existing tables and alembic version to ensure clean slate
    Base.metadata.drop_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
    command.upgrade(_alembic_config(), "head")
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_engine = create_async_engine(TEST_DB_URL)
    async with async_engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session
        await session.close()
        await trans.rollback()
    await async_engine.dispose()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    from doc_server.config import settings

    settings.database_url = TEST_DB_URL

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
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

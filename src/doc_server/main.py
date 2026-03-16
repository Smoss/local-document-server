import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from doc_server.config import settings
from doc_server.database import init_db
from doc_server.routers import documents, search


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    init_db()

    # Configure logging after init_db() because alembic's dictConfig
    # disables existing loggers and resets the root level.
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    ds_logger = logging.getLogger("doc_server")
    ds_logger.disabled = False
    ds_logger.setLevel(level)
    if not ds_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
        )
        ds_logger.addHandler(handler)
    ds_logger.propagate = False
    # Re-enable child loggers that dictConfig may have disabled
    for name in logging.Logger.manager.loggerDict:
        if name.startswith("doc_server."):
            lg = logging.getLogger(name)
            lg.disabled = False

    yield


app = FastAPI(title="Document Server", version="0.1.0", lifespan=lifespan)
app.include_router(documents.router)
app.include_router(search.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

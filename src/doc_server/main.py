from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from doc_server.config import settings
from doc_server.database import init_db
from doc_server.routers import documents, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(title="Document Server", version="0.1.0", lifespan=lifespan)
app.include_router(documents.router)
app.include_router(search.router)


@app.get("/health")
def health():
    return {"status": "ok"}

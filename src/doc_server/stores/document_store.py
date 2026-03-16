import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from doc_server.models import Document


async def get_document(db: AsyncSession, document_id: uuid.UUID) -> Document | None:
    return await db.get(Document, document_id)


async def create_document(db: AsyncSession, doc: Document) -> None:
    db.add(doc)
    await db.flush()


async def update_document(db: AsyncSession, doc: Document, **kwargs: Any) -> None:
    for key, value in kwargs.items():
        setattr(doc, key, value)
    if "updated_at" not in kwargs:
        doc.updated_at = datetime.now(timezone.utc)
    await db.flush()


async def list_documents(
    db: AsyncSession, offset: int, limit: int
) -> tuple[list[Document], int]:
    total = await db.scalar(select(func.count(Document.id)))
    result = await db.scalars(
        select(Document)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.all()), total or 0


async def commit_and_refresh(db: AsyncSession, doc: Document) -> None:
    await db.commit()
    await db.refresh(doc)

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.imports import CatalogImport


class ImportsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_job(self, data: dict) -> CatalogImport:
        record = CatalogImport(**data)
        self.session.add(record)
        await self.session.flush()
        return record

    async def create_record(self, data: dict) -> CatalogImport:
        return await self.create_job(data)

    async def update_status(self, import_id: uuid.UUID, status: str) -> CatalogImport | None:
        record = await self.get_import(import_id)
        if not record:
            return None
        record.status = status
        if status == "running" and not record.started_at:
            record.started_at = datetime.now(timezone.utc)
        if status in {"done", "failed"}:
            record.finished_at = datetime.now(timezone.utc)
        await self.session.flush()
        return record

    async def append_errors(self, import_id: uuid.UUID, errors: list[dict]) -> CatalogImport | None:
        record = await self.get_import(import_id)
        if not record:
            return None
        existing = list(record.errors or [])
        existing.extend(errors)
        record.errors = existing
        record.rows_invalid = len(existing)
        record.rows_valid = max(record.rows_total - record.rows_invalid, 0)
        await self.session.flush()
        return record

    async def finalize(
        self,
        import_id: uuid.UUID,
        *,
        status: str,
        counters: dict[str, int],
        rows_total: int,
        rows_valid: int,
        rows_invalid: int,
    ) -> CatalogImport | None:
        record = await self.get_import(import_id)
        if not record:
            return None
        record.status = status
        record.counters = counters
        record.rows_total = rows_total
        record.rows_valid = rows_valid
        record.rows_invalid = rows_invalid
        record.finished_at = datetime.now(timezone.utc)
        await self.session.flush()
        return record

    async def list_imports(self, limit: int = 100, offset: int = 0) -> list[CatalogImport]:
        stmt = (
            select(CatalogImport)
            .order_by(CatalogImport.created_at.desc(), CatalogImport.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_import(self, import_id: uuid.UUID) -> CatalogImport | None:
        result = await self.session.execute(select(CatalogImport).where(CatalogImport.id == import_id))
        return result.scalar_one_or_none()

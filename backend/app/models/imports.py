import uuid

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.db import Base


class CatalogImport(Base):
    __tablename__ = "catalog_imports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String, nullable=False, default="queued")
    mode: Mapped[str] = mapped_column(String, nullable=False, default="sync")
    filename: Mapped[str] = mapped_column(String, nullable=False)
    sheet_name: Mapped[str | None] = mapped_column(String, nullable=True)
    encoding: Mapped[str] = mapped_column(String, nullable=False, default="utf-8")
    delimiter: Mapped[str] = mapped_column(String, nullable=False, default=",")
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    rows_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_valid: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rows_invalid: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    source_rows: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)
    mapping: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    options: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    counters: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)
    errors: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

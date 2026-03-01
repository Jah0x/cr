import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class ImportStatus(StrEnum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class ImportMode(StrEnum):
    sync = "sync"
    background = "background"


class ImportOnConflict(StrEnum):
    update = "update"
    skip = "skip"
    fail = "fail"


ProductImportField = Literal[
    "name",
    "sku",
    "barcode",
    "category",
    "brand",
    "line",
    "unit",
    "cost_price",
    "sell_price",
    "tax_rate",
    "image_url",
    "description",
]


class ImportCounters(BaseModel):
    total: int = Field(default=0, ge=0)
    processed: int = Field(default=0, ge=0)
    created: int = Field(default=0, ge=0)
    updated: int = Field(default=0, ge=0)
    skipped: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)


class ImportInferredTypes(BaseModel):
    by_column: dict[str, str] = Field(default_factory=dict)


class ImportUploadResponse(BaseModel):
    job_id: str
    sheets: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    sample_rows: list[dict[str, str | int | float | bool | None]] = Field(default_factory=list)
    inferred: ImportInferredTypes = Field(default_factory=ImportInferredTypes)


class ImportPreviewOptions(BaseModel):
    on_conflict: ImportOnConflict = ImportOnConflict.update
    dry_run: bool = True
    strict: bool = False


class ImportPreviewRequest(BaseModel):
    mapping: dict[ProductImportField, str]
    options: ImportPreviewOptions = Field(default_factory=ImportPreviewOptions)


class ImportPreviewSummary(BaseModel):
    rows: int = Field(default=0, ge=0)
    valid: int = Field(default=0, ge=0)
    invalid: int = Field(default=0, ge=0)
    would_create: int = Field(default=0, ge=0)
    would_update: int = Field(default=0, ge=0)
    would_skip: int = Field(default=0, ge=0)


class ImportPreviewAction(BaseModel):
    row: int = Field(ge=1)
    action: Literal["create", "update", "skip", "error"]
    reason: str | None = None


class ImportPreviewResponse(BaseModel):
    mapping: dict[ProductImportField, str]
    options: ImportPreviewOptions
    rows: list[dict[str, str | int | float | Decimal | bool | None]] = Field(default_factory=list)
    summary: ImportPreviewSummary
    sample_actions: list[ImportPreviewAction] = Field(default_factory=list)


class ImportApplyRequest(BaseModel):
    import_id: str
    mode: ImportMode = ImportMode.sync
    mapping: dict[ProductImportField, str]
    options: ImportPreviewOptions = Field(default_factory=ImportPreviewOptions)


class ImportApplyResponse(BaseModel):
    import_id: str
    status: ImportStatus
    mode: ImportMode
    counters: ImportCounters
    error_log_url: HttpUrl | None = None


class ImportHistoryItem(BaseModel):
    import_id: str
    status: ImportStatus
    mode: ImportMode
    counters: ImportCounters
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ImportHistoryDetail(ImportHistoryItem):
    mapping: dict[ProductImportField, str]
    options: ImportPreviewOptions
    error_log_url: HttpUrl | None = None
    uploaded_by: uuid.UUID | None = None


class ImportHistoryListResponse(BaseModel):
    items: list[ImportHistoryItem] = Field(default_factory=list)
    total: int = Field(default=0, ge=0)

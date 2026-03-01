import csv
import io
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.deps import get_current_tenant, get_current_user, require_roles


@dataclass
class ImportRecord:
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    status: str
    created_at: datetime
    sheet_name: str | None = None
    encoding: str = "utf-8"
    delimiter: str = ","
    rows_total: int = 0
    rows_valid: int = 0
    rows_invalid: int = 0
    parsed_rows: list[dict[str, str]] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)


IMPORTS_STORE: dict[uuid.UUID, ImportRecord] = {}


class ImportOut(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    sheet_name: str | None
    encoding: str
    delimiter: str
    rows_total: int
    rows_valid: int
    rows_invalid: int
    created_at: datetime


class ImportPreviewRequest(BaseModel):
    import_id: uuid.UUID
    limit: int = Field(default=20, ge=1, le=1000)


class ImportApplyRequest(BaseModel):
    import_id: uuid.UUID


class ImportApplyResponse(BaseModel):
    import_id: uuid.UUID
    status: str
    applied_rows: int
    skipped_rows: int


router = APIRouter(
    prefix="/admin/imports",
    tags=["imports_catalog"],
    dependencies=[
        Depends(get_current_user),
        Depends(require_roles({"owner", "admin"})),
        Depends(get_current_tenant),
    ],
)


def _to_out(item: ImportRecord) -> ImportOut:
    return ImportOut(
        id=item.id,
        filename=item.filename,
        status=item.status,
        sheet_name=item.sheet_name,
        encoding=item.encoding,
        delimiter=item.delimiter,
        rows_total=item.rows_total,
        rows_valid=item.rows_valid,
        rows_invalid=item.rows_invalid,
        created_at=item.created_at,
    )


def _get_import_for_tenant(import_id: uuid.UUID, tenant_id: uuid.UUID) -> ImportRecord:
    item = IMPORTS_STORE.get(import_id)
    if not item or item.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Import not found")
    return item


def _parse_csv(content: bytes, encoding: str, delimiter: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    text = content.decode(encoding)
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for idx, row in enumerate(reader, start=2):
        normalized = {str(k): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        rows.append(normalized)
        if not any((value or "") for value in normalized.values()):
            errors.append({"row": str(idx), "error": "Empty row"})

    return rows, errors


@router.post("/catalog/upload", response_model=ImportOut)
async def upload_catalog_import(
    file: UploadFile = File(...),
    sheet_name: str | None = Form(default=None),
    encoding: str = Form(default="utf-8"),
    delimiter: str = Form(default=","),
    tenant=Depends(get_current_tenant),
    current_user=Depends(get_current_user),
):
    if len(delimiter) != 1:
        raise HTTPException(status_code=400, detail="Delimiter must be a single character")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        parsed_rows, errors = _parse_csv(raw, encoding, delimiter)
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Failed to decode file with encoding '{encoding}'") from exc
    except csv.Error as exc:
        raise HTTPException(status_code=400, detail="Failed to parse CSV") from exc

    import_id = uuid.uuid4()
    record = ImportRecord(
        id=import_id,
        tenant_id=tenant.id,
        user_id=current_user.id,
        filename=file.filename or "uploaded.csv",
        status="uploaded",
        created_at=datetime.now(tz=timezone.utc),
        sheet_name=sheet_name,
        encoding=encoding,
        delimiter=delimiter,
        rows_total=len(parsed_rows),
        rows_valid=len(parsed_rows) - len(errors),
        rows_invalid=len(errors),
        parsed_rows=parsed_rows,
        errors=errors,
    )
    IMPORTS_STORE[import_id] = record
    return _to_out(record)


@router.post("/catalog/preview")
async def preview_catalog_import(payload: ImportPreviewRequest, tenant=Depends(get_current_tenant)):
    item = _get_import_for_tenant(payload.import_id, tenant.id)
    preview_rows = item.parsed_rows[: payload.limit]
    return {
        "import": _to_out(item),
        "preview": preview_rows,
        "errors": item.errors,
    }


@router.post("/catalog/apply", response_model=ImportApplyResponse)
async def apply_catalog_import(payload: ImportApplyRequest, tenant=Depends(get_current_tenant)):
    item = _get_import_for_tenant(payload.import_id, tenant.id)
    item.status = "applied"
    return ImportApplyResponse(
        import_id=item.id,
        status=item.status,
        applied_rows=item.rows_valid,
        skipped_rows=item.rows_invalid,
    )


@router.get("", response_model=list[ImportOut])
async def list_imports(tenant=Depends(get_current_tenant)):
    items = [item for item in IMPORTS_STORE.values() if item.tenant_id == tenant.id]
    items.sort(key=lambda value: value.created_at, reverse=True)
    return [_to_out(item) for item in items]


@router.get("/{import_id}", response_model=ImportOut)
async def get_import(import_id: uuid.UUID, tenant=Depends(get_current_tenant)):
    item = _get_import_for_tenant(import_id, tenant.id)
    return _to_out(item)


@router.get("/{import_id}/errors")
async def download_import_errors(import_id: uuid.UUID, tenant=Depends(get_current_tenant)):
    item = _get_import_for_tenant(import_id, tenant.id)

    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["row", "error"])
    writer.writeheader()
    writer.writerows(item.errors)

    filename = f"import-errors-{import_id}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers=headers)

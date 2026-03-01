import csv
import io
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.db import get_sessionmaker
from app.core.db_utils import set_search_path
from app.core.deps import get_current_tenant, get_current_user, get_db_session, require_roles
from app.repos.imports_repo import ImportsRepo
from app.schemas.imports import ImportMode
from app.services.import_service import ImportService


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


class ImportPreviewRequest(BaseModel):
    import_id: uuid.UUID
    mapping: dict[str, str]
    options: dict = Field(default_factory=dict)


class ImportApplyRequest(BaseModel):
    import_id: uuid.UUID
    mode: ImportMode = ImportMode.sync
    mapping: dict[str, str]
    options: dict = Field(default_factory=dict)


class ImportApplyResponse(BaseModel):
    import_id: uuid.UUID
    status: str
    mode: ImportMode
    counters: dict[str, int]


router = APIRouter(
    prefix="/admin/imports",
    tags=["imports_catalog"],
    dependencies=[
        Depends(get_current_user),
        Depends(require_roles({"owner", "admin"})),
        Depends(get_current_tenant),
    ],
)


def _to_out(item) -> ImportOut:
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
    )


@router.post("/catalog/upload", response_model=ImportOut)
async def upload_catalog_import(
    file: UploadFile = File(...),
    sheet_name: str | None = Form(default=None),
    encoding: str = Form(default="utf-8"),
    delimiter: str = Form(default=","),
    tenant=Depends(get_current_tenant),
    current_user=Depends(get_current_user),
    session=Depends(get_db_session),
):
    if len(delimiter) != 1:
        raise HTTPException(status_code=400, detail="Delimiter must be a single character")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    service = ImportService(session, ImportsRepo(session))
    try:
        parsed = service.parse_file(raw, sheet=sheet_name, encoding=encoding, delimiter=delimiter)
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Failed to decode file with encoding '{encoding}'") from exc
    except csv.Error as exc:
        raise HTTPException(status_code=400, detail="Failed to parse CSV") from exc

    record = await service.imports_repo.create_job(
        {
            "filename": file.filename or "uploaded.csv",
            "status": "queued",
            "mode": "sync",
            "sheet_name": sheet_name,
            "encoding": encoding,
            "delimiter": delimiter,
            "uploaded_by": current_user.id,
            "rows_total": len(parsed["rows"]),
            "rows_valid": len(parsed["rows"]),
            "rows_invalid": 0,
            "source_rows": parsed["rows"],
            "errors": [],
            "mapping": {},
            "options": {},
            "counters": {},
        }
    )
    return _to_out(record)


@router.post("/catalog/preview")
async def preview_catalog_import(
    payload: ImportPreviewRequest,
    session=Depends(get_db_session),
):
    service = ImportService(session, ImportsRepo(session))
    return await service.preview_import(payload.import_id, payload.mapping, payload.options)


async def _perform_import_background(tenant_schema: str, import_id: uuid.UUID, mapping: dict[str, str], options: dict):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        await set_search_path(session, tenant_schema)
        service = ImportService(session, ImportsRepo(session))
        try:
            await service.perform_import(import_id, mapping, options)
            await session.commit()
        except Exception:
            await service.imports_repo.update_status(import_id, "failed")
            await session.commit()


@router.post("/catalog/apply", response_model=ImportApplyResponse)
async def apply_catalog_import(
    payload: ImportApplyRequest,
    background_tasks: BackgroundTasks,
    tenant=Depends(get_current_tenant),
    session=Depends(get_db_session),
):
    service = ImportService(session, ImportsRepo(session))

    if payload.mode == ImportMode.background:
        await service.imports_repo.update_status(payload.import_id, "queued")
        background_tasks.add_task(
            _perform_import_background,
            tenant.code,
            payload.import_id,
            payload.mapping,
            payload.options,
        )
        return ImportApplyResponse(import_id=payload.import_id, status="queued", mode=payload.mode, counters={})

    counters = await service.perform_import(payload.import_id, payload.mapping, payload.options)
    return ImportApplyResponse(import_id=payload.import_id, status="done", mode=payload.mode, counters=counters)


@router.get("", response_model=list[ImportOut])
async def list_imports(session=Depends(get_db_session)):
    repo = ImportsRepo(session)
    items = await repo.list_imports()
    return [_to_out(item) for item in items]


@router.get("/{import_id}", response_model=ImportOut)
async def get_import(import_id: uuid.UUID, session=Depends(get_db_session)):
    repo = ImportsRepo(session)
    item = await repo.get_import(import_id)
    if not item:
        raise HTTPException(status_code=404, detail="Import not found")
    return _to_out(item)


@router.get("/{import_id}/errors")
async def download_import_errors(import_id: uuid.UUID, session=Depends(get_db_session)):
    repo = ImportsRepo(session)
    item = await repo.get_import(import_id)
    if not item:
        raise HTTPException(status_code=404, detail="Import not found")

    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["row", "error"])
    writer.writeheader()
    writer.writerows(item.errors or [])

    filename = f"import-errors-{import_id}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers=headers)

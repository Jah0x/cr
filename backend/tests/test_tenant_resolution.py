import os
import asyncio
import pathlib
import sys
import pytest
from fastapi import HTTPException, status
from starlette.requests import Request
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test")
os.environ.setdefault("JWT_EXPIRES", "3600")

from app.core.db import Base
from app.models.tenant import Tenant, TenantStatus
from app.services.tenant_service import TenantService
from app.repos.tenant_repo import TenantRepo
from app.core import db as core_db

engine = create_async_engine(os.environ["DATABASE_URL"], future=True)
TestSession = async_sessionmaker(engine, expire_on_commit=False)
core_db.engine = engine
core_db.async_session = TestSession


async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


def setup_module():
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    asyncio.run(reset_db())


def teardown_module():
    asyncio.run(engine.dispose())
    if os.path.exists("./test.db"):
        os.remove("./test.db")


def build_request(headers: dict | None = None):
    headers = headers or {}
    raw = []
    lower_keys = {key.lower() for key in headers}
    for key, value in headers.items():
        raw.append((key.lower().encode(), str(value).encode()))
    if "host" not in lower_keys:
        raw.append((b"host", b"alpha.example.com"))
    scope = {"type": "http", "headers": raw}
    return Request(scope)


def test_resolves_from_header_and_sets_state():
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Alpha", code="alpha")
                session.add(tenant)
            service = TenantService(TenantRepo(session))
            request = build_request({"x-tenant-id": str(tenant.id)})
            resolved = await service.resolve_tenant(request)
            return tenant, resolved, request.state.tenant_id

    tenant, resolved, tenant_id = asyncio.run(scenario())
    assert resolved.id == tenant.id
    assert tenant_id == tenant.id


def test_resolves_from_host_subdomain():
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Beta", code="beta")
                session.add(tenant)
            service = TenantService(TenantRepo(session))
            request = build_request({"host": "beta.example.com"})
            resolved = await service.resolve_tenant(request)
            return tenant, resolved

    tenant, resolved = asyncio.run(scenario())
    assert resolved.id == tenant.id


def test_inactive_tenant_rejected():
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Gamma", code="gamma", status=TenantStatus.inactive)
                session.add(tenant)
            service = TenantService(TenantRepo(session))
            request = build_request({"x-tenant-code": "gamma"})
            with pytest.raises(HTTPException) as exc:
                await service.resolve_tenant(request)
            return exc.value.status_code

    status_code = asyncio.run(scenario())
    assert status_code == status.HTTP_403_FORBIDDEN

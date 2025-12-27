import os
import asyncio
import pathlib
import sys
import pytest
from fastapi import HTTPException
from starlette.requests import Request
import os
import asyncio
import pathlib
import sys
import pytest
from fastapi import HTTPException
from starlette.requests import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test")
os.environ.setdefault("JWT_EXPIRES", "3600")

from app.core.db import Base
from app.models.tenant import Tenant, TenantStatus
from app.api.health import readiness_check
from app.repos.tenant_repo import TenantRepo
from app.core import db as core_db

engine = create_async_engine(os.environ["DATABASE_URL"], future=True)
TestSession = async_sessionmaker(engine, expire_on_commit=False)
core_db.engine = engine
core_db.async_session = TestSession


def build_request(headers: dict | None = None):
    headers = headers or {}
    raw = [(key.lower().encode(), str(value).encode()) for key, value in headers.items()]
    scope = {"type": "http", "headers": raw}
    return Request(scope)


async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        await conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('test')"))


def setup_module():
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    asyncio.run(reset_db())


def teardown_module():
    asyncio.run(engine.dispose())
    if os.path.exists("./test.db"):
        os.remove("./test.db")


def test_ready_without_tenant():
    async def scenario():
        async with TestSession() as session:
            return await readiness_check(session, build_request(), None)

    result = asyncio.run(scenario())
    assert result == {"status": "ready"}


def test_ready_with_tenant_header_id():
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Alpha", code="alpha")
                session.add(tenant)
            repo = TenantRepo(session)
            tenant = await repo.get_by_code("alpha")
            return await readiness_check(session, build_request({"x-tenant-id": str(tenant.id)}), None)

    result = asyncio.run(scenario())
    assert result == {"status": "ready"}


def test_ready_with_tenant_query_code():
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Beta", code="beta")
                session.add(tenant)
            return await readiness_check(session, build_request(), "beta")

    result = asyncio.run(scenario())
    assert result == {"status": "ready"}


def test_ready_rejects_inactive_tenant():
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Gamma", code="gamma", status=TenantStatus.inactive)
                session.add(tenant)
            with pytest.raises(HTTPException) as exc:
                await readiness_check(session, build_request(), "gamma")
            return exc.value

    error = asyncio.run(scenario())
    assert error.status_code == 403


def test_ready_missing_tenant():
    async def scenario():
        async with TestSession() as session:
            with pytest.raises(HTTPException) as exc:
                await readiness_check(session, build_request({"x-tenant-code": "delta"}), None)
            return exc.value

    error = asyncio.run(scenario())
    assert error.status_code == 404

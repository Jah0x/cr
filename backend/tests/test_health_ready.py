import os
import asyncio
import pathlib
import sys
from starlette.requests import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test")
os.environ.setdefault("JWT_EXPIRES", "3600")
os.environ.setdefault("ROOT_DOMAIN", "example.com")
os.environ.setdefault("PLATFORM_HOSTS", "platform.example.com")
os.environ.setdefault("RESERVED_SUBDOMAINS", "admin,root")
os.environ.setdefault("DEFAULT_TENANT_SLUG", "default")

from app.core.db import Base
from app.models.tenant import Tenant
from app.api.health import readiness_check
from app.core import db as core_db

engine = create_async_engine(os.environ["DATABASE_URL"], future=True)
TestSession = async_sessionmaker(engine, expire_on_commit=False)
core_db.engine = engine
core_db.async_session = TestSession


def build_request(headers: dict | None = None):
    headers = headers or {}
    if "host" not in {key.lower() for key in headers}:
        headers["host"] = "platform.example.com"
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


def test_ready_on_platform_host():
    async def scenario():
        async with TestSession() as session:
            return await readiness_check(session, build_request(), None)

    result = asyncio.run(scenario())
    assert result == {"status": "ready"}


def test_ready_with_tenant_host():
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Alpha", code="alpha")
                session.add(tenant)
            return await readiness_check(session, build_request({"host": "alpha.example.com"}), None)

    result = asyncio.run(scenario())
    assert result == {"status": "ready"}


def test_ready_allows_reserved_subdomain_without_mapping():
    async def scenario():
        async with TestSession() as session:
            return await readiness_check(session, build_request({"host": "admin.example.com"}), None)

    result = asyncio.run(scenario())
    assert result == {"status": "ready"}


def test_ready_missing_tenant_host():
    async def scenario():
        async with TestSession() as session:
            return await readiness_check(session, build_request({"host": "delta.example.com"}), None)

    result = asyncio.run(scenario())
    assert result == {"status": "ready"}

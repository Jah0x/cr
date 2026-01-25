import os
import asyncio
import pathlib
import sys

import pytest
import httpx
from fastapi import Request
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test")
os.environ.setdefault("JWT_EXPIRES", "3600")
os.environ.setdefault("ROOT_DOMAIN", "example.com")
os.environ.setdefault("PLATFORM_HOSTS", "platform.example.com")
os.environ.setdefault("RESERVED_SUBDOMAINS", "admin,root")
os.environ.setdefault("DEFAULT_TENANT_SLUG", "default")
os.environ.setdefault("FIRST_OWNER_EMAIL", "platform@example.com")
os.environ.setdefault("FIRST_OWNER_PASSWORD", "platform-pass")

from app.core.db import Base
from app.core.security import hash_password
from app.core.deps import get_db_session
from app.core import deps as deps_module
from app.main import app
from app.models.tenant import Tenant, TenantStatus
from app.models.user import Role, User

engine = create_async_engine(os.environ["DATABASE_URL"], future=True)
TestSession = async_sessionmaker(engine, expire_on_commit=False)


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


@pytest.fixture
def app_client(monkeypatch):
    async def override_get_db_session(request: Request):
        async with TestSession() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def noop(*args, **kwargs):
        return None

    monkeypatch.setattr(deps_module, "set_search_path", noop)
    monkeypatch.setattr(deps_module, "ensure_tenant_ready", noop)
    app.dependency_overrides[get_db_session] = override_get_db_session
    yield app
    app.dependency_overrides.clear()


def test_tenant_login_not_503(app_client):
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Alpha", code="alpha", status=TenantStatus.active)
                role = Role(name="owner")
                user = User(email="owner@example.com", password_hash=hash_password("secret"), is_active=True)
                user.roles.append(role)
                session.add_all([tenant, role, user])

        transport = httpx.ASGITransport(app=app_client, lifespan="off")
        async with httpx.AsyncClient(transport=transport, base_url="http://alpha.example.com") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "owner@example.com", "password": "secret"},
            )
            return response.status_code

    status_code = asyncio.run(scenario())
    assert status_code in {200, 401, 403}
    assert status_code != 503


def test_platform_login_and_list_tenants(app_client):
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Beta", code="beta", status=TenantStatus.active)
                session.add(tenant)

        transport = httpx.ASGITransport(app=app_client, lifespan="off")
        async with httpx.AsyncClient(transport=transport, base_url="http://platform.example.com") as client:
            login = await client.post(
                "/api/v1/platform/auth/login",
                json={"email": "platform@example.com", "password": "platform-pass"},
            )
            token = login.json()["access_token"]
            response = await client.get(
                "/api/v1/platform/tenants",
                headers={"Authorization": f"Bearer {token}"},
            )
            return login.status_code, response.status_code

    login_status, list_status = asyncio.run(scenario())
    assert login_status == 200
    assert list_status == 200

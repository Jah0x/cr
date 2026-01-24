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
os.environ.setdefault("ROOT_DOMAIN", "example.com")
os.environ.setdefault("PLATFORM_HOSTS", "platform.example.com")
os.environ.setdefault("RESERVED_SUBDOMAINS", "admin,root")
os.environ.setdefault("DEFAULT_TENANT_SLUG", "default")
os.environ.setdefault("TENANT_CANONICAL_REDIRECT", "true")

from app.core.db import Base
from app.models.tenant import Tenant
from app.models.tenant_domain import TenantDomain
from app.services.tenant_service import TenantService
from app.repos.tenant_domain_repo import TenantDomainRepo
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


def build_request(headers: dict | None = None, *, path: str = "/", query_string: str = ""):
    headers = headers or {}
    raw = []
    lower_keys = {key.lower() for key in headers}
    for key, value in headers.items():
        raw.append((key.lower().encode(), str(value).encode()))
    if "host" not in lower_keys:
        raw.append((b"host", b"alpha.example.com"))
    scope = {
        "type": "http",
        "headers": raw,
        "path": path,
        "query_string": query_string.encode(),
        "scheme": "http",
    }
    return Request(scope)


def test_resolves_from_host_and_sets_state():
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Alpha", code="alpha")
                session.add(tenant)
            service = TenantService(TenantRepo(session), TenantDomainRepo(session))
            request = build_request({"host": "alpha.example.com"})
            resolved = await service.resolve_tenant(request)
            return tenant, resolved, request.state.tenant_id, request.state.tenant, request.state.tenant_schema

    tenant, resolved, tenant_id, state_tenant, tenant_schema = asyncio.run(scenario())
    assert resolved.id == tenant.id
    assert tenant_id == tenant.id
    assert state_tenant.id == tenant.id
    assert tenant_schema == tenant.code


def test_platform_host_returns_none():
    async def scenario():
        async with TestSession() as session:
            service = TenantService(TenantRepo(session), TenantDomainRepo(session))
            request = build_request({"host": "platform.example.com"})
            resolved = await service.resolve_tenant(request)
            return resolved, request.state.tenant, request.state.tenant_schema

    resolved, state_tenant, tenant_schema = asyncio.run(scenario())
    assert resolved is None
    assert state_tenant is None
    assert tenant_schema is None


def test_reserved_subdomain_returns_none():
    async def scenario():
        async with TestSession() as session:
            service = TenantService(TenantRepo(session), TenantDomainRepo(session))
            request = build_request({"host": "admin.example.com"})
            resolved = await service.resolve_tenant(request)
            return resolved, request.state.tenant, request.state.tenant_schema

    resolved, state_tenant, tenant_schema = asyncio.run(scenario())
    assert resolved is None
    assert state_tenant is None
    assert tenant_schema is None


def test_reserved_subdomain_ignores_explicit_mapping():
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Admin", code="admin")
                session.add(tenant)
            service = TenantService(TenantRepo(session), TenantDomainRepo(session))
            request = build_request({"host": "admin.example.com"})
            resolved = await service.resolve_tenant(request)
            return tenant, resolved, request.state.tenant, request.state.tenant_schema

    tenant, resolved, state_tenant, tenant_schema = asyncio.run(scenario())
    assert resolved is None
    assert state_tenant is None
    assert tenant_schema is None


def test_unknown_tenant_host_rejected():
    async def scenario():
        async with TestSession() as session:
            service = TenantService(TenantRepo(session), TenantDomainRepo(session))
            request = build_request({"host": "unknown.example.com"})
            with pytest.raises(HTTPException) as exc:
                await service.resolve_tenant(request)
            return exc.value.status_code

    status_code = asyncio.run(scenario())
    assert status_code == status.HTTP_404_NOT_FOUND


def test_custom_domain_resolves_tenant():
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Custom", code="custom")
                session.add(tenant)
            async with session.begin():
                domain = TenantDomain(tenant_id=tenant.id, domain="custom.example.org", is_primary=True)
                session.add(domain)
            service = TenantService(TenantRepo(session), TenantDomainRepo(session))
            request = build_request({"host": "custom.example.org"})
            resolved = await service.resolve_tenant(request)
            return tenant, resolved

    tenant, resolved = asyncio.run(scenario())
    assert resolved.id == tenant.id


def test_non_primary_domain_redirects_to_primary():
    async def scenario():
        async with TestSession() as session:
            async with session.begin():
                tenant = Tenant(name="Redirect", code="redirect")
                session.add(tenant)
            async with session.begin():
                session.add(
                    TenantDomain(tenant_id=tenant.id, domain="primary.example.com", is_primary=True)
                )
                session.add(
                    TenantDomain(tenant_id=tenant.id, domain="alias.example.com", is_primary=False)
                )
            service = TenantService(TenantRepo(session), TenantDomainRepo(session))
            request = build_request(
                {"host": "alias.example.com"},
                path="/orders",
                query_string="status=open",
            )
            with pytest.raises(HTTPException) as exc:
                await service.resolve_tenant(request)
            return exc.value

    exc = asyncio.run(scenario())
    assert exc.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert exc.headers["Location"] == "http://primary.example.com/orders?status=open"

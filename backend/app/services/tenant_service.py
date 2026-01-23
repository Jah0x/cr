from fastapi import HTTPException, Request, status

from app.core.config import get_settings
from app.core.tenancy import is_valid_tenant_slug, normalize_tenant_slug
from app.models.tenant import TenantStatus
from app.repos.tenant_repo import TenantRepo


class TenantService:
    def __init__(self, tenant_repo: TenantRepo):
        self.tenant_repo = tenant_repo

    async def resolve_tenant(self, request: Request):
        tenant_code = self._tenant_code_from_host(request)
        if not tenant_code:
            self._set_request_state(request, None)
            return None
        tenant = await self.tenant_repo.get_by_code(tenant_code)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        if tenant.status != TenantStatus.active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant inactive")
        self._set_request_state(request, tenant)
        return tenant

    def _tenant_code_from_host(self, request: Request):
        settings = get_settings()
        host = (request.headers.get("host") or "").split(":", 1)[0].lower().strip()
        if not host:
            return None
        if host in {"localhost", "127.0.0.1"} or host.endswith(".localhost"):
            if settings.default_tenant_slug and is_valid_tenant_slug(settings.default_tenant_slug):
                return normalize_tenant_slug(settings.default_tenant_slug)
            return None
        platform_hosts = {item for item in self._split_csv(settings.platform_hosts)}
        if host in platform_hosts:
            return None
        reserved_subdomains = {item for item in self._split_csv(settings.reserved_subdomains)}
        root_domain = settings.root_domain.lower().strip(".")
        if root_domain:
            if host == root_domain:
                return None
            suffix = f".{root_domain}"
            if host.endswith(suffix):
                subdomain = host[: -len(suffix)]
                if not subdomain or "." in subdomain or subdomain in reserved_subdomains:
                    return None
                if not is_valid_tenant_slug(subdomain):
                    return None
                return subdomain
            return None
        parts = host.split(".")
        if len(parts) != 2:
            return None
        subdomain = parts[0]
        if "." in subdomain or subdomain in reserved_subdomains:
            return None
        if not is_valid_tenant_slug(subdomain):
            return None
        return subdomain

    def _split_csv(self, value: str):
        return [item.strip().lower() for item in value.split(",") if item.strip()]

    def _set_request_state(self, request: Request, tenant):
        request.state.tenant = tenant
        if tenant:
            request.state.tenant_id = tenant.id
            request.state.tenant_schema = tenant.code
        else:
            request.state.tenant_id = None
            request.state.tenant_schema = None

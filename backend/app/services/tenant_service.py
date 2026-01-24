from fastapi import HTTPException, Request, status

from app.core.config import get_settings
from app.core.tenancy import is_valid_tenant_slug, normalize_tenant_slug
from app.models.tenant import TenantStatus
from app.models.tenant_domain import TenantDomain
from app.repos.tenant_domain_repo import TenantDomainRepo
from app.repos.tenant_repo import TenantRepo


class TenantService:
    def __init__(self, tenant_repo: TenantRepo, tenant_domain_repo: TenantDomainRepo | None = None):
        self.tenant_repo = tenant_repo
        self.tenant_domain_repo = tenant_domain_repo

    async def resolve_tenant(self, request: Request):
        tenant_code, domain_row, tenant = await self._tenant_code_from_host(request)
        if not tenant_code:
            if domain_row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
            self._set_request_state(request, None)
            return None
        if not tenant:
            tenant = await self.tenant_repo.get_by_code(tenant_code)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        settings = get_settings()
        if domain_row and settings.tenant_canonical_redirect and not domain_row.is_primary:
            primary_domain = await self._get_primary_domain(domain_row.tenant_id)
            if primary_domain and primary_domain.domain != domain_row.domain:
                redirect_url = request.url.replace(netloc=primary_domain.domain)
                raise HTTPException(
                    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                    headers={"Location": str(redirect_url)},
                )
        if tenant.status == TenantStatus.provisioning_failed:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=tenant.last_error or "Tenant provisioning failed",
            )
        if tenant.status != TenantStatus.active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant inactive")
        self._set_request_state(request, tenant)
        return tenant

    async def _tenant_code_from_host(self, request: Request):
        settings = get_settings()
        host = (request.headers.get("host") or "").split(":", 1)[0].lower().strip()
        if not host:
            return None, None, None
        if host in {"localhost", "127.0.0.1"} or host.endswith(".localhost"):
            if settings.default_tenant_slug and is_valid_tenant_slug(settings.default_tenant_slug):
                return normalize_tenant_slug(settings.default_tenant_slug), None, None
            return None, None, None
        platform_hosts = {item for item in self._split_csv(settings.platform_hosts)}
        if host in platform_hosts:
            return None, None, None
        reserved_subdomains = {item for item in self._split_csv(settings.reserved_subdomains)}
        root_domain = settings.root_domain.lower().strip(".")
        if self.tenant_domain_repo and not self._is_reserved_host(host, platform_hosts, reserved_subdomains, root_domain):
            domain_row = await self.tenant_domain_repo.get_by_domain(host)
            if domain_row:
                tenant = await self.tenant_repo.get_by_id(domain_row.tenant_id)
                if tenant:
                    return tenant.code, domain_row, tenant
                return None, domain_row, None
        if root_domain:
            if host == root_domain:
                return None, None, None
            suffix = f".{root_domain}"
            if host.endswith(suffix):
                subdomain = host[: -len(suffix)]
                if not subdomain or "." in subdomain or subdomain in reserved_subdomains:
                    return None, None, None
                if not is_valid_tenant_slug(subdomain):
                    return None, None, None
                return subdomain, None, None
            return None, None, None
        parts = host.split(".")
        if len(parts) != 2:
            return None, None, None
        subdomain = parts[0]
        if "." in subdomain or subdomain in reserved_subdomains:
            return None, None, None
        if not is_valid_tenant_slug(subdomain):
            return None, None, None
        return subdomain, None, None

    def _split_csv(self, value: str):
        return [item.strip().lower() for item in value.split(",") if item.strip()]

    async def _get_primary_domain(self, tenant_id) -> TenantDomain | None:
        if not self.tenant_domain_repo:
            return None
        domains = await self.tenant_domain_repo.list_by_tenant(tenant_id)
        for domain in domains:
            if domain.is_primary:
                return domain
        return None

    def _is_reserved_host(
        self,
        host: str,
        platform_hosts: set[str],
        reserved_subdomains: set[str],
        root_domain: str,
    ) -> bool:
        if host in platform_hosts:
            return True
        if root_domain:
            if host == root_domain:
                return True
            suffix = f".{root_domain}"
            if host.endswith(suffix):
                subdomain = host[: -len(suffix)]
                if subdomain in reserved_subdomains:
                    return True
            return False
        parts = host.split(".")
        if len(parts) == 2 and parts[0] in reserved_subdomains:
            return True
        return False

    def _set_request_state(self, request: Request, tenant):
        request.state.tenant = tenant
        if tenant:
            request.state.tenant_id = tenant.id
            request.state.tenant_schema = tenant.code
        else:
            request.state.tenant_id = None
            request.state.tenant_schema = None

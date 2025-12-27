import uuid
from fastapi import HTTPException, Request, status

from app.models.tenant import TenantStatus
from app.repos.tenant_repo import TenantRepo


class TenantService:
    def __init__(self, tenant_repo: TenantRepo):
        self.tenant_repo = tenant_repo

    async def resolve_tenant(self, request: Request, token_payload: dict | None = None):
        tenant_id = self._tenant_id_from_header(request)
        tenant_code = self._tenant_code_from_header(request)
        if not tenant_id and not tenant_code and token_payload:
            tenant_id = self._tenant_id_from_token(token_payload)
        if not tenant_id and not tenant_code:
            tenant_code = self._tenant_code_from_host(request)
        if not tenant_id and not tenant_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not specified")
        tenant = None
        if tenant_id:
            tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant and tenant_code:
            tenant = await self.tenant_repo.get_by_code(tenant_code)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        if tenant.status != TenantStatus.active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant inactive")
        request.state.tenant_id = tenant.id
        return tenant

    def _tenant_id_from_header(self, request: Request):
        raw = request.headers.get("x-tenant-id")
        if not raw:
            return None
        try:
            return uuid.UUID(raw)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant id")

    def _tenant_code_from_header(self, request: Request):
        return request.headers.get("x-tenant-code") or request.headers.get("x-tenant")

    def _tenant_id_from_token(self, token_payload: dict):
        value = token_payload.get("tenant_id")
        if not value:
            return None
        try:
            return uuid.UUID(str(value))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant token claim")

    def _tenant_code_from_host(self, request: Request):
        host = request.headers.get("host") or ""
        host = host.split(":", 1)[0]
        parts = host.split(".")
        if len(parts) < 2:
            return None
        return parts[0]

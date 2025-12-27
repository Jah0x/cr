import uuid
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(
    subject: str,
    roles: list[str],
    tenant_id: str | uuid.UUID,
    expires_delta: timedelta | None = None,
) -> str:
    if not tenant_id:
        raise ValueError("tenant_id is required")
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(seconds=settings.jwt_expires_seconds))
    to_encode = {
        "sub": subject,
        "roles": roles,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
    }
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def verify_token(token: str) -> dict:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    sub = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    if not sub or not tenant_id:
        raise JWTError("Invalid token")
    return payload


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(seconds=settings.jwt_access_ttl_seconds))
    to_encode = {"sub": subject, "exp": expire, "jti": str(uuid.uuid4())}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def verify_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    sub = payload.get("sub")
    if not sub:
        raise JWTError("Invalid token")
    return sub


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

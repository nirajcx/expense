from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError

from app.config import get_settings

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: UUID) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=settings.access_token_minutes,
    )
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> UUID:
    settings = get_settings()

    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp"]},
    )

    try:
        return UUID(payload["sub"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise InvalidTokenError("Invalid token subject") from exc

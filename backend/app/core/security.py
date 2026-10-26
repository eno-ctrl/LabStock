from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from backend.app.core.config import settings
from backend.app.core.exceptions import AuthenticationFailedException

# Modern Argon2id Password Hasher
_ph = PasswordHasher()


def get_password_hash(password: str) -> str:
    """Hash password using Argon2id with salt and memory-hard parameters."""
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(
    subject: str,
    role: str,
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token containing subject, user_id, role and exp."""
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "uid": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub", "uid", "role"]},
        )
        return payload
    except jwt.ExpiredSignatureError as err:
        raise AuthenticationFailedException("Session token has expired") from err
    except jwt.InvalidTokenError as err:
        raise AuthenticationFailedException("Invalid token signature or payload") from err


# In-memory IP/User login attempt tracker for rate-limiting
_login_attempts: dict[str, list[float]] = {}


def check_rate_limit(key: str, limit: int = 15, window_seconds: int = 60) -> bool:
    """Simple sliding window rate limiter. Returns True if within limit, False if exceeded."""
    import time

    now = time.time()
    attempts = _login_attempts.get(key, [])
    # Filter attempts within window
    attempts = [t for t in attempts if now - t < window_seconds]
    if len(attempts) >= limit:
        _login_attempts[key] = attempts
        return False
    attempts.append(now)
    _login_attempts[key] = attempts
    return True

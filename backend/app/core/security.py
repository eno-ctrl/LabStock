import uuid
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
    token_version: int = 1,
) -> str:
    """Create a signed JWT access token containing subject, user_id, role, jti, token_version, and exp."""
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = str(uuid.uuid4())
    payload = {
        "sub": subject,
        "uid": user_id,
        "role": role,
        "jti": jti,
        "ver": token_version,
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


# In-memory Revoked Tokens Store (tracks jti -> expiry timestamp)
_revoked_tokens: dict[str, float] = {}


def revoke_token(jti_or_token: str, exp_timestamp: float | None = None) -> None:
    """Revoke a token by registering its jti or signature until natural expiration."""
    import time

    now = time.time()
    # Periodic sweep of expired revoked entries
    expired = [k for k, exp in _revoked_tokens.items() if exp <= now]
    for k in expired:
        _revoked_tokens.pop(k, None)

    # If no expiry provided, hold for 24 hours
    _revoked_tokens[jti_or_token] = exp_timestamp or (now + 86400)


def is_token_revoked(jti_or_token: str) -> bool:
    """Check if token identifier or signature is currently revoked."""
    import time

    now = time.time()
    exp = _revoked_tokens.get(jti_or_token)
    if exp is not None:
        if exp > now:
            return True
        _revoked_tokens.pop(jti_or_token, None)
    return False


# In-memory IP/User login attempt tracker for rate-limiting
_login_attempts: dict[str, list[float]] = {}


def check_rate_limit(key: str, limit: int = 15, window_seconds: int = 60) -> bool:
    """Sliding window rate limiter with periodic cleanup of stale keys."""
    import time

    now = time.time()
    # Prune stale keys if tracking dictionary grows
    if len(_login_attempts) > 1000:
        stale_keys = [
            k for k, v in _login_attempts.items() if not v or (now - max(v) > window_seconds)
        ]
        for k in stale_keys:
            _login_attempts.pop(k, None)

    attempts = _login_attempts.get(key, [])
    # Filter attempts within window
    attempts = [t for t in attempts if now - t < window_seconds]
    if len(attempts) >= limit:
        _login_attempts[key] = attempts
        return False
    attempts.append(now)
    _login_attempts[key] = attempts
    return True

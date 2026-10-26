from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.core.exceptions import AuthenticationFailedException
from backend.app.core.permissions import get_current_active_user
from backend.app.core.security import (
    check_rate_limit,
    create_access_token,
    decode_access_token,
    revoke_token,
    verify_password,
)
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.user import TokenResponse, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticate user with email/username and Argon2id password hash."""
    client_ip = request.client.host if request.client else "unknown"

    # IP-level rate limiting against brute-force and credential stuffing
    if not check_rate_limit(f"ip_{client_ip}", limit=40, window_seconds=60):
        raise AuthenticationFailedException(
            "Too many requests from this IP address. Please wait 60 seconds before trying again."
        )

    rate_limit_key = f"login_{client_ip}_{payload.username_or_email}"
    if not check_rate_limit(rate_limit_key, limit=15, window_seconds=60):
        raise AuthenticationFailedException(
            "Too many login attempts for this account. Please wait 60 seconds before trying again."
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_email(payload.username_or_email)
    if not user or not verify_password(payload.password, user.hashed_password):
        # Generic response prevents username enumeration attacks
        raise AuthenticationFailedException("Invalid email/username or password")

    if not user.is_active:
        raise AuthenticationFailedException(
            "Your account is deactivated. Contact an Administrator."
        )

    # Record successful login timestamp
    user.last_login_at = datetime.now(UTC)
    db.commit()

    token = create_access_token(
        subject=user.email,
        role=user.role,
        user_id=user.id,
        token_version=user.token_version,
    )

    audit_repo = AuditRepository(db)
    audit_repo.log_event(
        action="LOGIN_SUCCESS",
        entity_type="user",
        entity_id=str(user.id),
        actor_id=user.id,
        details={"ip": client_ip},
    )
    db.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    """Fetch profile and permissions of the currently authenticated user."""
    return UserOut.model_validate(current_user)


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Acknowledge logout, revoke session token, and log audit event."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        raw_token = auth_header[7:].strip()
        try:
            payload = decode_access_token(raw_token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti:
                revoke_token(jti, exp)
            revoke_token(raw_token, exp)
        except Exception:
            revoke_token(raw_token)

    audit_repo = AuditRepository(db)
    audit_repo.log_event(
        action="LOGOUT",
        entity_type="user",
        entity_id=str(current_user.id),
        actor_id=current_user.id,
    )
    db.commit()
    return {"message": "Successfully logged out"}

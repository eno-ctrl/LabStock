from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import (
    AuthenticationFailedException,
    PermissionDeniedException,
    UserInactiveException,
)
from backend.app.core.security import decode_access_token
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.user import UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=True,
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate bearer JWT token and retrieve active database user."""
    payload = decode_access_token(token)
    user_id = payload.get("uid")
    if not user_id:
        raise AuthenticationFailedException("Token payload missing user identifier")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthenticationFailedException("User referenced by session no longer exists")

    if not user.is_active:
        raise UserInactiveException(
            "Account has been deactivated. Please contact an Administrator."
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency verifying that the user is authenticated and active."""
    return current_user


def require_roles(allowed_roles: list[UserRole]):
    """Factory creating an endpoint dependency checking permitted roles."""

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in [r.value for r in allowed_roles]:
            raise PermissionDeniedException(
                f"Your role ({current_user.role}) is not authorized to execute this operation. "
                f"Required: {[r.value for r in allowed_roles]}"
            )
        return current_user

    return role_checker


# Convenient role-bound dependencies
require_admin = require_roles([UserRole.ADMINISTRATOR])
require_inventory_manager = require_roles([UserRole.ADMINISTRATOR, UserRole.INVENTORY_MANAGER])
require_authenticated_viewer = require_roles(
    [
        UserRole.ADMINISTRATOR,
        UserRole.INVENTORY_MANAGER,
        UserRole.VIEWER,
    ]
)

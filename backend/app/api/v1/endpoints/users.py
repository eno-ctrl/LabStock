import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.exceptions import NotFoundException
from backend.app.core.permissions import require_admin
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.common import PaginatedResponse, PaginationMeta
from backend.app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("", response_model=PaginatedResponse[UserOut])
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Administrator-only: list all accounts with pagination."""
    skip = (page - 1) * page_size
    user_repo = UserRepository(db)
    users, total = user_repo.list_users(skip=skip, limit=page_size)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedResponse(
        items=[UserOut.model_validate(u) for u in users],
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Administrator-only: create a new user account with hashed credentials."""
    user_repo = UserRepository(db)
    new_user = user_repo.create(payload)

    audit_repo = AuditRepository(db)
    audit_repo.log_event(
        action="CREATE_USER",
        entity_type="user",
        entity_id=str(new_user.id),
        actor_id=admin.id,
        details={"email": new_user.email, "role": new_user.role},
    )
    db.commit()
    return UserOut.model_validate(new_user)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundException("User", user_id)
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Administrator-only: update user details, role assignment, or active state."""
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundException("User", user_id)

    updated = user_repo.update(user, payload, actor_id=admin.id)

    audit_repo = AuditRepository(db)
    audit_repo.log_event(
        action="UPDATE_USER",
        entity_type="user",
        entity_id=str(updated.id),
        actor_id=admin.id,
        details={"email": updated.email, "role": updated.role, "is_active": updated.is_active},
    )
    db.commit()
    return UserOut.model_validate(updated)

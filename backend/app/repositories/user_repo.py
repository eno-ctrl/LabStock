from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.exceptions import ConflictException
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserRole, UserUpdate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(func.lower(User.email) == email.lower().strip()).first()

    def count_active_admins(self) -> int:
        return (
            self.db.query(User)
            .filter(User.role == UserRole.ADMINISTRATOR.value, User.is_active.is_(True))
            .count()
        )

    def list_users(self, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
        query = self.db.query(User).order_by(User.id.asc())
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total

    def create(self, user_in: UserCreate) -> User:
        existing = self.get_by_email(user_in.email)
        if existing:
            raise ConflictException(
                code="USER_EMAIL_EXISTS",
                message=f"A user with email '{user_in.email}' already exists",
            )
        db_user = User(
            email=user_in.email.lower().strip(),
            full_name=user_in.full_name.strip(),
            hashed_password=get_password_hash(user_in.password),
            role=user_in.role.value,
            is_active=user_in.is_active,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update(self, user: User, user_in: UserUpdate, actor_id: int | None = None) -> User:
        # Prevent deactivating or demoting the last active administrator
        if user.role == UserRole.ADMINISTRATOR.value and user.is_active:
            will_deactivate = user_in.is_active is False
            will_demote = (
                user_in.role is not None and user_in.role.value != UserRole.ADMINISTRATOR.value
            )
            if will_deactivate or will_demote:
                active_admins = self.count_active_admins()
                if active_admins <= 1:
                    raise ConflictException(
                        code="LAST_ADMIN_PROTECTED",
                        message="Cannot deactivate or demote the last active Administrator in the system.",
                    )

        if user_in.full_name is not None:
            user.full_name = user_in.full_name.strip()
        if user_in.role is not None:
            user.role = user_in.role.value
        if user_in.is_active is not None:
            user.is_active = user_in.is_active
        if user_in.password is not None and user_in.password.strip():
            user.hashed_password = get_password_hash(user_in.password)

        self.db.commit()
        self.db.refresh(user)
        return user

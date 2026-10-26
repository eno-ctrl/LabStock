import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import contextlib

from backend.app.core.security import create_access_token
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.user import User
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.user import UserCreate, UserRole

# Isolated SQLite in-memory / file test database
TEST_DB_FILE = "test_isolated.db"
TEST_DATABASE_URL = f"sqlite:///./{TEST_DB_FILE}"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    if os.path.exists(TEST_DB_FILE):
        with contextlib.suppress(Exception):
            os.remove(TEST_DB_FILE)
    Base.metadata.create_all(bind=test_engine)
    yield
    if os.path.exists(TEST_DB_FILE):
        with contextlib.suppress(Exception):
            os.remove(TEST_DB_FILE)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db: Session) -> User:
    user_repo = UserRepository(db)
    user = user_repo.get_by_email("test_admin@labstock.edu")
    if not user:
        user = user_repo.create(
            UserCreate(
                email="test_admin@labstock.edu",
                full_name="Test Admin",
                password="AdminPassword123#",
                role=UserRole.ADMINISTRATOR,
                is_active=True,
            )
        )
    return user


@pytest.fixture
def manager_user(db: Session) -> User:
    user_repo = UserRepository(db)
    user = user_repo.get_by_email("test_manager@labstock.edu")
    if not user:
        user = user_repo.create(
            UserCreate(
                email="test_manager@labstock.edu",
                full_name="Test Manager",
                password="ManagerPassword123#",
                role=UserRole.INVENTORY_MANAGER,
                is_active=True,
            )
        )
    return user


@pytest.fixture
def viewer_user(db: Session) -> User:
    user_repo = UserRepository(db)
    user = user_repo.get_by_email("test_viewer@labstock.edu")
    if not user:
        user = user_repo.create(
            UserCreate(
                email="test_viewer@labstock.edu",
                full_name="Test Viewer",
                password="ViewerPassword123#",
                role=UserRole.VIEWER,
                is_active=True,
            )
        )
    return user


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    token = create_access_token(admin_user.email, admin_user.role, admin_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_headers(manager_user: User) -> dict:
    token = create_access_token(manager_user.email, manager_user.role, manager_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers(viewer_user: User) -> dict:
    token = create_access_token(viewer_user.email, viewer_user.role, viewer_user.id)
    return {"Authorization": f"Bearer {token}"}

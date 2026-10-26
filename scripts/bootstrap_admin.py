import argparse
import getpass
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.user import UserCreate, UserRole, UserUpdate


def bootstrap_admin(email: str, full_name: str, password: str):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        existing = user_repo.get_by_email(email)
        if existing:
            if existing.role != UserRole.ADMINISTRATOR.value or not existing.is_active:
                existing.role = UserRole.ADMINISTRATOR.value
                existing.is_active = True
                user_repo.update(
                    existing,
                    user_in=UserUpdate(
                        full_name=full_name,
                        password=password,
                        role=UserRole.ADMINISTRATOR,
                        is_active=True,
                    ),
                )
                print(f"Updated existing user '{email}' to active Administrator.")
            else:
                print(f"Administrator with email '{email}' already exists.")
            return

        new_admin = user_repo.create(
            UserCreate(
                email=email,
                full_name=full_name,
                password=password,
                role=UserRole.ADMINISTRATOR,
                is_active=True,
            )
        )
        print(f"Successfully bootstrapped Administrator '{new_admin.email}' (ID: {new_admin.id}).")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="LabStock Administrator Bootstrap Utility")
    parser.add_argument("--email", help="Administrator email address")
    parser.add_argument("--name", help="Administrator full name", default="Lab Administrator")
    parser.add_argument("--password", help="Administrator password (prompted if omitted)")

    args = parser.parse_args()

    email = args.email or input("Enter Administrator Email: ").strip()
    name = args.name or input("Enter Administrator Full Name: ").strip()
    password = args.password
    if not password:
        password = getpass.getpass("Enter Administrator Password (min 8 chars): ")
        confirm = getpass.getpass("Confirm Administrator Password: ")
        if password != confirm:
            print("Error: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters long.", file=sys.stderr)
        sys.exit(1)

    bootstrap_admin(email, name, password)


if __name__ == "__main__":
    main()

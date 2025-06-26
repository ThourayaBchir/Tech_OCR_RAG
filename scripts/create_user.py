import os
import sys
from getpass import getpass

from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load .env if present
load_dotenv()

# --- DB CONFIG from env ---
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# --- PASSWORD HASHER ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Import your SQLAlchemy Base and User model
from storage.db.models import Base, User  # Adjust import as needed


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/create_user.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    password = getpass("Password: ")

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Check if user exists
    if session.query(User).filter_by(username=username).first():
        print(f"User '{username}' already exists!")
        sys.exit(1)

    user = User(username=username, password_hash=hash_password(password))
    session.add(user)
    session.commit()
    print(f"User '{username}' created successfully.")


if __name__ == "__main__":
    main()

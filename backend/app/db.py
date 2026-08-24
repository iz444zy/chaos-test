import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


load_dotenv(Path(__file__).resolve().parent.parent / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recipe_dev.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def migrate_database() -> None:
    """Apply the additive ownership migration for SQLite databases created before Supabase auth."""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "supabase_user_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN supabase_user_id VARCHAR(36)"))
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_supabase_user_id "
                    "ON users (supabase_user_id)"
                )
            )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

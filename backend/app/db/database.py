import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/study_quiz",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables() -> None:
    Base.metadata.create_all(bind=engine)

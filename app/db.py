from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .config import get_settings

settings = get_settings()

engine = create_engine(f"sqlite:///{settings.db_path}", future=True, echo=False)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


def init_db():
    from . import models  # noqa: F401

    models.Base.metadata.create_all(bind=engine)

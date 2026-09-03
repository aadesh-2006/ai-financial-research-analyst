"""SQLAlchemy database session and engine setup."""
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import settings
from app.utils.logging import setup_logger

logger = setup_logger("database")


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""
    pass


def create_db_engine(db_url: Optional[str] = None, echo: bool = False):
    """Factory function to build a SQLAlchemy engine with appropriate dialect arguments."""
    url = db_url or settings.database_url
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        url,
        echo=echo,
        connect_args=connect_args,
        future=True,
    )


# Default application engine and sessionmaker
engine = create_db_engine(settings.database_url, settings.database_echo)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a SQLAlchemy session.
    Guarantees transaction rollback on error and session cleanup on request termination.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
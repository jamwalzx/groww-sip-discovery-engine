from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import DATABASE_URL
from src.db.models import Base

# SQLite configuration: check_same_thread=False allows multi-threaded access
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes all database tables defined in SQLAlchemy models."""
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db():
    """Context manager for safe database transactional sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


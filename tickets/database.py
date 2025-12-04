"""
Database setup and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import config
from tickets.models import Base


# Create engine
engine = create_engine(
    config.DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database - create all tables."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def get_db() -> Session:
    """Get a database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here - let caller manage


def close_db(db: Session):
    """Close a database session."""
    if db:
        db.close()

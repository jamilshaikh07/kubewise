import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from models.db import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kubewise.db")

is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

if is_sqlite:
    # Default SQLite journal mode takes an exclusive lock on every write,
    # blocking all reads until it completes -- with a periodic agent ingest
    # writing dozens of rows every few minutes, that was enough to stall the
    # dashboard's read queries for extended periods. WAL mode lets readers
    # and writers run concurrently (only writer-vs-writer is serialized).
    # busy_timeout is a safety net for that remaining writer-vs-writer case.
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

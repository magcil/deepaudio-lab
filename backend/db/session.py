import os
from sqlite3 import Connection as SQLite3Connection

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Configure database
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

is_sqlite = DATABASE_URL.startswith("sqlite")

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if is_sqlite else {},
)

@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Enable foreign key enforcement on new SQLite connections.

    SQLite parses ``FOREIGN KEY`` declarations but does not enforce them
    by default. This listener runs ``PRAGMA foreign_keys=ON`` on every
    new SQLite connection so that foreign key constraints, ``ON DELETE``
    cascades, and other referential integrity rules are actually applied.

    Args:
        dbapi_connection: The raw DB-API connection object that
            SQLAlchemy has just opened. 
        connection_record: SQLAlchemy's internal bookkeeping object
            for the connection in the pool; Required by the event signature.
    """
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    """Yield a database session for the duration of a single request.

    Yields:
        sqlalchemy.orm.Session: An active SQLAlchemy session bound to
            the configured engine.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
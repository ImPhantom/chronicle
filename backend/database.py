import datetime

from sqlalchemy import DateTime, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import TypeDecorator

SQLALCHEMY_DATABASE_URL = "sqlite:///./chronicle.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Thank you mike! https://mike.depalatis.net/blog/sqlalchemy-timestamps.html
class UTCDateTime(TypeDecorator):
    """DateTime that always stores and returns UTC-aware datetimes.

    SQLite has no native timezone support, so we store naive UTC strings and
    re-attach timezone.utc on read so Pydantic serialises them with a +00:00
    offset that JS can parse unambiguously.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=datetime.timezone.utc)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

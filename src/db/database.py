from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy import create_engine, event

from .database_path import get_database_path


database_path = get_database_path()

engine = create_engine(
    f"sqlite:///{database_path}",
    connect_args={
        "check_same_thread": False,
        "timeout": 10,
    },
)


@event.listens_for(engine, "connect")
def configure_sqlite(
    database_connection,
    connection_record,
) -> None:
    cursor = database_connection.cursor()

    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=10000")

    cursor.close()


class Base(DeclarativeBase):
    pass


SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def create_tables() -> None:
    from . import models

    Base.metadata.create_all(bind=engine)
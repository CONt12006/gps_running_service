from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def configure_database(database_path: Path) -> None:
    global engine
    global SessionLocal

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
        _connection_record,
    ) -> None:
        cursor = database_connection.cursor()

        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=10000")

        cursor.close()

    SessionLocal = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


def create_tables() -> None:
    if engine is None:
        raise RuntimeError(
            "Сначала вызови configure_database()"
        )

    from src.db import models

    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    if SessionLocal is None:
        raise RuntimeError(
            "База данных ещё не настроена"
        )

    return SessionLocal()
import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_sqlite_path() -> Path:
    return project_root() / "data" / "competitive_intelligence.db"


def default_database_url() -> str:
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        return configured_url
    return f"sqlite:///{default_sqlite_path().as_posix()}"


def create_database_engine(database_url: str | None = None) -> Engine:
    resolved_url = database_url or default_database_url()
    url = make_url(resolved_url)
    connect_args = {}
    engine_options = {}

    if url.drivername.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if url.database and url.database != ":memory:":
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        if url.database == ":memory:":
            engine_options["poolclass"] = StaticPool

    return create_engine(resolved_url, connect_args=connect_args, **engine_options)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    from app.storage import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def drop_db(engine: Engine) -> None:
    from app.storage import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

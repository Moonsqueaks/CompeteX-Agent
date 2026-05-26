from collections.abc import Generator
from contextlib import contextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from app.storage import create_database_engine, create_session_factory, init_db


@contextmanager
def repository_session(app: FastAPI) -> Generator[Session]:
    session_factory = get_session_factory(app)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_session_factory(app: FastAPI) -> sessionmaker[Session]:
    session_factory = getattr(app.state, "session_factory", None)
    if session_factory is not None:
        return session_factory

    database_url = getattr(app.state, "database_url", None)
    engine = create_database_engine(database_url)
    init_db(engine)
    session_factory = create_session_factory(engine)
    app.state.engine = engine
    app.state.session_factory = session_factory
    return session_factory

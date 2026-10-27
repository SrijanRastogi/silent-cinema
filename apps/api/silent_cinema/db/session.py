"""Database engine and session helpers.

The API and worker share this module. No global session is created; callers
open a short-lived session per unit of work.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class Database:
    """Owns one SQLAlchemy engine for the lifetime of the application."""

    def __init__(self, url: str) -> None:
        self.engine: Engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            connect_args={"connect_timeout": 3},
        )
        self._session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    def ping(self) -> None:
        """Execute a trivial query. Raises on any connection failure."""
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Provide a transaction-scoped ORM session."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self.engine.dispose()

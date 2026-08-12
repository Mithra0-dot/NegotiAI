"""Postgres connection + session plumbing (SQLAlchemy).

Must be Postgres, not SQLite — Render's disk is ephemeral and wipes on
redeploy/restart, so anything backed by a local file loses all history.
The one exception is the repository-layer unit tests (test_history.py,
test_eval_simulation.py), which use an in-memory SQLite purely as a
fast, dependency-free test fixture — they never touch the app's real
persistence path (app.config.settings.database_url), so this doesn't
conflict with that rule.

Naming note: SQLAlchemy's `Session` (a DB transaction/connection) and this
app's own "negotiation session" concept (SessionScore, SessionRecord) are
unfortunately overlapping vocabulary. Callers importing SQLAlchemy's
Session should alias it (`as DBSession`) to keep the two unambiguous.
"""

import logging
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url, pool_pre_ping=True)
# expire_on_commit=False: without it, every commit() marks all objects
# already fetched/added in that session as stale, requiring a fresh
# SELECT on next attribute access. Fine for a single-record-per-request
# handler (the object's used before the session ever closes), but
# eval/run_simulation.py's run_n_sessions() commits once per simulated
# session on one long-lived session, then hands the whole list of
# records back to its caller after closing it — with the default, every
# record but the last would raise DetachedInstanceError the moment its
# attributes were read. Harmless for the request-scoped path (get_db
# below) since nothing there depends on post-commit auto-refresh either.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """FastAPI dependency — yields a DB session, always closed after the
    request regardless of success/failure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables if they don't exist yet. Fine for this MVP's single
    table via plain create_all(); revisit with Alembic once the schema
    needs versioned migrations.

    Deliberately does not raise on failure (e.g. Postgres not running
    yet) — called once at FastAPI startup, and a DB outage shouldn't
    prevent the rest of the app (which doesn't all depend on history)
    from starting. Callers that do need the DB (the /chat persistence
    step, GET /sessions) fail on their own terms when they actually touch
    it, per their own docstrings.
    """
    from app.history import models  # noqa: F401 - registers SessionRecord on Base
    from eval import models as eval_models  # noqa: F401 - registers SimulatedSessionRecord on Base

    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        logger.exception(
            "Could not reach Postgres at startup (DATABASE_URL=%s). "
            "Session history will be unavailable until it's reachable — "
            "everything else keeps working. Start it with "
            "`docker compose up -d` (repo root) if you haven't.",
            settings.database_url,
        )

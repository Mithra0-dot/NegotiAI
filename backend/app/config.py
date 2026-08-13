"""App configuration, loaded from environment variables / backend/.env.

`anthropic_api_key` is intentionally optional here rather than required at
startup: if it's unset, the underlying Anthropic SDK still tries its own
credential resolution (ANTHROPIC_AUTH_TOKEN, an `ant auth login` profile,
Workload Identity Federation — see the Anthropic API docs' Authentication
section). We can't reliably detect those from Python config without
shelling out, so we don't fail fast here — a genuinely missing credential
surfaces as a clear error on the first real /chat call instead (see
app/agent/llm.py).
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    # Dev/demo toggle: skip the real Anthropic call and return a canned,
    # tactic-appropriate reply instead — see app/agent/mock.py. Lets the
    # full flow (including visible tone shifts as tactic escalates) be
    # tested without API credits.
    mock_llm: bool = False

    # Defaults to the local docker-compose Postgres (see repo-root
    # docker-compose.yml) so a fresh clone works with zero config beyond
    # `docker compose up -d`. Override via .env for anything else (e.g.
    # Render's Postgres URL in production). Must be Postgres, not SQLite
    # — see app/db.py's docstring.
    database_url: str = "postgresql+psycopg://negotiai:negotiai@localhost:5432/negotiai"

    @field_validator("database_url")
    @classmethod
    def _normalize_postgres_scheme(cls, value: str) -> str:
        """Render (and Heroku-style platforms) hand out connection strings
        prefixed `postgres://`. SQLAlchemy 1.4+/2.0 dropped that dialect
        name and rejects it outright (`NoSuchModuleError`) — confirmed
        directly against this project's installed SQLAlchemy version, not
        assumed. Rewritten to `postgresql+psycopg://`, not just
        `postgresql://`: a bare `postgresql://` URL resolves to
        SQLAlchemy's default driver, psycopg2 — which isn't installed
        here (requirements.txt has `psycopg[binary]`, i.e. psycopg3) and
        would fail with `ModuleNotFoundError` instead, just a different
        error at the same spot. Also normalizes an already-bare
        `postgresql://` for the same reason, in case one shows up without
        the `postgres://` prefix. A URL that already names a driver
        (`postgresql+psycopg://`, the default above) passes through
        untouched."""
        if value.startswith("postgres://"):
            return "postgresql+psycopg://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value.removeprefix("postgresql://")
        return value


settings = Settings()

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


settings = Settings()

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


settings = Settings()

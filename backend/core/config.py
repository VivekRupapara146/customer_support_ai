"""
Centralized application configuration.

All environment variables are loaded and validated here via Pydantic Settings.
No other module should read os.environ directly — import `settings` instead.
"""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "TechMart Support AI"
    environment: str = "development"
    log_level: str = "INFO"

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Database
    mongo_uri: str
    mongo_db_name: str = "techmart_support"

    # LLM
    gemini_api_key: str = ""

    # Demo auth credential (Milestone 10 hardening) — a single fixed
    # username + bcrypt-hashed password, NOT a real user system. Good
    # enough to stop anonymous strangers from minting tokens against a
    # public deployment; not a substitute for real accounts.
    demo_username: str = "demo"
    demo_password_hash: str = ""

    # Rate limiting
    rate_limit_default: str = "60/minute"

    # Router version: "rule_based" | "llm_based" | "trained_classifier"
    active_router: str = "rule_based"

    # CORS — comma-separated in .env, parsed to a list here
    cors_allowed_origins_raw: str = Field(default="http://localhost:3000", validation_alias="CORS_ALLOWED_ORIGINS")

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins_raw.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — .env is read once, not per-request."""
    return Settings()


settings = get_settings()

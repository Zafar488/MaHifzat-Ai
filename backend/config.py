"""Portable, explicit configuration. Production fails closed."""
from pathlib import Path
from typing import Literal
import secrets
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    PROJECT_ROOT: Path = ROOT
    ARTIFACTS_DIR: Path = ROOT / "artifacts"
    DATA_DIR: Path = ROOT / "data"
    APP_ENV: Literal["development", "test", "production"] = "development"
    APP_DEBUG: bool = False
    DEMO_MODE: bool = False
    # New development DB; original backend/maahifazat.db is never opened by default.
    DATABASE_URL: str = f"sqlite+aiosqlite:///{ROOT / 'data' / 'local-app.db'}"
    JWT_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = Field(60, ge=1, le=1440)
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    LLM_TIMEOUT_SECONDS: float = Field(25, ge=1, le=60)
    OVERPASS_URL: str = "https://overpass.private.coffee/api/interpreter"
    OSM_MAP_FALLBACK_URL: str = "https://api.openstreetmap.org/api/0.6/map.json"
    HOSPITAL_SEARCH_TIMEOUT_SECONDS: float = Field(25, ge=1, le=60)
    ENABLE_LLM: bool = False
    APP_NAME: str = "MaaHifazat AI"
    APP_VERSION: str = "2.0.0"
    REQUIRE_MODELS: bool = True
    FACILITY_DIRECTORY_PATH: Path | None = None
    FACILITY_VERIFICATION_MAX_DAYS: int = Field(365, ge=1, le=3650)
    OPENROUTESERVICE_API_KEY: str = ""
    ROUTING_TIMEOUT_SECONDS: float = Field(8, ge=1, le=30)
    FOLLOWUP_TIMEZONE: str = "Asia/Karachi"

    @model_validator(mode="after")
    def production_requirements(self):
        if self.APP_ENV == "production":
            if "JWT_SECRET" not in self.model_fields_set or len(self.JWT_SECRET) < 32:
                raise ValueError("Production requires an explicit JWT_SECRET of at least 32 characters")
            if not self.DATABASE_URL.startswith("postgresql+asyncpg://"):
                raise ValueError("Production requires a persistent PostgreSQL DATABASE_URL")
            if self.DEMO_MODE or self.APP_DEBUG or "*" in self.CORS_ORIGINS:
                raise ValueError("Production disallows demo/debug and wildcard CORS")
        return self


settings = Settings()

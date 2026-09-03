"""Application configuration using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

# Resolve project root relative to this file (works on any machine / Vercel)
_HERE = Path(__file__).parent          # backend/
_ROOT = _HERE.parent                   # project root


class Settings(BaseSettings):
    # Project paths (relative to repo root — portable across machines)
    PROJECT_ROOT: Path = _ROOT
    ARTIFACTS_DIR: Path = _ROOT / "artifacts"
    DATA_DIR: Path = _ROOT / "data"

    # Model paths
    FETALWATCH_MODEL: Path = _ROOT / "artifacts/fetalwatch/best_model.joblib"
    MATERNALGUARD_MODEL: Path = _ROOT / "artifacts/maternalguard/best_model.joblib"
    MATERNALGUARD_ENCODER: Path = _ROOT / "artifacts/maternalguard/label_encoder.joblib"
    PRETERMGUARD_MODEL: Path = _ROOT / "artifacts/pretermguard/best_model.joblib"
    CAREREACH_MODEL: Path = _ROOT / "artifacts/carereach/best_model.joblib"
    CAREREACH_PREPROCESSOR: Path = _ROOT / "artifacts/carereach/preprocessor.joblib"
    GESTATIONINSIGHT_MODEL: Path = _ROOT / "artifacts/gestationinsight/best_model.joblib"
    GESTATIONINSIGHT_ENCODER: Path = _ROOT / "artifacts/gestationinsight/label_encoder.joblib"

    # Database (relative path — works locally and on Vercel /tmp)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{_ROOT / 'backend' / 'maahifazat.db'}"

    # JWT Auth
    JWT_SECRET: str = "maahifazat-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # External APIs (stubs for now)
    VOICE_API_URL: str = "http://localhost:8001/voice"
    FACILITY_API_URL: str = "https://overpass-api.de/api/interpreter"
    ROUTING_API_URL: str = "https://api.openrouteservice.org"
    MESSAGING_API_URL: str = "http://localhost:8002/messaging"

    # Groq LLM API
    # NOTE: "llama-3.3-70b-versatile" is not available on this Groq account
    # (404 model_not_found). "openai/gpt-oss-120b" is Groq's flagship
    # replacement and is what this key has access to.
    GROQ_API_KEY: str = ""  # Set via GROQ_API_KEY env var or .env file
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # App settings
    APP_NAME: str = "MaaHifazat AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

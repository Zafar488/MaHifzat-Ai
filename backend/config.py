"""Application configuration using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    # Project paths
    PROJECT_ROOT: Path = Path("g:/hackthon")
    ARTIFACTS_DIR: Path = Path("g:/hackthon/artifacts")
    DATA_DIR: Path = Path("g:/hackthon/data")

    # Model paths
    FETALWATCH_MODEL: Path = Path("g:/hackthon/artifacts/fetalwatch/best_model.joblib")
    MATERNALGUARD_MODEL: Path = Path("g:/hackthon/artifacts/maternalguard/best_model.joblib")
    MATERNALGUARD_ENCODER: Path = Path("g:/hackthon/artifacts/maternalguard/label_encoder.joblib")
    PRETERMGUARD_MODEL: Path = Path("g:/hackthon/artifacts/pretermguard/best_model.joblib")
    CAREREACH_MODEL: Path = Path("g:/hackthon/artifacts/carereach/best_model.joblib")
    CAREREACH_PREPROCESSOR: Path = Path("g:/hackthon/artifacts/carereach/preprocessor.joblib")
    GESTATIONINSIGHT_MODEL: Path = Path("g:/hackthon/artifacts/gestationinsight/best_model.joblib")
    GESTATIONINSIGHT_ENCODER: Path = Path("g:/hackthon/artifacts/gestationinsight/label_encoder.joblib")

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///g:/hackthon/backend/maahifazat.db"

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

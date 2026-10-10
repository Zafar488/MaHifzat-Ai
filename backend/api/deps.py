"""Dependency injection helpers for FastAPI routes."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.engine import AsyncSessionLocal
from backend.services.inference import ModelRegistry
from backend.services.safety import SafetyService, get_safety_service as _get_safety


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session (auto-commit / rollback)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# ML model registry
# ---------------------------------------------------------------------------


def get_model_registry() -> ModelRegistry:
    """Return the singleton ModelRegistry (models loaded at startup)."""
    registry = ModelRegistry()
    registry.load_all()
    return registry


# ---------------------------------------------------------------------------
# Safety service
# ---------------------------------------------------------------------------


def get_safety_service() -> SafetyService:
    """Return the process-wide SafetyService singleton."""
    return _get_safety()

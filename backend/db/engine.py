"""Async sessions; SQL logs disabled and SQLite foreign keys enforced."""
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(connection, record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    from backend.db import models  # register metadata
    if settings.APP_ENV == "production":
        # Production schemas are managed by Alembic, never implicit startup DDL.
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

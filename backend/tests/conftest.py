"""Synthetic identities and in-memory DB. Never opens the user database."""
import os
os.environ["APP_ENV"] = "test"
os.environ["ENABLE_LLM"] = "false"
os.environ["DEMO_MODE"] = "false"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.db.models import Base, User
from backend.api.main import app
from backend.api.deps import get_db
from backend.api.auth import _hash_password
from backend.services.inference import ModelRegistry

engine = create_async_engine("sqlite+aiosqlite://", echo=False)
@event.listens_for(engine.sync_engine, "connect")
def foreign_keys(conn, record):
    conn.execute("PRAGMA foreign_keys=ON")
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def async_client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        for role in ("admin", "clinician", "lhw", "patient"):
            session.add(User(id="test-" + role, username=role, full_name="Synthetic " + role, role=role, hashed_password=_hash_password("Synthetic-test-pass!")))
        await session.commit()
    app.dependency_overrides[get_db] = override_get_db
    ModelRegistry().load_all()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def login_as(client, role):
    r = await client.post("/api/auth/login", data={"username": role, "password": "Synthetic-test-pass!"})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}


@pytest_asyncio.fixture
async def auth_headers(async_client):
    return await login_as(async_client, "admin")


@pytest_asyncio.fixture
async def patient_id(async_client, auth_headers):
    r = await async_client.post("/api/patients", json={"name": "Synthetic Patient", "age": 30}, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()["patient_id"]

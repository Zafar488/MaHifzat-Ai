"""Seed isolated synthetic demo identities. Never run against a real patient database."""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from backend.config import settings
from backend.db.engine import init_db, AsyncSessionLocal, engine
from backend.db.models import User
from backend.api.auth import _hash_password

DEMO_PASSWORD = "MaaHifazat-Demo-2026!"
async def seed():
    if not settings.DEMO_MODE or settings.APP_ENV != "development" or not settings.DATABASE_URL.endswith("demo-app.db"):
        raise RuntimeError("Demo seed requires development DEMO_MODE and the isolated demo-app.db")
    await init_db()
    async with AsyncSessionLocal() as db:
        for role in ("admin", "clinician", "lhw"):
            username = "demo-" + role
            if not await db.scalar(select(User.id).where(User.username == username)):
                db.add(User(id=username, username=username, full_name="Demo " + role, role=role, hashed_password=_hash_password(DEMO_PASSWORD)))
        await db.commit()
    await engine.dispose()
if __name__ == "__main__":
    asyncio.run(seed())
    print("Synthetic demo accounts ready in data/demo-app.db")

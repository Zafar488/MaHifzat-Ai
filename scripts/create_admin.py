"""Provision a staff administrator locally; passwords are entered privately."""
import asyncio
import getpass
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.api.auth import SignupRequest,create_user
from backend.db.engine import init_db,AsyncSessionLocal
from backend.schemas.auth import UserRole

async def main():
    await init_db()
    username=input("Admin username: ").strip()
    name=input("Full name: ").strip()
    password=getpass.getpass("Password (12+ characters): ")
    if password!=getpass.getpass("Confirm password: "):raise ValueError("Passwords do not match")
    async with AsyncSessionLocal() as db:
        await create_user(db,SignupRequest(username=username,password=password,full_name=name,role=UserRole.ADMIN))
        await db.commit()
    print("Admin created. Sign in and provision clinician/health-worker accounts.")
if __name__=="__main__":asyncio.run(main())

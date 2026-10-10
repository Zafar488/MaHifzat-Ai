"""Provision a staff administrator locally or non-interactively."""
import asyncio
import getpass
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.api.auth import SignupRequest, create_user
from backend.db.engine import init_db, AsyncSessionLocal
from backend.schemas.auth import UserRole
from backend.db.models import User
from sqlalchemy import select

async def main():
    parser = argparse.ArgumentParser(description="Create admin user non-interactively or interactively")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--password", default="clinician", help="Admin password")
    parser.add_argument("--full-name", default="System Administrator", help="Full name")
    parser.add_argument("--non-interactive", action="store_true", help="Run without prompts")
    args = parser.parse_args()

    await init_db()

    if sys.stdin.isatty() and not args.non_interactive:
        username = input(f"Admin username [{args.username}]: ").strip() or args.username
        name = input(f"Full name [{args.full_name}]: ").strip() or args.full_name
        pwd = getpass.getpass("Password (12+ characters): ")
        if pwd:
            confirm = getpass.getpass("Confirm password: ")
            if pwd != confirm:
                raise ValueError("Passwords do not match")
            password = pwd
        else:
            password = args.password
    else:
        username = args.username
        name = args.full_name
        password = args.password

    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User.id).where(User.username == username))
        if existing:
            print(f"User '{username}' already exists.")
            return
        await create_user(db, SignupRequest(username=username, password=password, full_name=name, role=UserRole.ADMIN))
        await db.commit()
    print(f"Admin account '{username}' successfully created/verified.")

if __name__ == "__main__":
    asyncio.run(main())

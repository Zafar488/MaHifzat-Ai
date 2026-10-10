"""Run the real local backend application and Vite frontend server."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    env = {
        **os.environ,
        "APP_ENV": "development",
        "DEMO_MODE": "false",
        "BACKEND_URL": "http://127.0.0.1:8000",
        "PYTHONIOENCODING": "utf-8",
    }
    children = []
    try:
        # 1. FastAPI backend server
        children.append(
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "backend.api.main:app", "--host", "127.0.0.1", "--port", "8000"],
                cwd=ROOT,
                env=env,
            )
        )
        print("MaaHifazat AI Backend running at http://127.0.0.1:8000", flush=True)
        while all(p.poll() is None for p in children):
            try:
                children[0].wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
    except KeyboardInterrupt:
        pass
    finally:
        for p in children:
            if p.poll() is None:
                p.terminate()
        for p in children:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()

if __name__ == "__main__":
    main()

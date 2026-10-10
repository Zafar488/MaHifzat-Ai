"""Start the isolated demo API and Streamlit UI. Ctrl+C stops both children."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def main():
    env = {**os.environ, "APP_ENV": "development", "DEMO_MODE": "true", "ENABLE_LLM": "false",
           "DATABASE_URL": "sqlite+aiosqlite:///" + (ROOT / "data/demo-app.db").as_posix(),
           "BACKEND_URL": "http://127.0.0.1:8000", "PYTHONIOENCODING": "utf-8"}
    subprocess.run([sys.executable, str(ROOT / "scripts/bootstrap_demo.py")], cwd=ROOT, env=env, check=True)
    children = []
    try:
        children.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.api.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd=ROOT, env=env))
        children.append(subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py", "--server.address", "127.0.0.1",
             "--server.port", "8501", "--server.headless", "true", "--browser.gatherUsageStats", "false"], cwd=ROOT, env=env))
        print("Open http://localhost:8501 | login: demo-clinician | password: MaaHifazat-Demo-2026!")
        while all(p.poll() is None for p in children):
            try: children[0].wait(timeout=1)
            except subprocess.TimeoutExpired: pass
    except KeyboardInterrupt:
        pass
    finally:
        for process in children:
            if process.poll() is None: process.terminate()
        for process in children:
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.kill()
if __name__ == "__main__":
    main()

"""Run the real local application; no seed accounts or fictional hospitals."""
import os
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    env={**os.environ,"APP_ENV":"development","DEMO_MODE":"false",
         "BACKEND_URL":"http://127.0.0.1:8000","PYTHONIOENCODING":"utf-8"}
    # Settings reads existing .env credentials. Do not print them.
    children=[]
    try:
        for args in ([sys.executable,"-m","uvicorn","backend.api.main:app","--host","127.0.0.1","--port","8000"],
                     [sys.executable,"-m","streamlit","run","app.py","--server.address","127.0.0.1","--server.port","8501","--server.headless","true","--browser.gatherUsageStats","false"]):
            children.append(subprocess.Popen(args,cwd=ROOT,env=env))
        print("MaaHifazat running at http://localhost:8501 | Create an account to begin",flush=True)
        while all(p.poll() is None for p in children):
            try:children[0].wait(timeout=1)
            except subprocess.TimeoutExpired:pass
    except KeyboardInterrupt:pass
    finally:
        for p in children:
            if p.poll() is None:p.terminate()
        for p in children:
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.kill()
if __name__=="__main__":main()

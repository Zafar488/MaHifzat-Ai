"""
Vercel serverless entrypoint.
Imports the FastAPI app so Vercel's Python runtime can serve it.
"""
import sys
import os

# Make the project root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api.main import app  # noqa: F401 – Vercel picks up 'app'

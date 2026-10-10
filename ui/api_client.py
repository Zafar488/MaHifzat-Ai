"""Thin client; all patient data and decisions go through scoped FastAPI endpoints."""
import os
import httpx

class APIError(Exception):
    def __init__(self,message,status_code=None):
        super().__init__(message)
        self.status_code=status_code

class APIClient:
    def __init__(self, token=None):
        self.base_url = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
        self.token = token
    def request(self, method, path, **kwargs):
        headers = {"Authorization": "Bearer " + self.token} if self.token else {}
        try:
            with httpx.Client(base_url=self.base_url, timeout=100) as client:
                response = client.request(method, "/api" + path, headers=headers, **kwargs)
        except httpx.RequestError:
            raise APIError("Backend is unreachable. Start it with scripts/start_app.py or run uvicorn.")
        if response.status_code >= 400:
            if response.status_code == 401:
                raise APIError("Session expired or credentials incorrect. Sign in again.",status_code=401)
            try:
                body = response.json()
                detail = body.get("detail", body.get("error", "Request failed"))
                if isinstance(detail, list):
                    detail = "; ".join(f"{'.'.join(map(str, e.get('loc', [])))}: {e.get('msg')}" for e in detail)
            except ValueError:
                detail = "Request failed"
            raise APIError(f"{response.status_code}: {detail}")
        return response.json()

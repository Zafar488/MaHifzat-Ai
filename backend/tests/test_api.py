"""Integration tests for FastAPI endpoints (end-to-end with test DB)."""
import uuid
import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """GET /api/health returns 200 with status ok."""
    resp = await async_client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "models" in body


@pytest.mark.asyncio
async def test_login(async_client: AsyncClient):
    """POST /api/auth/login with admin/admin returns a JWT token."""
    resp = await async_client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "admin"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_create_patient(async_client: AsyncClient, auth_headers: dict):
    """POST /api/patients with auth headers returns 201."""
    payload = {
        "name": "Test Patient",
        "age": 28,
        "gender": "female",
        "phone": "+923001234567",
        "location": "Peshawar",
        "gestational_age_weeks": 28.0,
        "parity": 2,
        "language": "ur",
        "channel": "app",
    }
    resp = await async_client.post(
        "/api/patients",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 201, f"Create patient failed: {resp.text}"
    body = resp.json()
    assert body["name"] == "Test Patient"
    assert "patient_id" in body


@pytest.mark.asyncio
async def test_get_patient(async_client: AsyncClient, auth_headers: dict):
    """GET /api/patients/{id} returns 200 for an existing patient."""
    # Create a patient first
    create_payload = {
        "name": "Get Test Patient",
        "age": 25,
        "gender": "female",
    }
    create_resp = await async_client.post(
        "/api/patients",
        json=create_payload,
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    patient_id = create_resp.json()["patient_id"]

    # Fetch the patient
    resp = await async_client.get(
        f"/api/patients/{patient_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["patient_id"] == patient_id
    assert body["name"] == "Get Test Patient"


@pytest.mark.asyncio
async def test_risk_assess(async_client: AsyncClient, auth_headers: dict):
    """POST /api/risks/assess with vitals returns risk_level."""
    payload = {
        "patient_id": f"test-{uuid.uuid4()}",
        "vitals": {
            "Age": 30,
            "SystolicBP": 120,
            "DiastolicBP": 80,
            "BS": 7.0,
            "BodyTemp": 98.6,
            "HeartRate": 76,
        },
    }
    resp = await async_client.post(
        "/api/risks/assess",
        json=payload,
        headers=auth_headers,
    )
    assert resp.status_code == 200, f"Risk assess failed: {resp.text}"
    body = resp.json()
    assert "case_id" in body
    assert "maternal_risk" in body
    assert body["maternal_risk"] is not None
    assert "risk_level" in body["maternal_risk"]


@pytest.mark.asyncio
async def test_model_health(async_client: AsyncClient, auth_headers: dict):
    """GET /api/analytics/models/health returns model statuses."""
    resp = await async_client.get(
        "/api/analytics/models/health",
        headers=auth_headers,
    )
    assert resp.status_code == 200, f"Model health failed: {resp.text}"
    body = resp.json()
    assert "models" in body
    assert "all_loaded" in body
    assert "loaded_count" in body
    assert "total_count" in body
    assert body["total_count"] == 5


@pytest.mark.asyncio
async def test_unauthorized_access(async_client: AsyncClient):
    """GET /api/audit/logs without token returns 401."""
    resp = await async_client.get("/api/audit/logs")
    assert resp.status_code == 401

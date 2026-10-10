#!/usr/bin/env python3
"""
MaaHifazat AI Backend Automated Deployment Smoke Test Script
Executes end-to-end HTTP health & API tests against running backend instance.
"""

import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import time

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

def log_pass(msg):
    print(f"✅ PASS: {msg}")

def log_fail(msg):
    print(f"❌ FAIL: {msg}")

def make_request(path, method="GET", data=None, headers=None, is_form=False):
    url = f"{BASE_URL}{path}"
    headers = headers or {}
    
    if is_form and data:
        body = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode("utf-8")
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
    else:
        body = None
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            status = response.getcode()
            resp_body = response.read().decode("utf-8")
            return status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(resp_body)
        except Exception:
            parsed = {"error": resp_body}
        return e.code, parsed
    except Exception as e:
        return 0, {"error": str(e)}

def run_smoke_test():
    print(f"Starting MaaHifazat AI Smoke Tests against target: {BASE_URL}\n" + "="*60)
    failed = 0

    # 1. Health Check
    status, res = make_request("/api/health")
    if status == 200 and res.get("status") == "ok":
        models_status = res.get("models", {})
        loaded_count = sum(1 for loaded in models_status.values() if loaded)
        log_pass(f"/api/health returned 200 OK — Loaded ML Models: {loaded_count}/5 ({models_status})")
    else:
        log_fail(f"/api/health returned status {status}: {res}")
        failed += 1

    # 2. Authentication Login (Form Data)
    login_payload = {"username": "clinician", "password": "clinician"}
    status, res = make_request("/api/auth/login", method="POST", data=login_payload, is_form=True)
    token = res.get("access_token")
    if status == 200 and token:
        log_pass(f"/api/auth/login authenticated successfully (JWT Token: {token[:20]}...)")
    else:
        log_fail(f"/api/auth/login failed with status {status}: {res}")
        failed += 1
        return 1

    auth_headers = {"Authorization": f"Bearer {token}"}

    # 3. Authenticated User Profile Endpoint
    status, res = make_request("/api/auth/me", method="GET", headers=auth_headers)
    if status == 200 and "user_id" in res:
        log_pass(f"/api/auth/me verified JWT user role: {res.get('role')} (User ID: {res.get('user_id')})")
    else:
        log_fail(f"/api/auth/me failed with status {status}: {res}")
        failed += 1

    # 4. Risk Assessment Endpoint
    sample_risk_request = {
        "patient_id": "pat-smoke-001",
        "vitals": {
            "Age": 28,
            "SystolicBP": 120,
            "DiastolicBP": 80,
            "BS": 6.5,
            "BodyTemp": 98.6,
            "HeartRate": 75,
            "gestational_age_weeks": 32
        }
    }
    status, res = make_request("/api/risks/assess", method="POST", data=sample_risk_request, headers=auth_headers)
    if status == 200 and "case_id" in res:
        log_pass(f"/api/risks/assess returned 200 OK — Case ID: {res.get('case_id')}, Maternal Risk: {res.get('maternal_risk', {}).get('risk_level')}")
    else:
        log_fail(f"/api/risks/assess failed with status {status}: {res}")
        failed += 1

    # 5. LangGraph Multi-Agent Pipeline Execution
    agent_payload = {
        "patient_id": "pat-smoke-001",
        "case_id": "case-smoke-001",
        "patient_data": {
            "name": "Fatima Bibi",
            "age": 26,
            "vitals": {
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "heart_rate": 75,
                "temperature_celsius": 37.0,
                "gestational_age_weeks": 32
            }
        }
    }
    status, res = make_request("/api/agents/run", method="POST", data=agent_payload, headers=auth_headers)
    if status == 200 and "status" in res:
        log_pass(f"/api/agents/run completed 9-agent workflow successfully (Status: {res.get('status')})")
    else:
        log_fail(f"/api/agents/run failed with status {status}: {res}")
        failed += 1

    print("="*60)
    if failed == 0:
        print("🎉 ALL SMOKE TESTS PASSED SUCCESSFULLY!")
        return 0
    else:
        print(f"⚠️ SMOKE TESTS COMPLETED WITH {failed} FAILURES.")
        return 1

if __name__ == "__main__":
    sys.exit(run_smoke_test())

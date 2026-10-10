"""Tests for Section B Pregnancy Helper RAG, danger sign triage, and API endpoints."""
import pytest
from backend.services.pregnancy_rag import (
    retrieve_guidelines,
    check_urgent_symptoms,
    generate_pregnancy_advice,
    CURATED_GUIDELINES
)


def test_curated_guidelines_structure():
    assert len(CURATED_GUIDELINES) >= 6
    for g in CURATED_GUIDELINES:
        assert g["id"] and g["source"] and g["guideline"] and g["url"]
        assert "content_en" in g and "content_ur" in g
        assert len(g["topics"]) >= 1


def test_retrieve_guidelines():
    # Nutrition query
    results = retrieve_guidelines("What iron and folic acid supplements should I take in pregnancy?")
    assert len(results) >= 1
    assert any("nutrition" in g["topics"] or "iron" in g["topics"] for g in results)

    # Pre-eclampsia / BP query
    results_bp = retrieve_guidelines("High blood pressure headache preeclampsia")
    assert len(results_bp) >= 1
    assert any("blood pressure" in g["topics"] or "preeclampsia" in g["topics"] for g in results_bp)


def test_danger_sign_detection():
    # Bleeding trigger
    urgent_bleeding = check_urgent_symptoms("I have severe vaginal bleeding and stomach pain")
    assert urgent_bleeding is not None
    assert urgent_bleeding["is_urgent"] is True
    assert "bleeding" in urgent_bleeding["reason_en"].lower()

    # Pre-eclampsia trigger
    urgent_headache = check_urgent_symptoms("I have severe headache and blurry vision flashing lights")
    assert urgent_headache is not None
    assert urgent_headache["is_urgent"] is True

    # Safe general question
    safe_q = check_urgent_symptoms("Can I eat yogurt and apples during pregnancy?")
    assert safe_q is None


@pytest.mark.asyncio
async def test_generate_pregnancy_advice_with_shared_assessment():
    shared_assessment = {
        "vitals": {
            "gestational_age_weeks": 32,
            "systolic_bp": 150,
            "diastolic_bp": 95,
            "heart_rate": 88,
            "temperature_celsius": 36.8
        },
        "clinical_risk_result": {
            "who_red_flags": {"triage_level": "MODERATE_HYPERTENSION"}
        },
        "referral_result": {
            "selected_facility": {"name": "Peshawar Maternity Hospital"}
        }
    }
    advice = await generate_pregnancy_advice(
        query="What does my blood pressure reading mean?",
        language="en",
        shared_assessment=shared_assessment
    )
    assert "answer" in advice
    assert len(advice["citations"]) >= 1
    assert advice["language"] == "en"


@pytest.mark.asyncio
async def test_helper_api_endpoints(async_client, auth_headers):
    # Test chat endpoint
    chat_resp = await async_client.post(
        "/api/helper/chat",
        json={
            "query": "Is light walking safe during second trimester?",
            "language": "en"
        },
        headers=auth_headers
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert "answer" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)

    # Test public search endpoint
    search_resp = await async_client.post(
        "/api/helper/search",
        json={"query": "maternity hospital Peshawar contacts"},
        headers=auth_headers
    )
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert "results" in search_data

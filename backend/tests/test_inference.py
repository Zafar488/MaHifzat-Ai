"""Estimator invocation, artifact parity, absence and explicit units."""
from pathlib import Path
import copy
import json
import pytest
from pydantic import ValidationError
from backend.services.inference import ModelRegistry, MATERNAL_FEATURES, CTG_FEATURES
from backend.services.safety import SafetyService
from backend.schemas.clinical import ClinicalInput
from scripts.export_contract import render
from scripts.run_models import ROOT


def test_model_readiness_complete_pipelines():
    r = ModelRegistry()
    r.load_all()
    assert r.health_check() == {"maternalguard": True, "fetalwatch": True, "pretermguard": False, "gestationinsight": False, "carereach": False}


@pytest.mark.parametrize("name,features", [("maternalguard", MATERNAL_FEATURES), ("fetalwatch", CTG_FEATURES)])
def test_training_serving_parity_and_estimator_called(name, features, monkeypatch):
    r = ModelRegistry()
    r.load_all()
    bundle = r._models[name]
    calls = []
    estimator = bundle["pipeline"].named_steps["estimator"]
    old_predict, old_proba = estimator.predict, estimator.predict_proba
    monkeypatch.setattr(estimator, "predict", lambda *args, **kwargs: (calls.append("predict"), old_predict(*args, **kwargs))[1])
    monkeypatch.setattr(estimator, "predict_proba", lambda *args, **kwargs: (calls.append("predict_proba"), old_proba(*args, **kwargs))[1])
    sample = dict(zip(features, bundle["known_input"]))
    result = r.predict_maternal_risk(sample) if name == "maternalguard" else r.predict_fetal_health(sample)
    key = "risk_level" if name == "maternalguard" else "fetal_status"
    assert result[key] == bundle["label_map"][bundle["known_prediction"]]
    assert list(result["probabilities"].values()) == pytest.approx(bundle["known_probabilities"])
    assert "predict" in calls and "predict_proba" in calls
    assert result["confidence"] is None


def test_failing_estimator_cannot_return_prediction(monkeypatch):
    r = ModelRegistry()
    r.load_all()
    bundle = r._models["maternalguard"]
    def fail(x):
        raise RuntimeError("Estimator unavailable")
    monkeypatch.setattr(bundle["pipeline"].named_steps["estimator"], "predict", fail)
    result = r.predict_maternal_risk(dict(zip(MATERNAL_FEATURES, bundle["known_input"])))
    assert result["model_available"] is False and result["status"] == "error"


def test_absent_and_incompatible_artifacts(monkeypatch):
    r = ModelRegistry()
    r.load_all()
    monkeypatch.setattr(r, "_models", {})
    assert not any(r.health_check().values())
    assert r.predict_maternal_risk({})["status"] == "unavailable"
    for fn in (r.predict_preterm_risk, r.predict_gestational_complication, r.predict_anc_followup_risk):
        assert fn({})["model_available"] is False


def test_missing_measured_features_abstains():
    r = ModelRegistry()
    r.load_all()
    assert r.predict_maternal_risk({"systolic_bp": 180})["status"] == "insufficient_data"
    assert r.predict_fetal_health({"LB": 130})["status"] == "insufficient_data"


@pytest.mark.parametrize("sign", ["Convulsions", "Vaginal bleeding", "Severe headache", "Visual changes", "Reduced fetal movement"])
def test_danger_sign_without_vitals(sign):
    result = SafetyService().check_who_red_flags({}, [{"name": sign, "severity": "severe"}])
    assert result["is_emergency"] is True


def test_unknown_vitals_not_normal():
    result = SafetyService().check_who_red_flags({})
    assert result["triage_level"] == "INSUFFICIENT_DATA"
    assert result["missing_fields"]


def test_explicit_unit_conversions():
    v = ClinicalInput.model_validate({"blood_sugar": 180.182, "blood_sugar_unit": "mg/dL", "temperature": 98.6, "temperature_unit": "F"})
    assert v.blood_sugar_mmol_l == pytest.approx(10)
    assert v.temperature_celsius == pytest.approx(37)
    legacy = ClinicalInput.model_validate({"BS": 10, "BodyTemp": 98.6})
    assert legacy == v
    assert v.maternal_features()["BodyTemp"] == pytest.approx(98.6)


def test_contract_generated_from_authoritative_schema():
    assert (ROOT / "docs/contracts/clinical.generated.ts").read_text(encoding="utf-8") == render()


@pytest.mark.parametrize("name", ["maternalguard", "fetalwatch"])
def test_saved_splits_do_not_share_feature_groups(name):
    import pandas as pd
    manifest = json.loads((ROOT / "artifacts/serving" / name / "manifest.json").read_text())
    features = MATERNAL_FEATURES if name == "maternalguard" else CTG_FEATURES
    df = pd.read_parquet(ROOT / "data" / manifest["dataset"])
    groups = pd.util.hash_pandas_object(df[features].astype(float), index=False)
    assert not set(groups.iloc[manifest["train_indices"]]) & set(groups.iloc[manifest["test_indices"]])
    assert manifest["train_test_group_overlap"] == 0

def test_direct_ctg_boolean_and_absent_input_abstain():
    r=ModelRegistry()
    r.load_all()
    assert r.predict_fetal_health({"AC":True})["status"]=="error"
    assert r.predict_fetal_health(None)["status"]=="insufficient_data"

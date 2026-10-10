"""Versioned complete-pipeline serving. Legacy bare estimators are never served."""
from functools import lru_cache
from pathlib import Path
import logging
import joblib
import numpy as np
import pandas as pd
import sklearn
from backend.config import settings
from backend.schemas.clinical import ClinicalInput

logger = logging.getLogger(__name__)
MATERNAL_FEATURES = ["Age", "SystolicBP", "DiastolicBP", "BS", "BodyTemp", "HeartRate"]
CTG_FEATURES = ["LB", "AC", "FM", "UC", "DL", "DS", "DP", "ASTV", "MSTV", "ALTV", "MLTV", "Width", "Min", "Max", "Nmax", "Nzeros", "Mode", "Mean", "Median", "Variance", "Tendency"]
DISABLED = {
    "pretermguard": "No labelled preterm-birth outcome dataset or validated model.",
    "gestationinsight": "Pima diabetes proxy is not an observed pregnancy-complication outcome.",
    "carereach": "General appointment cohort is not a validated ANC population.",
}


class ModelRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models = {}
            cls._instance._errors = {}
            cls._instance._loaded = False
        return cls._instance

    def load_all(self):
        if self._loaded:
            return
        for name, features in (("maternalguard", MATERNAL_FEATURES), ("fetalwatch", CTG_FEATURES)):
            path = settings.ARTIFACTS_DIR / "serving" / name / "pipeline-v1.joblib"
            try:
                bundle = joblib.load(path)
                self._validate(bundle, features)
                self._models[name] = bundle
            except Exception as exc:
                self._errors[name] = "Complete compatible pipeline unavailable; rebuild with scripts/run_models.py."
                logger.warning("Pipeline %s unavailable (%s)", name, type(exc).__name__)
        self._loaded = True

    @staticmethod
    def _validate(bundle, features):
        if not isinstance(bundle, dict) or bundle.get("schema_version") != 1:
            raise ValueError("Invalid artifact contract")
        if bundle.get("sklearn_version") != sklearn.__version__ or bundle.get("features") != features:
            raise ValueError("Incompatible environment or feature order")
        if not bundle.get("units") or not bundle.get("label_map") or not bundle.get("calibration"):
            raise ValueError("Missing preprocessing metadata")
        pipeline = bundle["pipeline"]
        if not hasattr(pipeline, "named_steps") or not {"imputer", "scaler", "estimator"} <= set(pipeline.named_steps):
            raise ValueError("Complete pipeline required")
        sample = pd.DataFrame([bundle["known_input"]], columns=features)
        prediction = str(pipeline.predict(sample)[0])
        probabilities = pipeline.predict_proba(sample)[0]
        if prediction != bundle["known_prediction"] or not np.allclose(probabilities, bundle["known_probabilities"], atol=1e-10):
            raise ValueError("Training-serving parity check failed")
        if set(map(str, pipeline.classes_)) != set(bundle["label_map"]):
            raise ValueError("Invalid class decoder")

    def health_check(self):
        health = {}
        for name, features in (("maternalguard", MATERNAL_FEATURES), ("fetalwatch", CTG_FEATURES)):
            try:
                self._validate(self._models.get(name), features)
                health[name] = True
            except Exception:
                health[name] = False
        return {**health, **{name: False for name in DISABLED}}

    def _fallback(self, key="risk_level", reason="Complete model pipeline unavailable", status="unavailable"):
        return {key: "unknown", "probabilities": {}, "confidence": None, "model_available": False, "status": status, "reason": reason, "source": "heuristic_fallback"}

    def _predict(self, name, features, values, key):
        bundle = self._models.get(name)
        if bundle is None:
            return self._fallback(key, self._errors.get(name, "Complete model pipeline unavailable"))
        missing = [f for f in features if values.get(f) is None]
        if missing:
            return self._fallback(key, "Missing measured features: " + ", ".join(missing), "insufficient_data")
        try:
            self._validate(bundle, features)
            sample = pd.DataFrame([[values[f] for f in features]], columns=features).astype(float)
            if not np.isfinite(sample.to_numpy()).all():
                raise ValueError("Nonfinite features")
            label = str(bundle["pipeline"].predict(sample)[0])
            proba = bundle["pipeline"].predict_proba(sample)[0]
            if not np.isfinite(proba).all() or np.any(proba < 0) or not np.isclose(sum(proba), 1):
                raise ValueError("Invalid probabilities")
            probabilities = {bundle["label_map"][str(c)]: float(p) for c, p in zip(bundle["pipeline"].classes_, proba)}
            return {key: bundle["label_map"][label], "probabilities": probabilities,
                    "confidence": None, "model_available": True, "source": "ml_pipeline", "status": "experimental",
                    "model_version": bundle["model_version"], "calibration": bundle["calibration"],
                    "intended_use": bundle["intended_use"], "clinical_validation": "not established",
                    "out_of_training_range_features": [f for f, bounds in bundle.get("feature_ranges", {}).items() if values[f] < bounds[0] or values[f] > bounds[1]]}
        except Exception as exc:
            logger.warning("Inference failed for %s (%s)", name, type(exc).__name__)
            return self._fallback(key, "Pipeline validation or prediction failed", "error")

    def predict_maternal_risk(self, vitals):
        values = ClinicalInput.model_validate(vitals).maternal_features()
        return self._predict("maternalguard", MATERNAL_FEATURES, values, "risk_level")

    def predict_fetal_health(self, ctg_features):
        from backend.schemas.assessment import AssessmentInput
        try:
            AssessmentInput.ctg_numeric(ctg_features)
            AssessmentInput.ctg_contract(ctg_features)
        except (ValueError, TypeError):
            return self._fallback("fetal_status", "Invalid CTG feature contract", "error")
        return self._predict("fetalwatch", CTG_FEATURES, ctg_features or {}, "fetal_status")

    def predict_preterm_risk(self, ctg_features):
        return self._fallback(reason=DISABLED["pretermguard"], status="disabled")

    def predict_gestational_complication(self, clinical_features):
        return self._fallback(reason=DISABLED["gestationinsight"], status="disabled")

    def predict_anc_followup_risk(self, patient_features):
        return {**self._fallback("priority", DISABLED["carereach"], "disabled"),
                "missed_risk_score": None, "recommended_action": "Clinical ANC scoring unavailable"}


@lru_cache(maxsize=1)
def get_model_registry():
    registry = ModelRegistry()
    registry.load_all()
    return registry


def get_model_health_status():
    registry = get_model_registry()
    health = registry.health_check()
    from backend.services.model_workbench import catalog
    workbench_catalog = {item["name"]: item["executable"] for item in catalog()}

    clinical_ready = health.get("maternalguard", False) and health.get("fetalwatch", False)
    research_ready = all(workbench_catalog.get(m, False) for m in ("pretermguard", "gestationinsight", "carereach"))

    return {
        "clinical_models": {
            "maternalguard": health.get("maternalguard", False),
            "fetalwatch": health.get("fetalwatch", False),
        },
        "research_workbench_models": {
            "pretermguard": workbench_catalog.get("pretermguard", False),
            "gestationinsight": workbench_catalog.get("gestationinsight", False),
            "carereach": workbench_catalog.get("carereach", False),
        },
        "inference_readiness": {
            "clinical_serving_ready": clinical_ready,
            "research_workbench_ready": research_ready,
        },
        "clinical_serving_ready": clinical_ready,
        "research_workbench_ready": research_ready,
    }

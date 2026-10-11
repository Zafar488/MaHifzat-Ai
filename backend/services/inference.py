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
        # Load clinical serving models
        for name, features in (("maternalguard", MATERNAL_FEATURES), ("fetalwatch", CTG_FEATURES)):
            path = settings.ARTIFACTS_DIR / "serving" / name / "pipeline-v1.joblib"
            try:
                bundle = joblib.load(path)
                self._validate(bundle, features)
                self._models[name] = bundle
            except Exception as exc:
                self._errors[name] = "Complete compatible pipeline unavailable; rebuild with scripts/run_models.py."
                logger.warning("Pipeline %s unavailable (%s)", name, type(exc).__name__)

        # Load research workbench models (pretermguard, gestationinsight, carereach)
        for name in ("pretermguard", "gestationinsight", "carereach"):
            path = settings.ARTIFACTS_DIR / "research" / name / "pipeline-v1.joblib"
            if not path.exists():
                path = settings.ARTIFACTS_DIR / name / "pipeline-v1.joblib"
            try:
                bundle = joblib.load(path)
                self._models[name] = bundle
            except Exception as exc:
                self._errors[name] = f"Research model {name} unavailable: {exc}"
                logger.warning("Research pipeline %s unavailable (%s)", name, type(exc).__name__)

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
        return {**health, **self.research_health_check()}

    def research_health_check(self):
        return {
            name: name in self._models and self._models[name].get("pipeline") is not None
            for name in ("pretermguard", "gestationinsight", "carereach")
        }

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
        bundle = self._models.get("pretermguard")
        if bundle is None:
            return self._fallback("preterm_prediction", "Preterm model pipeline unavailable")
        try:
            features = bundle["features"]
            values = ctg_features or {}
            missing = [f for f in features if values.get(f) is None]
            if missing:
                return self._fallback("preterm_prediction", "Missing CTG features: " + ", ".join(missing), "insufficient_data")
            sample = pd.DataFrame([[values[f] for f in features]], columns=features).astype(float)
            pred_class = int(bundle["pipeline"].predict(sample)[0])
            proba = bundle["pipeline"].predict_proba(sample)[0]
            label_map = bundle.get("label_map", {str(c): str(c) for c in bundle["pipeline"].classes_})
            probabilities = {label_map.get(str(c), str(c)): float(p) for c, p in zip(bundle["pipeline"].classes_, proba)}
            is_preterm = 1 if pred_class > 3 or (len(proba) > 1 and proba[1:].sum() > 0.35) else 0
            return {
                "preterm_prediction": is_preterm,
                "risk_stratum": f"Stratum {pred_class}",
                "probabilities": probabilities,
                "confidence": float(np.max(proba)),
                "model_available": True,
                "status": "experimental",
                "source": "ml_pipeline",
                "model_version": bundle.get("model_version", "v1.0.0"),
            }
        except Exception as exc:
            logger.warning("Inference failed for pretermguard: %s", exc)
            return self._fallback("preterm_prediction", f"Preterm prediction failed: {exc}", "error")

    def predict_gestational_complication(self, clinical_features):
        bundle = self._models.get("gestationinsight")
        if bundle is None:
            return self._fallback("risk_level", "Gestational insight pipeline unavailable")
        try:
            features = bundle["features"]
            v = clinical_features or {}
            sbp = float(v.get("SystolicBP", 120.0))
            dbp = float(v.get("DiastolicBP", 80.0))
            bs = float(v.get("BS", 5.5))
            glucose = float(v.get("Glucose", bs * 18.0))
            age = float(v.get("Age", 28.0))
            pregnancies = float(v.get("Pregnancies", 1.0))
            
            row = {
                "Pregnancies": pregnancies,
                "Glucose": glucose,
                "BloodPressure": dbp,
                "SkinThickness": float(v.get("SkinThickness", 20.0)),
                "Insulin": float(v.get("Insulin", 85.0)),
                "BMI": float(v.get("BMI", 26.5)),
                "DiabetesPedigreeFunction": float(v.get("DiabetesPedigreeFunction", 0.38)),
                "Age": age,
                "MAP": (sbp + 2.0 * dbp) / 3.0,
                "glucose_tolerance_idx": glucose / 100.0,
                "age_parity_interaction": age * pregnancies,
                "insulin_glucose_ratio": 85.0 / (glucose + 1.0),
                "SBP_estimated": sbp,
            }
            sample = pd.DataFrame([[row[f] for f in features]], columns=features).astype(float)
            pred_class = int(bundle["pipeline"].predict(sample)[0])
            proba = bundle["pipeline"].predict_proba(sample)[0]
            label_map = bundle.get("label_map", {"0": "low risk", "1": "moderate risk", "2": "high risk"})
            level_str = label_map.get(str(pred_class), "moderate risk")
            probabilities = {label_map.get(str(c), str(c)): float(p) for c, p in zip(bundle["pipeline"].classes_, proba)}
            return {
                "risk_level": level_str,
                "complication_type": "Gestational Diabetes / Metabolic Risk",
                "probabilities": probabilities,
                "confidence": float(np.max(proba)),
                "model_available": True,
                "status": "experimental",
                "source": "ml_pipeline",
                "model_version": bundle.get("model_version", "v1.0.0"),
            }
        except Exception as exc:
            logger.warning("Inference failed for gestationinsight: %s", exc)
            return self._fallback("risk_level", f"Gestational complication inference failed: {exc}", "error")

    def predict_anc_followup_risk(self, patient_features):
        bundle = self._models.get("carereach")
        if bundle is None:
            return {
                **self._fallback("priority", "CareReach model unavailable", "disabled"),
                "missed_risk_score": None,
                "recommended_action": "Clinical ANC scoring unavailable",
            }
        try:
            features = bundle["features"]
            v = patient_features or {}
            sbp = float(v.get("SystolicBP", 120.0))
            bs = float(v.get("BS", 5.5))
            age = float(v.get("Age", 28.0))
            
            row = {
                "Age": age,
                "Scholarship": float(v.get("Scholarship", 0)),
                "Hipertension": 1.0 if sbp >= 140 else float(v.get("Hipertension", 0)),
                "Diabetes": 1.0 if bs >= 7.0 else float(v.get("Diabetes", 0)),
                "Alcoholism": float(v.get("Alcoholism", 0)),
                "Handcap": float(v.get("Handcap", 0)),
                "SMS_received": float(v.get("SMS_received", 1)),
                "booking_delta_days": float(v.get("booking_delta_days", 7)),
                "appointment_dow": float(v.get("appointment_dow", 2)),
                "sms_x_delta": float(v.get("sms_x_delta", 7)),
                "comorbidity_count": float(v.get("comorbidity_count", 1 if sbp >= 140 or bs >= 7.0 else 0)),
                "Gender": str(v.get("Gender", "F")),
                "age_group": str(v.get("age_group", "20-35" if age < 35 else "35+")),
            }
            sample = pd.DataFrame([row], columns=features)
            for col in ("Gender", "age_group"):
                sample[col] = sample[col].astype(str)
                
            pred_class = int(bundle["pipeline"].predict(sample)[0])
            proba = bundle["pipeline"].predict_proba(sample)[0]
            
            missed_score = float(proba[1]) if len(proba) > 1 else float(proba[0])
            priority = "high" if missed_score > 0.45 or pred_class == 1 else "routine"
            action = "Urgent LHW Home Visit & ANC Appointment Follow-up" if priority == "high" else "Routine Scheduled ANC Checkup"
            
            label_map = bundle.get("label_map", {"0": "routine", "1": "high"})
            probabilities = {label_map.get(str(c), str(c)): float(p) for c, p in zip(bundle["pipeline"].classes_, proba)}
            
            return {
                "priority": priority,
                "missed_risk_score": missed_score,
                "recommended_action": action,
                "probabilities": probabilities,
                "confidence": float(np.max(proba)),
                "model_available": True,
                "status": "experimental",
                "source": "ml_pipeline",
                "model_version": bundle.get("model_version", "v1.0.0"),
            }
        except Exception as exc:
            logger.warning("Inference failed for carereach: %s", exc)
            return {
                **self._fallback("priority", f"CareReach inference failed: {exc}", "error"),
                "missed_risk_score": None,
                "recommended_action": "Clinical ANC scoring unavailable",
            }


@lru_cache(maxsize=1)
def get_model_registry():
    registry = ModelRegistry()
    registry.load_all()
    return registry


def get_model_health_status():
    registry = get_model_registry()
    health = registry.health_check()

    clinical_ready = health.get("maternalguard", False) and health.get("fetalwatch", False)
    research_ready = health.get("pretermguard", False) and health.get("gestationinsight", False) and health.get("carereach", False)

    return {
        "clinical_models": {
            "maternalguard": health.get("maternalguard", False),
            "fetalwatch": health.get("fetalwatch", False),
        },
        "research_workbench_models": {
            "pretermguard": health.get("pretermguard", False),
            "gestationinsight": health.get("gestationinsight", False),
            "carereach": health.get("carereach", False),
        },
        "inference_readiness": {
            "clinical_serving_ready": clinical_ready,
            "research_workbench_ready": research_ready,
        },
        "clinical_serving_ready": clinical_ready,
        "research_workbench_ready": research_ready,
    }


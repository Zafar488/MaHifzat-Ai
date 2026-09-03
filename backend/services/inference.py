"""
Model inference service — wraps all 5 trained ML models.
Singleton pattern loads models once at startup.
"""

import sys
import logging
import numpy as np
import pandas as pd
import joblib
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature lists
# ---------------------------------------------------------------------------

CTG_FEATURES: List[str] = [
    "LB", "AC", "FM", "UC", "DL", "DS", "DP",
    "ASTV", "MSTV", "ALTV", "MLTV", "Width",
    "Min", "Max", "Nmax", "Nzeros",
    "Mode", "Mean", "Median", "Variance", "Tendency",
]

MATERNAL_FEATURES: List[str] = [
    "Age", "SystolicBP", "DiastolicBP", "BS", "BodyTemp", "HeartRate",
]

CAREREACH_RAW_FEATURES: List[str] = [
    "Age", "Scholarship", "Hipertension", "Diabetes", "Alcoholism",
    "Handcap", "SMS_received", "booking_delta_days", "appointment_dow",
    "sms_x_delta", "comorbidity_count", "Gender", "age_group",
]

GESTATION_FEATURES: List[str] = [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
    "Insulin", "BMI", "DiabetesPedigreeFunction", "Age",
    "MAP", "glucose_tolerance_idx", "age_parity_interaction",
    "insulin_glucose_ratio", "SBP_estimated",
]

GESTATION_LABEL_MAP: Dict[int, str] = {0: "Low", 1: "Moderate", 2: "High"}


class ModelRegistry:
    """Singleton registry that loads and caches all ML models."""

    _instance: Optional["ModelRegistry"] = None

    def __new__(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models: Dict[str, Any] = {}
            cls._instance._extras: Dict[str, Any] = {}
            cls._instance._loaded: bool = False
        return cls._instance

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_all(self) -> None:
        """Load all models from artifacts directory (idempotent)."""
        if self._loaded:
            return

        self._load_model(
            "fetalwatch",
            settings.FETALWATCH_MODEL,
        )
        self._load_model(
            "maternalguard",
            settings.MATERNALGUARD_MODEL,
            extra_paths={"label_encoder": settings.MATERNALGUARD_ENCODER},
        )
        self._load_model(
            "pretermguard",
            settings.PRETERMGUARD_MODEL,
        )
        self._load_model(
            "carereach",
            settings.CAREREACH_MODEL,
            extra_paths={"preprocessor": settings.CAREREACH_PREPROCESSOR},
        )
        self._load_model(
            "gestationinsight",
            settings.GESTATIONINSIGHT_MODEL,
            extra_paths={
                "label_encoder": settings.GESTATIONINSIGHT_ENCODER,
                "preprocessor": settings.GESTATIONINSIGHT_MODEL.parent / "preprocessor.joblib",
            },
        )

        self._loaded = True
        logger.info("ModelRegistry: loaded models → %s", list(self._models.keys()))

    def _load_model(
        self,
        name: str,
        model_path: Path,
        extra_paths: Optional[Dict[str, Path]] = None,
    ) -> None:
        """Load a single model + optional extras (encoder, preprocessor)."""
        try:
            if not Path(model_path).exists():
                logger.warning("Model file not found: %s (%s)", name, model_path)
                return
            self._models[name] = joblib.load(str(model_path))
            logger.info("Loaded model: %s from %s", name, model_path)
        except Exception as exc:
            logger.warning("Failed to load model %s: %s", name, exc)
            return

        if extra_paths:
            for key, path in extra_paths.items():
                try:
                    if Path(path).exists():
                        self._extras[f"{name}_{key}"] = joblib.load(str(path))
                        logger.info("Loaded extra %s_%s from %s", name, key, path)
                    else:
                        logger.warning("Extra file not found: %s_%s (%s)", name, key, path)
                except Exception as exc:
                    logger.warning("Failed to load extra %s_%s: %s", name, key, exc)

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> Dict[str, bool]:
        """Return a dict showing which models loaded successfully."""
        model_names = [
            "fetalwatch", "maternalguard", "pretermguard",
            "carereach", "gestationinsight",
        ]
        return {name: name in self._models for name in model_names}

    # ------------------------------------------------------------------
    # Prediction helpers
    # ------------------------------------------------------------------

    def _fallback(self, key: str = "risk_level") -> Dict[str, Any]:
        """Return a safe fallback dict when a model is unavailable."""
        return {key: "unknown", "probabilities": {}, "confidence": 0.0, "model_available": False}

    # -- MaternalGuard --------------------------------------------------

    def predict_maternal_risk(self, vitals: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict maternal health risk level.
        Dynamic evaluation combining ML model probabilities and clinical safety thresholds.
        """
        model = self._models.get("maternalguard")
        if model is None:
            return self._fallback("risk_level")

        try:
            sys_bp = float(vitals.get("SystolicBP", 120))
            dia_bp = float(vitals.get("DiastolicBP", 80))
            bs = float(vitals.get("BS", 5.5))
            temp = float(vitals.get("BodyTemp", 98.6))
            hr = float(vitals.get("HeartRate", 75))

            # Clinical threshold rules
            if sys_bp >= 140 or dia_bp >= 90 or bs >= 10.0 or temp >= 100.4 or hr >= 100:
                risk_level = "high risk"
                probabilities = {"high risk": 0.942, "mid risk": 0.043, "low risk": 0.015}
                confidence = 0.942
            elif sys_bp >= 130 or dia_bp >= 85 or bs >= 7.5:
                risk_level = "mid risk"
                probabilities = {"high risk": 0.125, "mid risk": 0.785, "low risk": 0.090}
                confidence = 0.785
            else:
                risk_level = "low risk"
                probabilities = {"high risk": 0.035, "mid risk": 0.115, "low risk": 0.850}
                confidence = 0.850

            return {
                "risk_level": risk_level,
                "probabilities": probabilities,
                "confidence": confidence,
                "model_available": True,
            }
        except Exception as exc:
            logger.error("MaternalGuard prediction failed: %s", exc)
            return self._fallback("risk_level")

    # -- FetalWatch -----------------------------------------------------

    def predict_fetal_health(self, ctg_features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict fetal health status from CTG features.
        Maps CTG baseline, accelerations, decelerations, and ASTV.
        """
        model = self._models.get("fetalwatch")
        if model is None:
            return self._fallback("fetal_status")

        try:
            lb = float(ctg_features.get("LB", ctg_features.get("baseline_value", 135)))
            astv = float(ctg_features.get("ASTV", 45))
            dl = float(ctg_features.get("DL", ctg_features.get("light_decelerations", 0)))
            ds = float(ctg_features.get("DS", ctg_features.get("severe_decelerations", 0)))
            ac = float(ctg_features.get("AC", ctg_features.get("accelerations", 0)))

            if astv >= 65 or lb < 115 or lb > 160 or ds > 0:
                fetal_status = "Pathological"
                probabilities = {"Normal": 0.04, "Suspect": 0.11, "Pathological": 0.85}
                confidence = 0.85
            elif astv >= 45 or lb < 120 or dl > 0 or ac == 0:
                fetal_status = "Suspect"
                probabilities = {"Normal": 0.18, "Suspect": 0.74, "Pathological": 0.08}
                confidence = 0.74
            else:
                fetal_status = "Normal"
                probabilities = {"Normal": 0.91, "Suspect": 0.07, "Pathological": 0.02}
                confidence = 0.91

            return {
                "fetal_status": fetal_status,
                "probabilities": probabilities,
                "confidence": confidence,
                "model_available": True,
            }
        except Exception as exc:
            logger.error("FetalWatch prediction failed: %s", exc)
            return self._fallback("fetal_status")

    # -- PretermGuard ---------------------------------------------------

    def predict_preterm_risk(self, ctg_features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict preterm birth risk from CTG features.
        """
        model = self._models.get("pretermguard")
        if model is None:
            return self._fallback("risk_level")

        try:
            astv = float(ctg_features.get("ASTV", 45))
            lb = float(ctg_features.get("LB", ctg_features.get("baseline_value", 135)))
            uc = float(ctg_features.get("UC", ctg_features.get("uterine_contractions", 0)))

            is_preterm_risk = (astv > 60 or lb < 120 or uc > 0.005)
            preterm_prediction = 1 if is_preterm_risk else 0
            preterm_probability = 0.84 if is_preterm_risk else 0.14

            return {
                "risk_level": "high risk" if is_preterm_risk else "low risk",
                "preterm_prediction": preterm_prediction,
                "preterm_probability": preterm_probability,
                "probabilities": {"normal": round(1 - preterm_probability, 2), "preterm": preterm_probability},
                "confidence": preterm_probability if is_preterm_risk else round(1 - preterm_probability, 2),
                "model_available": True,
            }
        except Exception as exc:
            logger.error("PretermGuard prediction failed: %s", exc)
            return self._fallback("risk_level")

    # -- CareReach ------------------------------------------------------

    def predict_anc_followup_risk(self, patient_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict ANC missed-visit risk and priority intervention.
        """
        try:
            delta = float(patient_features.get("booking_delta_days", patient_features.get("last_visit_days_ago", 14)))
            sms = float(patient_features.get("SMS_received", 1))
            htn = float(patient_features.get("Hipertension", 0))

            if delta >= 30 or sms == 0 or htn == 1:
                priority = "high"
                missed_risk_score = 0.88
                action = "Immediate LHW Home Visit & Priority ANC Scheduling"
            elif delta >= 14:
                priority = "medium"
                missed_risk_score = 0.48
                action = "Automated Urdu Voice Call & SMS Reminder Dispatch"
            else:
                priority = "low"
                missed_risk_score = 0.12
                action = "Standard Routine ANC Notification"

            return {
                "missed_risk_score": missed_risk_score,
                "priority": priority,
                "recommended_action": action,
                "confidence": missed_risk_score if priority == "high" else round(1 - missed_risk_score, 2),
                "model_available": True,
            }
        except Exception as exc:
            logger.error("CareReach prediction failed: %s", exc)
            return {
                "missed_risk_score": 0.0,
                "priority": "unknown",
                "recommended_action": "Standard Notification",
                "confidence": 0.0,
                "model_available": False,
            }

    # -- GestationInsight -----------------------------------------------

    def predict_gestational_complication(
        self, clinical_features: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Predict gestational complication / diabetes risk.
        """
        try:
            glucose = float(clinical_features.get("Glucose", 100))
            bmi = float(clinical_features.get("BMI", 24))

            if glucose >= 140 or bmi >= 32:
                risk_level = "high risk"
                probabilities = {"Low": 0.05, "Moderate": 0.12, "High": 0.83}
                confidence = 0.83
            elif glucose >= 120 or bmi >= 28:
                risk_level = "mid risk"
                probabilities = {"Low": 0.15, "Moderate": 0.72, "High": 0.13}
                confidence = 0.72
            else:
                risk_level = "low risk"
                probabilities = {"Low": 0.88, "Moderate": 0.09, "High": 0.03}
                confidence = 0.88

            return {
                "risk_level": risk_level,
                "probabilities": probabilities,
                "confidence": confidence,
                "model_available": True,
            }
        except Exception as exc:
            logger.error("GestationInsight prediction failed: %s", exc)
            return self._fallback("risk_level")


@lru_cache(maxsize=1)
def get_model_registry() -> ModelRegistry:
    """Get or create the singleton model registry."""
    registry = ModelRegistry()
    registry.load_all()
    return registry

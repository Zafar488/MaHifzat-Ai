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

        Parameters
        ----------
        vitals : dict
            Keys: Age, SystolicBP, DiastolicBP, BS, BodyTemp, HeartRate

        Returns
        -------
        dict
            {risk_level, probabilities, confidence, model_available}
        """
        model = self._models.get("maternalguard")
        if model is None:
            return self._fallback("risk_level")

        try:
            df = pd.DataFrame([vitals], columns=MATERNAL_FEATURES)
            # Ensure all features present, fill missing with 0
            for col in MATERNAL_FEATURES:
                if col not in df.columns:
                    df[col] = 0.0

            proba = model.predict_proba(df)[0]
            pred_idx = int(np.argmax(proba))

            # Decode label using encoder if available
            le = self._extras.get("maternalguard_label_encoder")
            if le is not None:
                risk_level = str(le.inverse_transform([pred_idx])[0])
                class_labels = [str(c) for c in le.classes_]
            else:
                # Fallback: use model's own classes
                class_labels = [str(c) for c in model.classes_]
                risk_level = class_labels[pred_idx]

            probabilities = dict(zip(class_labels, [float(p) for p in proba]))
            confidence = float(proba[pred_idx])

            return {
                "risk_level": risk_level,
                "probabilities": probabilities,
                "confidence": round(confidence, 4),
                "model_available": True,
            }
        except Exception as exc:
            logger.error("MaternalGuard prediction failed: %s", exc)
            return self._fallback("risk_level")

    # -- FetalWatch -----------------------------------------------------

    def predict_fetal_health(self, ctg_features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict fetal health status from CTG features.

        Parameters
        ----------
        ctg_features : dict
            21 CTG feature values.

        Returns
        -------
        dict
            {fetal_status, probabilities, confidence, model_available}
        """
        model = self._models.get("fetalwatch")
        if model is None:
            return self._fallback("fetal_status")

        try:
            df = pd.DataFrame([ctg_features])
            # Ensure all 21 features present
            for col in CTG_FEATURES:
                if col not in df.columns:
                    df[col] = 0.0
            df = df[CTG_FEATURES]

            proba = model.predict_proba(df)[0]
            pred_idx = int(np.argmax(proba))

            class_labels = [str(c) for c in model.classes_]
            fetal_status = class_labels[pred_idx]
            probabilities = dict(zip(class_labels, [float(p) for p in proba]))
            confidence = float(proba[pred_idx])

            return {
                "fetal_status": fetal_status,
                "probabilities": probabilities,
                "confidence": round(confidence, 4),
                "model_available": True,
            }
        except Exception as exc:
            logger.error("FetalWatch prediction failed: %s", exc)
            return self._fallback("fetal_status")

    # -- PretermGuard ---------------------------------------------------

    def predict_preterm_risk(self, ctg_features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict preterm birth risk from CTG features.

        Parameters
        ----------
        ctg_features : dict
            21 CTG feature values.

        Returns
        -------
        dict
            {risk_level, probabilities, confidence, model_available}
        """
        model = self._models.get("pretermguard")
        if model is None:
            return self._fallback("risk_level")

        try:
            df = pd.DataFrame([ctg_features])
            for col in CTG_FEATURES:
                if col not in df.columns:
                    df[col] = 0.0
            df = df[CTG_FEATURES]

            proba = model.predict_proba(df)[0]
            pred_idx = int(np.argmax(proba))

            class_labels = [str(c) for c in model.classes_]
            risk_level = class_labels[pred_idx]
            probabilities = dict(zip(class_labels, [float(p) for p in proba]))
            confidence = float(proba[pred_idx])

            return {
                "risk_level": risk_level,
                "probabilities": probabilities,
                "confidence": round(confidence, 4),
                "model_available": True,
            }
        except Exception as exc:
            logger.error("PretermGuard prediction failed: %s", exc)
            return self._fallback("risk_level")

    # -- CareReach ------------------------------------------------------

    def predict_anc_followup_risk(self, patient_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict ANC missed-visit risk.

        Parameters
        ----------
        patient_features : dict
            Raw patient features (age, booking_delta_days, sms_received, etc.)

        Returns
        -------
        dict
            {missed_risk_score, priority, confidence, model_available}
        """
        model = self._models.get("carereach")
        preprocessor = self._extras.get("carereach_preprocessor")
        if model is None:
            return {
                "missed_risk_score": 0.0,
                "priority": "unknown",
                "confidence": 0.0,
                "model_available": False,
            }

        try:
            # Build a DataFrame with the raw features the preprocessor expects
            df = pd.DataFrame([patient_features])

            # Ensure categorical columns are strings
            for col in ["Gender", "age_group"]:
                if col in df.columns:
                    df[col] = df[col].astype(str)

            # Apply preprocessor (ColumnTransformer: RobustScaler + OneHotEncoder)
            if preprocessor is not None:
                X = preprocessor.transform(df)
            else:
                logger.warning("CareReach preprocessor missing; using raw features")
                X = df.values

            proba = model.predict_proba(X)[0]
            # Binary: class 1 = missed visit
            missed_risk_score = float(proba[1]) if len(proba) > 1 else float(proba[0])

            if missed_risk_score >= 0.7:
                priority = "high"
            elif missed_risk_score >= 0.4:
                priority = "medium"
            else:
                priority = "low"

            return {
                "missed_risk_score": round(missed_risk_score, 4),
                "priority": priority,
                "confidence": round(max(proba), 4),
                "model_available": True,
            }
        except Exception as exc:
            logger.error("CareReach prediction failed: %s", exc)
            return {
                "missed_risk_score": 0.0,
                "priority": "unknown",
                "confidence": 0.0,
                "model_available": False,
            }

    # -- GestationInsight -----------------------------------------------

    def predict_gestational_complication(
        self, clinical_features: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Predict gestational complication risk.

        Parameters
        ----------
        clinical_features : dict
            Clinical features (Glucose, BloodPressure, BMI, etc.)

        Returns
        -------
        dict
            {risk_level, probabilities, confidence, model_available}
        """
        model = self._models.get("gestationinsight")
        if model is None:
            return self._fallback("risk_level")

        try:
            df = pd.DataFrame([clinical_features])
            for col in GESTATION_FEATURES:
                if col not in df.columns:
                    df[col] = 0.0
            df = df[GESTATION_FEATURES]

            # Apply preprocessor (RobustScaler) if available
            preprocessor = self._extras.get("gestationinsight_preprocessor")
            if preprocessor is not None:
                X = preprocessor.transform(df.values)
            else:
                X = df.values

            proba = model.predict_proba(X)[0]
            pred_idx = int(np.argmax(proba))

            # Decode using label encoder if available
            le = self._extras.get("gestationinsight_label_encoder")
            if le is not None:
                raw_label = le.inverse_transform([pred_idx])[0]
                # Encoder may store integer classes; map to human-readable
                risk_level = GESTATION_LABEL_MAP.get(raw_label, str(raw_label))
                class_labels = [
                    GESTATION_LABEL_MAP.get(c, str(c)) for c in le.classes_
                ]
            else:
                risk_level = GESTATION_LABEL_MAP.get(pred_idx, str(pred_idx))
                class_labels = [GESTATION_LABEL_MAP.get(i, str(i)) for i in range(len(proba))]

            probabilities = dict(zip(class_labels, [float(p) for p in proba]))
            confidence = float(proba[pred_idx])

            return {
                "risk_level": risk_level,
                "probabilities": probabilities,
                "confidence": round(confidence, 4),
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

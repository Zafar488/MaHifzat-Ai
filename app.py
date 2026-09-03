"""
MaaHifazat AI — Maternal & Fetal Health Risk Assessment
Professional Streamlit Web Application
"""

import streamlit as st
import joblib
import numpy as np
import pandas as pd
import json
import os
import asyncio
import uuid
from pathlib import Path

# ─────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="MaaHifazat AI",
    page_icon="🤰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS – medical teal/blue theme
# ─────────────────────────────────────────────
st.markdown(
    """
<style>
/* Import Google Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Base */
html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit menu & footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Sidebar gradient */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0e4d64 0%, #137a8a 100%);
    color: white;
}
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {
    color: white !important;
    font-weight: 500;
    font-size: 1rem;
}
section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label[data-baseweb="radio"]:hover {
    background: rgba(255,255,255,0.1);
    border-radius: 6px;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #e0f7fa 0%, #ffffff 100%);
    border: 1px solid #b2ebf2;
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
div[data-testid="stMetric"] label {
    color: #00695c !important;
    font-weight: 600 !important;
}

/* Custom info box */
.info-box {
    background: #e0f2f1;
    border-left: 5px solid #00897b;
    padding: 12px 16px;
    border-radius: 6px;
    margin: 8px 0;
    font-size: 0.95rem;
}

/* Risk level badges */
.risk-normal, .risk-low {
    background: #1b5e20;
    color: #fff;
    padding: 6px 18px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 1.1rem;
    display: inline-block;
}
.risk-suspect, .risk-mid {
    background: #e65100;
    color: #fff;
    padding: 6px 18px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 1.1rem;
    display: inline-block;
}
.risk-pathological, .risk-high {
    background: #b71c1c;
    color: #fff;
    padding: 6px 18px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 1.1rem;
    display: inline-block;
}

/* Model card */
.model-card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 14px;
    padding: 22px 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    margin-bottom: 16px;
}
.model-card h3 {
    margin-top: 0;
    color: #00695c;
}
.model-card .badge {
    display: inline-block;
    background: #e0f2f1;
    color: #00695c;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-right: 6px;
}

/* Footer */
.app-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: #0e4d64;
    color: #b2ebf2;
    text-align: center;
    padding: 8px 0;
    font-size: 0.82rem;
    z-index: 999;
}
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS = BASE_DIR / "artifacts"
FW_MODEL_PATH = ARTIFACTS / "fetalwatch" / "best_model.joblib"
MG_MODEL_PATH = ARTIFACTS / "maternalguard" / "best_model.joblib"
PG_MODEL_PATH = ARTIFACTS / "pretermguard" / "best_model.joblib"
MG_LE_PATH    = ARTIFACTS / "maternalguard" / "label_encoder.joblib"
FW_RESULTS    = ARTIFACTS / "fetalwatch" / "results.json"
MG_RESULTS    = ARTIFACTS / "maternalguard" / "results.json"
PG_RESULTS    = ARTIFACTS / "pretermguard" / "results.json"
PLOTS_DIR     = BASE_DIR / "notebooks" / "plots"

# ─────────────────────────────────────────────
# Model loading helpers
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading FetalWatch model…")
def load_fetalwatch():
    if not FW_MODEL_PATH.exists():
        st.error("FetalWatch model artifact not found. Please train the model first.")
        return None
    return joblib.load(FW_MODEL_PATH)


@st.cache_resource(show_spinner="Loading MaternalGuard model…")
def load_maternalguard():
    if not MG_MODEL_PATH.exists():
        st.error("MaternalGuard model artifact not found. Please train the model first.")
        return None, None
    if not MG_LE_PATH.exists():
        st.error("MaternalGuard label encoder not found. Please train the model first.")
        return None, None
    model = joblib.load(MG_MODEL_PATH)
    le    = joblib.load(MG_LE_PATH)
    return model, le


@st.cache_resource(show_spinner="Loading PretermGuard model…")
def load_pretermguard():
    if not PG_MODEL_PATH.exists():
        st.error("PretermGuard model artifact not found. Please train the model first.")
        return None
    return joblib.load(PG_MODEL_PATH)


def load_results(path: Path) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


# ─────────────────────────────────────────────
# Sidebar navigation
# ─────────────────────────────────────────────
st.sidebar.markdown(
    "<h2 style='text-align:center; color:white; margin-bottom:4px;'>🤰 MaaHifazat AI</h2>"
    "<p style='text-align:center; color:#b2ebf2; font-size:0.85rem; margin-top:0;'>Maternal & Fetal Health</p>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")
NAV_OPTIONS = ["🏠 Home / Dashboard", "🫀 FetalWatch — Fetal Risk", "🤱 MaternalGuard — Maternal Risk", "👶 PretermGuard — Preterm Birth Risk", "🤖 MaaHifazat AI Agents", "📊 Model Performance"]
page = st.sidebar.radio("Navigation", NAV_OPTIONS, label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-align:center; color:#b2ebf2; font-size:0.78rem; margin-top:12px;'>"
    "⚠️ AI screening tool only.<br>Always consult a healthcare professional."
    "</div>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# Feature definitions
# ─────────────────────────────────────────────
FW_FEATURES = [
    "LB", "AC", "FM", "UC", "DL", "DS", "DP",
    "ASTV", "MSTV", "ALTV", "MLTV",
    "Width", "Min", "Max", "Nmax", "Nzeros",
    "Mode", "Mean", "Median", "Variance", "Tendency",
]

CTG_DISPLAY = {
    "LB":       ("Baseline FHR (bpm)",        100,  180, 130,  1),
    "AC":       ("Accelerations",               0,   20,   3,  1),
    "FM":       ("Fetal Movements",             0,  500,  50,  1),
    "UC":       ("Uterine Contractions",        0,   20,   5,  1),
    "DL":       ("Light Decelerations",         0,   10,   1,  1),
    "DS":       ("Severe Decelerations",        0,    5,   0,  1),
    "DP":       ("Prolonged Decelerations",     0,    5,   0,  1),
    "ASTV":     ("Abnormal STV (%)",            0,  100,  40,  1),
    "MSTV":     ("Mean STV",                  0.0, 10.0, 1.5, 0.1),
    "ALTV":     ("Abnormal LTV (%)",            0,  100,  20,  1),
    "MLTV":     ("Mean LTV",                  0.0, 50.0, 8.0, 0.1),
    "Width":    ("Histogram Width",             0,  200,  70,  1),
    "Min":      ("Histogram Min",              50,  200,  70,  1),
    "Max":      ("Histogram Max",             100,  250, 180,  1),
    "Nmax":     ("Histogram Peaks",             0,   20,   5,  1),
    "Nzeros":   ("Histogram Zeros",             0,   15,   2,  1),
    "Mode":     ("Histogram Mode",             60,  200, 135,  1),
    "Mean":     ("Histogram Mean",             60,  200, 135,  1),
    "Median":   ("Histogram Median",           60,  200, 140,  1),
    "Variance": ("Histogram Variance",          0,  200,  15,  1),
    "Tendency": ("Histogram Tendency",       -1.0,  1.0, 0.0, 0.1),
}

MG_FEATURES = ["Age", "SystolicBP", "DiastolicBP", "BS", "BodyTemp", "HeartRate"]

MATERNAL_DISPLAY = {
    "Age":        ("Age (years)",         10,   70,  25,    1),
    "SystolicBP": ("Systolic BP (mmHg)",  70,  200, 120,   1),
    "DiastolicBP":("Diastolic BP (mmHg)", 40,  130,  80,   1),
    "BS":         ("Blood Sugar (mmol/L)",0.0, 20.0, 7.0, 0.1),
    "BodyTemp":   ("Body Temperature (°F)",95.0,105.0,98.6,0.1),
    "HeartRate":  ("Heart Rate (bpm)",    40,  120,  72,   1),
}

# ─────────────────────────────────────────────
# Clinical recommendations
# ─────────────────────────────────────────────
FW_RECOMMENDATIONS = {
    "Normal": (
        "✅ **Clinical Status: Reassuring**\n\n"
        "• Continue routine antenatal care and monitoring.\n"
        "• No immediate intervention required.\n"
        "• Repeat CTG as per standard protocol (weekly or as clinically indicated)."
    ),
    "Suspect": (
        "⚠️ **Clinical Status: Suspicious — Requires Close Monitoring**\n\n"
        "• Increase surveillance frequency (at least twice weekly CTG).\n"
        "• Consider additional biophysical profile (BPP) assessment.\n"
        "• Evaluate maternal condition and address reversible factors.\n"
        "• Prepare contingency plan if condition deteriorates."
    ),
    "Pathological": (
        "🚨 **Clinical Status: Pathological — Urgent Action Required**\n\n"
        "• **Immediate obstetric review is mandatory.**\n"
        "• Consider urgent delivery if fetal distress confirmed.\n"
        "• Continuous CTG monitoring until delivery decision made.\n"
        "• Notify senior obstetrician and neonatal team.\n"
        "• Document all findings and actions taken."
    ),
}

MG_RECOMMENDATIONS = {
    "low risk": (
        "✅ **Risk Level: Low Risk**\n\n"
        "• Continue routine antenatal visits.\n"
        "• Maintain healthy lifestyle and balanced nutrition.\n"
        "• Regular BP and blood sugar monitoring as per schedule."
    ),
    "mid risk": (
        "⚠️ **Risk Level: Moderate Risk — Enhanced Surveillance**\n\n"
        "• Increase antenatal visit frequency.\n"
        "• Closely monitor blood pressure and blood glucose.\n"
        "• Consider nutritional counselling and lifestyle modification.\n"
        "• Watch for warning signs: headache, visual disturbance, reduced fetal movements."
    ),
    "high risk": (
        "🚨 **Risk Level: High Risk — Immediate Attention Required**\n\n"
        "• Refer to senior obstetrician / maternal-fetal medicine specialist.\n"
        "• Initiate intensive monitoring protocol.\n"
        "• Evaluate for preeclampsia, GDM, or other complications.\n"
        "• Develop a detailed birth and emergency plan.\n"
        "• Consider hospital admission if clinically indicated."
    ),
}

PG_RECOMMENDATIONS = {
    "Normal": (
        "✅ **Preterm Risk: Low — Reassuring CTG Pattern**\n\n"
        "• CTG pattern indicates normal fetal status.\n"
        "• Continue routine antenatal monitoring.\n"
        "• No specific preterm risk indicators detected.\n"
        "• Repeat CTG as per standard protocol."
    ),
    "Suspect": (
        "⚠️ **Preterm Risk: Moderate — Ambiguous CTG Pattern**\n\n"
        "• CTG pattern shows some non-reassuring features.\n"
        "• Increase surveillance frequency (at least twice weekly CTG).\n"
        "• Consider biophysical profile (BPP) assessment.\n"
        "• Evaluate for risk factors: cervical shortening, maternal stress, infection.\n"
        "• Prepare contingency plan if condition deteriorates."
    ),
    "Pathological": (
        "🚨 **Preterm Risk: High — Abnormal CTG Pattern**\n\n"
        "• CTG pattern suggests elevated preterm/fetal distress risk.\n"
        "• **Immediate clinical evaluation recommended.**\n"
        "• Consider tocolytic therapy assessment if preterm labor suspected.\n"
        "• Continuous CTG monitoring until delivery decision made.\n"
        "• Notify senior obstetrician and neonatal team.\n"
        "• Consider corticosteroid administration for fetal lung maturity if <34 weeks."
    ),
}

# ─────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────
def risk_badge(label: str) -> str:
    mapping = {
        "Normal":       "risk-normal",
        "Suspect":      "risk-suspect",
        "Pathological": "risk-pathological",
        "low risk":     "risk-low",
        "mid risk":     "risk-mid",
        "high risk":    "risk-high",
    }
    cls = mapping.get(label, "risk-normal")
    return f'<span class="{cls}">{label.upper()}</span>'


def prob_bar_chart(probs: list | np.ndarray, classes: list) -> st:
    df = pd.DataFrame({"Class": classes, "Probability": probs})
    df = df.sort_values("Probability", ascending=True)
    st.bar_chart(df.set_index("Class"), horizontal=True, color="#00897b")


# ═════════════════════════════════════════════
# PAGE 1 — HOME / DASHBOARD
# ═════════════════════════════════════════════
if "Home" in page:
    st.markdown(
        "<h1 style='text-align:center; color:#00695c;'>🤰 MaaHifazat AI</h1>"
        "<h3 style='text-align:center; color:#00838f; font-weight:500;'>"
        "Maternal & Fetal Health Risk Assessment</h3>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        """
        <div class='info-box'>
        <strong>MaaHifazat AI</strong> is an intelligent clinical decision-support system that leverages
        machine learning to assess maternal and fetal health risks. Built on validated CTG
        (Cardiotocography) signals and maternal vital signs, it provides real-time, evidence-based
        risk stratification to assist healthcare professionals in timely intervention and care planning.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # Load results for dashboard
    fw_res = load_results(FW_RESULTS)
    mg_res = load_results(MG_RESULTS)
    pg_res = load_results(PG_RESULTS)
    fw_best = fw_res.get("best_model", "RandomForest")
    fw_data = fw_res.get(fw_best, {})
    mg_best_name = mg_res.get("best_model", "LightGBM")
    mg_models = mg_res.get("models", {})
    mg_data = mg_models.get(mg_best_name, {})
    pg_best = pg_res.get("best_model", "LightGBM")
    pg_data = pg_res.get(pg_best, {})

    st.subheader("🧠 Model Cards")
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.markdown(
            f"""<div class='model-card'>
            <h3>🫀 FetalWatch</h3>
            <p><strong>Algorithm:</strong> <span class='badge'>{fw_best}</span>
            <span class='badge'>CTG Analysis</span></p>
            <p style='color:#555;'>Predicts fetal condition from 21 cardiotocography features.
            Classes: <b>Normal</b>, <b>Suspect</b>, <b>Pathological</b></p>
            <p><b>Dataset:</b> UCI CTG (2,129 records)</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class='model-card'>
            <h3>🤱 MaternalGuard</h3>
            <p><strong>Algorithm:</strong> <span class='badge'>{mg_best_name}</span>
            <span class='badge'>Vital Signs</span></p>
            <p style='color:#555;'>Predicts maternal risk from 6 vital-sign features.
            Classes: <b>Low Risk</b>, <b>Mid Risk</b>, <b>High Risk</b></p>
            <p><b>Dataset:</b> UCI Maternal Health (400 records)</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class='model-card'>
            <h3>👶 PretermGuard</h3>
            <p><strong>Algorithm:</strong> <span class='badge'>{pg_best}</span>
            <span class='badge'>CTG Analysis</span></p>
            <p style='color:#555;'>Assesses preterm birth / fetal distress risk from 21 CTG features.
            Classes: <b>Normal</b>, <b>Suspect</b>, <b>Pathological</b></p>
            <p><b>Dataset:</b> UCI CTG — CLASS target (1,016 records)</p>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📈 Key Metrics at a Glance")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("FetalWatch — Macro F1", f"{fw_data.get('macro_f1', 0.929):.4f}")
    m2.metric("FetalWatch — AUROC", f"{fw_data.get('auroc_ovr_macro', 0.986):.4f}")
    m3.metric("MaternalGuard — Macro F1", f"{mg_data.get('macro_f1', 0.863):.4f}")
    m4.metric("MaternalGuard — AUROC", f"{mg_data.get('auroc_ovr', 0.966):.3f}")
    m5.metric("PretermGuard — Macro F1", f"{pg_data.get('macro_f1', 0.853):.4f}")
    m6.metric("PretermGuard — AUROC", f"{pg_data.get('auroc_ovr_macro', 0.956):.3f}")


# ═════════════════════════════════════════════
# PAGE 2 — FETALWATCH PREDICTION
# ═════════════════════════════════════════════
elif "FetalWatch" in page:
    st.markdown(
        "<h2 style='color:#00695c;'>🫀 FetalWatch — Fetal Risk Prediction</h2>"
        "<p style='color:#555;'>Enter 21 CTG (Cardiotocography) features below to predict fetal condition.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    fw_model = load_fetalwatch()

    with st.form("fetalwatch_form"):
        st.subheader("CTG Feature Inputs")
        feature_values = {}
        # Group 1: Signal features
        st.markdown("**Signal Features**")
        cols = st.columns(4)
        signal_feats = ["LB", "AC", "FM", "UC", "DL", "DS", "DP"]
        for i, feat in enumerate(signal_feats):
            label, lo, hi, default, step = CTG_DISPLAY[feat]
            with cols[i % 4]:
                if isinstance(step, int):
                    feature_values[feat] = st.slider(label, int(lo), int(hi), int(default), int(step), key=f"fw_{feat}")
                else:
                    feature_values[feat] = st.slider(label, float(lo), float(hi), float(default), float(step), key=f"fw_{feat}")

        # Group 2: Variability features
        st.markdown("**Variability Features**")
        cols = st.columns(4)
        var_feats = ["ASTV", "MSTV", "ALTV", "MLTV"]
        for i, feat in enumerate(var_feats):
            label, lo, hi, default, step = CTG_DISPLAY[feat]
            with cols[i % 4]:
                if isinstance(step, int) or step >= 1:
                    feature_values[feat] = st.slider(label, int(lo), int(hi), int(default), int(step), key=f"fw_{feat}")
                else:
                    feature_values[feat] = st.slider(label, float(lo), float(hi), float(default), float(step), key=f"fw_{feat}")

        # Group 3: Histogram features
        st.markdown("**Histogram Features**")
        cols = st.columns(4)
        hist_feats = ["Width", "Min", "Max", "Nmax", "Nzeros", "Mode", "Mean", "Median", "Variance", "Tendency"]
        for i, feat in enumerate(hist_feats):
            label, lo, hi, default, step = CTG_DISPLAY[feat]
            with cols[i % 4]:
                if isinstance(step, int) or step >= 1:
                    feature_values[feat] = st.slider(label, int(lo), int(hi), int(default), int(step), key=f"fw_{feat}")
                else:
                    feature_values[feat] = st.slider(label, float(lo), float(hi), float(default), float(step), key=f"fw_{feat}")

        predict_fw = st.form_submit_button("🔍 Predict Fetal Risk", use_container_width=True)

    if predict_fw:
        if fw_model is None:
            st.error("Model not available. Please ensure model artifacts are trained.")
        else:
            try:
                input_arr = np.array([[feature_values[f] for f in FW_FEATURES]])
                input_df  = pd.DataFrame(input_arr, columns=FW_FEATURES)

                prediction  = fw_model.predict(input_df)[0]
                probas      = fw_model.predict_proba(input_df)[0]
                classes     = list(fw_model.classes_)

                st.markdown("---")
                st.subheader("🔬 Prediction Result")

                badge = risk_badge(prediction)
                st.markdown(f"#### Predicted Class: {badge}", unsafe_allow_html=True)
                confidence = max(probas) * 100
                st.metric("Model Confidence", f"{confidence:.1f}%")

                st.markdown("**Prediction Probabilities**")
                prob_bar_chart(probas, classes)

                st.markdown("---")
                st.subheader("📋 Clinical Recommendation")
                st.markdown(FW_RECOMMENDATIONS.get(prediction, "No recommendation available."))

                # Show input summary
                with st.expander("📊 View Input Summary"):
                    st.dataframe(input_df.T.rename(columns={0: "Value"}), use_container_width=True)

            except Exception as e:
                st.error(f"Prediction failed: {e}. Ensure the model is compatible with the 21-feature input.")


# ═════════════════════════════════════════════
# PAGE 3 — MATERNALGUARD PREDICTION
# ═════════════════════════════════════════════
elif "MaternalGuard" in page:
    st.markdown(
        "<h2 style='color:#00695c;'>🤱 MaternalGuard — Maternal Risk Prediction</h2>"
        "<p style='color:#555;'>Enter 6 maternal vital-sign features to assess risk level.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    mg_model, mg_le = load_maternalguard()

    with st.form("maternalguard_form"):
        st.subheader("Maternal Vital Signs")
        mat_values = {}
        cols = st.columns(3)
        for i, feat in enumerate(MG_FEATURES):
            label, lo, hi, default, step = MATERNAL_DISPLAY[feat]
            with cols[i % 3]:
                if feat == "BS":
                    mat_values[feat] = st.number_input(label, min_value=float(lo), max_value=float(hi),
                                                       value=float(default), step=float(step), key=f"mg_{feat}")
                elif feat == "BodyTemp":
                    mat_values[feat] = st.number_input(label, min_value=float(lo), max_value=float(hi),
                                                       value=float(default), step=float(step), key=f"mg_{feat}")
                else:
                    mat_values[feat] = st.slider(label, int(lo), int(hi), int(default), int(step), key=f"mg_{feat}")

        predict_mg = st.form_submit_button("🔍 Predict Maternal Risk", use_container_width=True)

    if predict_mg:
        if mg_model is None or mg_le is None:
            st.error("Model not available. Please ensure model artifacts are trained.")
        else:
            try:
                input_arr = np.array([[mat_values[f] for f in MG_FEATURES]])
                input_df  = pd.DataFrame(input_arr, columns=MG_FEATURES)

                pred_idx  = mg_model.predict(input_df)[0]
                probas    = mg_model.predict_proba(input_df)[0]

                # Decode using label encoder
                prediction = mg_le.inverse_transform([pred_idx])[0]
                classes    = list(mg_le.inverse_transform(mg_model.classes_))

                st.markdown("---")
                st.subheader("🔬 Prediction Result")

                badge = risk_badge(prediction)
                st.markdown(f"#### Predicted Risk: {badge}", unsafe_allow_html=True)
                confidence = max(probas) * 100
                st.metric("Model Confidence", f"{confidence:.1f}%")

                st.markdown("**Prediction Probabilities**")
                prob_bar_chart(probas, classes)

                st.markdown("---")
                st.subheader("📋 Clinical Recommendation")
                st.markdown(MG_RECOMMENDATIONS.get(prediction, "No recommendation available."))

                with st.expander("📊 View Input Summary"):
                    st.dataframe(input_df.T.rename(columns={0: "Value"}), use_container_width=True)

            except Exception as e:
                st.error(f"Prediction failed: {e}. Ensure the model is compatible with the 6-feature input.")


# ═════════════════════════════════════════════
# PAGE 4 — PRETERMGUARD PREDICTION
# ═════════════════════════════════════════════
elif "PretermGuard" in page:
    st.markdown(
        "<h2 style='color:#00695c;'>👶 PretermGuard — Preterm Birth Risk Prediction</h2>"
        "<p style='color:#555;'>Enter 21 CTG (Cardiotocography) features below to assess preterm birth / fetal distress risk.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    pg_model = load_pretermguard()

    with st.form("pretermguard_form"):
        st.subheader("CTG Feature Inputs")
        pg_feature_values = {}

        # Group 1: Signal features
        st.markdown("**Signal Features**")
        cols = st.columns(4)
        signal_feats = ["LB", "AC", "FM", "UC", "DL", "DS", "DP"]
        for i, feat in enumerate(signal_feats):
            label, lo, hi, default, step = CTG_DISPLAY[feat]
            with cols[i % 4]:
                if isinstance(step, int):
                    pg_feature_values[feat] = st.slider(label, int(lo), int(hi), int(default), int(step), key=f"pg_{feat}")
                else:
                    pg_feature_values[feat] = st.slider(label, float(lo), float(hi), float(default), float(step), key=f"pg_{feat}")

        # Group 2: Variability features
        st.markdown("**Variability Features**")
        cols = st.columns(4)
        var_feats = ["ASTV", "MSTV", "ALTV", "MLTV"]
        for i, feat in enumerate(var_feats):
            label, lo, hi, default, step = CTG_DISPLAY[feat]
            with cols[i % 4]:
                if isinstance(step, int) or step >= 1:
                    pg_feature_values[feat] = st.slider(label, int(lo), int(hi), int(default), int(step), key=f"pg_{feat}")
                else:
                    pg_feature_values[feat] = st.slider(label, float(lo), float(hi), float(default), float(step), key=f"pg_{feat}")

        # Group 3: Histogram features
        st.markdown("**Histogram Features**")
        cols = st.columns(4)
        hist_feats = ["Width", "Min", "Max", "Nmax", "Nzeros", "Mode", "Mean", "Median", "Variance", "Tendency"]
        for i, feat in enumerate(hist_feats):
            label, lo, hi, default, step = CTG_DISPLAY[feat]
            with cols[i % 4]:
                if isinstance(step, int) or step >= 1:
                    pg_feature_values[feat] = st.slider(label, int(lo), int(hi), int(default), int(step), key=f"pg_{feat}")
                else:
                    pg_feature_values[feat] = st.slider(label, float(lo), float(hi), float(default), float(step), key=f"pg_{feat}")

        predict_pg = st.form_submit_button("🔍 Predict Preterm Risk", use_container_width=True)

    if predict_pg:
        if pg_model is None:
            st.error("Model not available. Please ensure model artifacts are trained.")
        else:
            try:
                input_arr = np.array([[pg_feature_values[f] for f in FW_FEATURES]])
                input_df  = pd.DataFrame(input_arr, columns=FW_FEATURES)

                prediction  = pg_model.predict(input_df)[0]
                probas      = pg_model.predict_proba(input_df)[0]
                classes     = list(pg_model.classes_)

                st.markdown("---")
                st.subheader("🔬 Prediction Result")

                badge = risk_badge(prediction)
                st.markdown(f"#### Predicted Class: {badge}", unsafe_allow_html=True)
                confidence = max(probas) * 100
                st.metric("Model Confidence", f"{confidence:.1f}%")

                st.markdown("**Prediction Probabilities**")
                prob_bar_chart(probas, classes)

                st.markdown("---")
                st.subheader("📋 Clinical Recommendation")
                st.markdown(PG_RECOMMENDATIONS.get(prediction, "No recommendation available."))

                # Show input summary
                with st.expander("📊 View Input Summary"):
                    st.dataframe(input_df.T.rename(columns={0: "Value"}), use_container_width=True)

            except Exception as e:
                st.error(f"Prediction failed: {e}. Ensure the model is compatible with the 21-feature input.")


# ═════════════════════════════════════════════
# PAGE 6 — AI AGENT WORKFLOW (LangGraph)
# ═════════════════════════════════════════════
elif "AI Agents" in page:
    # --- Async helper -------------------------------------------------
    def _run_async(coro):
        """Run an async coroutine from sync Streamlit context."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, coro).result()
            return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    # --- Quick-test scenario presets ----------------------------------
    SCENARIOS = {
        "Normal Pregnancy": {
            "age": 26, "gestational_week": 28, "systolic_bp": 118,
            "diastolic_bp": 76, "blood_sugar": 5.2, "body_temp": 98.4,
            "heart_rate": 74, "spo2": 98, "symptoms": [],
            "include_ctg": False,
        },
        "High Risk Emergency": {
            "age": 34, "gestational_week": 34, "systolic_bp": 180,
            "diastolic_bp": 120, "blood_sugar": 9.8, "body_temp": 101.2,
            "heart_rate": 110, "spo2": 93, "symptoms": ["headache", "blurred vision", "swelling", "bleeding"],
            "include_ctg": False,
        },
        "Fetal Distress": {
            "age": 30, "gestational_week": 36, "systolic_bp": 145,
            "diastolic_bp": 95, "blood_sugar": 7.5, "body_temp": 99.0,
            "heart_rate": 92, "spo2": 96, "symptoms": ["reduced fetal movement"],
            "include_ctg": True,
        },
    }

    PATHOLOGICAL_CTG = {
        "LB": 155, "AC": 0, "FM": 5, "UC": 12, "DL": 6, "DS": 4, "DP": 3,
        "ASTV": 85, "MSTV": 0.5, "ALTV": 65, "MLTV": 2.0, "Width": 42,
        "Min": 60, "Max": 165, "Nmax": 8, "Nzeros": 10, "Mode": 155,
        "Mean": 150, "Median": 152, "Variance": 8, "Tendency": -0.8,
    }

    # --- Sidebar: quick test scenarios --------------------------------
    with st.sidebar:
        st.markdown("---")
        st.markdown("<p style='color:white; font-weight:600;'>⚡ Quick Test Scenarios</p>", unsafe_allow_html=True)
        if st.button("🟢 Normal Pregnancy", key="scenario_normal"):
            st.session_state["agent_scenario"] = "Normal Pregnancy"
            st.rerun()
        if st.button("🔴 High Risk Emergency", key="scenario_emergency"):
            st.session_state["agent_scenario"] = "High Risk Emergency"
            st.rerun()
        if st.button("🟠 Fetal Distress", key="scenario_fetal"):
            st.session_state["agent_scenario"] = "Fetal Distress"
            st.rerun()

    # --- Page header --------------------------------------------------
    st.markdown(
        "<h2 style='color:#00695c;'>🤖 MaaHifazat AI — Multi-Agent Assessment</h2>"
        "<p style='color:#555;'>Runs the full LangGraph workflow: 9 AI agents perform intake, risk assessment, "
        "fetal monitoring, ANC follow-up, referral, communication, and clinician review — powered by Groq LLM.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # --- Load scenario if selected ------------------------------------
    active_scenario = st.session_state.get("agent_scenario", None)
    preset = SCENARIOS.get(active_scenario, {})

    # --- Patient Input Form -------------------------------------------
    with st.form("agent_workflow_form"):
        st.subheader("👤 Patient Information")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            patient_name = st.text_input("Name", value=preset.get("name", ""), key="ai_name")
        with col2:
            patient_age = st.number_input("Age (years)", 10, 60, value=preset.get("age", 25), key="ai_age")
        with col3:
            gestational_week = st.number_input("Gestational Week", 4, 44, value=preset.get("gestational_week", 28), key="ai_gw")
        with col4:
            language = st.selectbox("Language", ["en", "ur", "ps"], index=0, key="ai_lang",
                                    format_func=lambda x: {"en": "English", "ur": "Urdu", "ps": "Pashto"}[x])

        st.subheader("📍 Location")
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input("Latitude", value=34.0080, format="%.4f", key="ai_lat")
        with col2:
            longitude = st.number_input("Longitude", value=71.5785, format="%.4f", key="ai_lon")

        st.subheader("🩺 Vitals")
        col1, col2, col3 = st.columns(3)
        with col1:
            systolic_bp = st.number_input("Systolic BP (mmHg)", 60, 220, value=preset.get("systolic_bp", 120), key="ai_sbp")
            blood_sugar = st.number_input("Blood Sugar (mmol/L)", 0.0, 25.0, value=float(preset.get("blood_sugar", 5.5)), step=0.1, key="ai_bs")
        with col2:
            diastolic_bp = st.number_input("Diastolic BP (mmHg)", 30, 140, value=preset.get("diastolic_bp", 80), key="ai_dbp")
            body_temp = st.number_input("Body Temp (°F)", 95.0, 106.0, value=float(preset.get("body_temp", 98.6)), step=0.1, key="ai_temp")
        with col3:
            heart_rate = st.number_input("Heart Rate (bpm)", 30, 180, value=preset.get("heart_rate", 72), key="ai_hr")
            spo2 = st.number_input("SpO2 (%)", 70, 100, value=preset.get("spo2", 98), key="ai_spo2")

        SYMPTOM_OPTIONS = ["headache", "blurred vision", "swelling", "bleeding",
                           "reduced fetal movement", "fever", "abdominal pain"]
        default_symptoms = preset.get("symptoms", [])
        symptoms = st.multiselect("Symptoms", options=SYMPTOM_OPTIONS,
                                  default=[s for s in default_symptoms if s in SYMPTOM_OPTIONS],
                                  key="ai_symptoms")

        st.subheader("🫀 CTG Data (Optional)")
        include_ctg = st.checkbox("Include CTG features for fetal monitoring", value=preset.get("include_ctg", False), key="ai_ctg")
        ctg_features = {}
        if include_ctg:
            use_sample = st.checkbox("📋 Use Pathological Sample CTG Data", value=preset.get("include_ctg", False), key="ai_ctg_sample")
            st.markdown("*Enter 21 CTG features or use the sample data button above.*")
            cols = st.columns(4)
            for i, (feat, (label, lo, hi, default, step)) in enumerate(CTG_DISPLAY.items()):
                with cols[i % 4]:
                    val = PATHOLOGICAL_CTG.get(feat, default) if use_sample else default
                    if step >= 1:
                        ctg_features[feat] = st.number_input(label, value=int(val), key=f"ai_ctg_{feat}")
                    else:
                        ctg_features[feat] = st.number_input(label, value=float(val), step=float(step), key=f"ai_ctg_{feat}")

        run_workflow_btn = st.form_submit_button("🚀 Run Full Assessment", use_container_width=True)

    # --- Execute workflow ---------------------------------------------
    if run_workflow_btn:
        # Build initial state
        patient_id = f"P-{uuid.uuid4().hex[:8].upper()}"
        case_id = f"C-{uuid.uuid4().hex[:8].upper()}"

        initial_state = {
            "patient_id": patient_id,
            "case_id": case_id,
            "language": language,
            "channel": "app",
            "demographics": {
                "name": patient_name,
                "age": patient_age,
                "gestational_age_weeks": gestational_week,
                "latitude": latitude,
                "longitude": longitude,
            },
            "vitals": {
                "systolic_bp": systolic_bp,
                "diastolic_bp": diastolic_bp,
                "heart_rate": heart_rate,
                "temperature_celsius": body_temp,
                "blood_sugar": blood_sugar,
                "spo2": spo2,
                "gestational_age_weeks": gestational_week,
                # Also include keys the models expect
                "SystolicBP": systolic_bp,
                "DiastolicBP": diastolic_bp,
                "HeartRate": heart_rate,
                "BodyTemp": body_temp,
                "BS": blood_sugar,
                "Age": patient_age,
            },
            "symptoms": symptoms,
            "intake_complete": True,
            "emergency": False,
            "audit_trail": [],
            "errors": [],
        }

        if include_ctg and ctg_features:
            initial_state["ctg_data"] = ctg_features

        # Import and run the REAL workflow
        try:
            from backend.agents.orchestrator import run_workflow as _run_wf

            with st.spinner("🧠 Running 9 AI agents — intake, risk assessment, fetal monitoring, referral, communication, review…"):
                result = _run_async(_run_wf(initial_state))

            st.session_state["agent_result"] = result
            st.session_state["agent_patient_id"] = patient_id
            st.session_state["agent_case_id"] = case_id

        except Exception as e:
            st.error(f"Workflow execution failed: {e}")
            import traceback
            with st.expander("🔍 View Traceback"):
                st.code(traceback.format_exc())

    # --- Display Results -----------------------------------------------
    result = st.session_state.get("agent_result")
    if result is not None:
        st.markdown("---")
        pid = st.session_state.get("agent_patient_id", "N/A")
        cid = st.session_state.get("agent_case_id", "N/A")
        st.markdown(f"**Patient ID:** `{pid}` &nbsp;|&nbsp; **Case ID:** `{cid}`")

        is_emergency = result.get("emergency", False)

        # ---- Emergency Banner ----
        if is_emergency:
            st.markdown(
                """<div style='background:#b71c1c; color:white; padding:18px 24px; border-radius:10px;
                    font-size:1.2rem; font-weight:700; text-align:center; margin:12px 0;
                    animation: pulse 1.5s infinite;'>
                🚨 EMERGENCY ALERT — Immediate medical attention required! 🚨
                </div>
                <style>
                @keyframes pulse {
                    0% { box-shadow: 0 0 0 0 rgba(183,28,28,0.7); }
                    70% { box-shadow: 0 0 0 15px rgba(183,28,28,0); }
                    100% { box-shadow: 0 0 0 0 rgba(183,28,28,0); }
                }
                </style>""",
                unsafe_allow_html=True,
            )

        # ---- 1. Risk Assessment ----
        clinical_risk = result.get("clinical_risk_result") or {}
        with st.expander("🩺 Risk Assessment", expanded=True):
            if clinical_risk:
                maternal = clinical_risk.get("maternal_risk") or {}
                risk_level = maternal.get("risk_level", "unknown")
                risk_map = {
                    "high risk": ("🔴", "risk-high"),
                    "mid risk": ("🟠", "risk-mid"),
                    "low risk": ("🟢", "risk-low"),
                }
                emoji, cls = risk_map.get(risk_level.lower() if isinstance(risk_level, str) else "", ("⚪", "risk-normal"))
                st.markdown(f"#### {emoji} Maternal Risk: <span class='{cls}'>{risk_level.upper()}</span>", unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                c1.metric("Risk Level", risk_level)
                c2.metric("Confidence", f"{maternal.get('confidence', 0):.1%}")
                c3.metric("WHO Triage", clinical_risk.get("who_red_flags", {}).get("triage_level", "N/A"))

                # LLM Risk Summary
                risk_summary = clinical_risk.get("risk_summary", "")
                if risk_summary:
                    st.markdown("**AI-Generated Risk Summary:**")
                    st.info(risk_summary)
                    if clinical_risk.get("llm_generated"):
                        st.caption("✅ Generated by Groq LLM")

                # WHO Red Flags
                who = clinical_risk.get("who_red_flags") or {}
                triggered = who.get("triggered_rules", [])
                if triggered:
                    st.markdown("**⚠️ WHO Red Flags Triggered:**")
                    for rule in triggered:
                        st.warning(f"• {rule}")
                actions = who.get("recommended_actions", [])
                if actions:
                    st.markdown("**Recommended Actions:**")
                    for act in actions:
                        st.markdown(f"- {act}")
            else:
                st.info("No clinical risk assessment was performed.")

        # ---- 2. Fetal Health ----
        fetal = result.get("fetal_result") or {}
        if fetal.get("fetal_status") and fetal["fetal_status"] != "not_assessed":
            with st.expander("🫀 Fetal Health Assessment", expanded=True):
                status = fetal.get("fetal_status", "unknown")
                status_colors = {"normal": "🟢", "suspect": "🟠", "pathological": "🔴"}
                icon = status_colors.get(status.lower(), "⚪")
                st.markdown(f"#### {icon} Fetal Status: **{status.upper()}**")

                c1, c2, c3 = st.columns(3)
                c1.metric("Fetal Status", status)
                c2.metric("Fetal Confidence", f"{fetal.get('fetal_confidence', 0):.1%}")
                c3.metric("Preterm Risk", fetal.get("preterm_risk", "N/A"))

                if fetal.get("escalate"):
                    st.warning("⚠️ Escalation recommended based on fetal/preterm assessment.")

        # ---- 3. ANC Follow-up ----
        anc = result.get("anc_result") or {}
        if anc:
            with st.expander("📅 ANC Follow-up", expanded=False):
                c1, c2, c3 = st.columns(3)
                c1.metric("Missed Visit Risk", f"{anc.get('missed_visit_risk', 0):.3f}")
                c2.metric("Priority", anc.get("priority", "N/A"))
                c3.metric("Action", anc.get("recommended_action", "N/A"))

                risk_factors = anc.get("risk_factors", [])
                if risk_factors:
                    st.markdown("**Risk Factors:** " + ", ".join(risk_factors))

        # ---- 4. Referral ----
        referral = result.get("referral_result") or {}
        if referral.get("selected_facility"):
            with st.expander("🏥 Referral", expanded=False):
                fac = referral["selected_facility"]
                c1, c2, c3 = st.columns(3)
                c1.metric("Facility", fac.get("name", "N/A"))
                c2.metric("Distance (km)", f"{fac.get('distance_km', 'N/A')}")
                c3.metric("Travel Time", f"{referral.get('estimated_travel_time_min', 'N/A')} min")

                st.markdown(f"**Urgency:** {referral.get('urgency_level', 'N/A').upper()}")
                caps = referral.get("capabilities_needed", {})
                if caps:
                    needed = [k for k, v in caps.items() if v]
                    st.markdown(f"**Capabilities Needed:** {', '.join(needed)}")

        # ---- 5. Communication ----
        comm = result.get("communication_result") or {}
        if comm:
            with st.expander("📱 Communication & Messages", expanded=False):
                c1, c2, c3 = st.columns(3)
                c1.metric("Messages Sent", comm.get("messages_sent", 0))
                c2.metric("All Delivered", "Yes" if comm.get("all_delivered") else "No")
                c3.metric("Channel", comm.get("channel_used", "N/A"))

                if comm.get("is_emergency_alert"):
                    st.error("🚨 Emergency alert was dispatched")

                # Show delivery details
                delivery = comm.get("delivery_status", [])
                if delivery:
                    st.markdown("**Message Delivery Log:**")
                    for i, msg in enumerate(delivery):
                        recipient = msg.get("recipient", "N/A")
                        status = msg.get("status", "unknown")
                        channel = msg.get("channel", "N/A")
                        icon = "✅" if status == "delivered" else "❌"
                        st.markdown(f"{icon} Message {i+1}: **{status}** via {channel} → {recipient}")

                if comm.get("llm_generated"):
                    st.caption("✅ Messages generated by Groq LLM")

        # ---- 6. Case Summary (Clinician Review) ----
        clinician = result.get("clinician_result") or {}
        if clinician:
            with st.expander("📋 Case Summary — Clinician Review", expanded=True):
                if clinician.get("requires_immediate_attention"):
                    st.error("⚠️ This case requires **immediate attention**")

                risk_indicators = clinician.get("risk_indicators", [])
                if risk_indicators:
                    st.markdown("**Risk Indicators:**")
                    for ri in risk_indicators:
                        st.warning(f"• {ri}")

                case_text = clinician.get("case_summary_text", "")
                if case_text:
                    st.markdown("**AI-Generated Case Summary:**")
                    st.info(case_text)
                    if clinician.get("llm_generated"):
                        st.caption("✅ Generated by Groq LLM")

                st.markdown(f"**Review Status:** {clinician.get('status', 'N/A')}")

        # ---- 7. Audit Trail ----
        audit = result.get("audit_trail", [])
        if audit:
            with st.expander(f"🕐 Audit Trail ({len(audit)} entries)", expanded=False):
                audit_df = pd.DataFrame(audit)
                if "timestamp" in audit_df.columns:
                    audit_df = audit_df.sort_values("timestamp")
                st.dataframe(audit_df, use_container_width=True, hide_index=True)

        # ---- Errors ----
        errors = result.get("errors", [])
        if errors:
            with st.expander(f"⚠️ Errors ({len(errors)})", expanded=True):
                for err in errors:
                    agent = err.get("agent", "unknown")
                    msg = err.get("error", str(err))
                    st.error(f"**{agent}**: {msg}")


# ═════════════════════════════════════════════
# PAGE 5 — MODEL PERFORMANCE
# ═════════════════════════════════════════════
elif "Performance" in page:
    st.markdown(
        "<h2 style='color:#00695c;'>📊 Model Performance Dashboard</h2>"
        "<p style='color:#555;'>Comprehensive evaluation metrics for all prediction models.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    fw_res = load_results(FW_RESULTS)
    mg_res = load_results(MG_RESULTS)
    pg_res = load_results(PG_RESULTS)

    # ── FetalWatch Performance ──
    st.subheader("🫀 FetalWatch Performance")
    fw_best_name = fw_res.get("best_model", "RandomForest")
    fw_data = fw_res.get(fw_best_name, {})

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Best Model", fw_best_name)
    m2.metric("Macro F1-Score", f"{fw_data.get('macro_f1', 0):.4f}")
    m3.metric("AUROC (OVR Macro)", f"{fw_data.get('auroc_ovr_macro', 0):.4f}")
    report = fw_data.get("classification_report", {})
    m4.metric("Overall Accuracy", f"{report.get('accuracy', 0):.4f}")

    per_class = fw_data.get("per_class", {})
    if per_class:
        st.markdown("**Per-Class Metrics**")
        rows = []
        for cls, metrics in per_class.items():
            rows.append({
                "Class": cls,
                "Precision": f"{metrics['precision']:.4f}",
                "Recall":    f"{metrics['recall']:.4f}",
                "F1-Score":  f"{metrics['f1-score']:.4f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Plot images
    fw_plots = ["fw_roc_curves.png", "fw_confusion_matrix.png", "fw_feature_importance.png", "fw_calibration.png"]
    fw_plot_paths = [PLOTS_DIR / p for p in fw_plots]
    available_fw_plots = [p for p in fw_plot_paths if p.exists()]
    if available_fw_plots:
        st.markdown("**Diagnostic Plots**")
        cols = st.columns(2, gap="large")
        for i, p in enumerate(available_fw_plots):
            with cols[i % 2]:
                st.image(str(p), caption=p.stem.replace("fw_", "").replace("_", " ").title(),
                         use_container_width=True)

    st.markdown("---")

    # ── MaternalGuard Performance ──
    st.subheader("🤱 MaternalGuard Performance")
    mg_best_name = mg_res.get("best_model", "LightGBM")
    mg_models = mg_res.get("models", {})
    mg_data = mg_models.get(mg_best_name, {})

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Best Model", mg_best_name)
    m2.metric("Macro F1-Score", f"{mg_data.get('macro_f1', 0):.4f}")
    m3.metric("AUROC (OVR)", f"{mg_data.get('auroc_ovr', 0):.3f}")
    mg_report = mg_data.get("per_class", {})
    # Compute macro precision/recall from per-class
    if mg_report:
        precisions = [v["precision"] for v in mg_report.values()]
        recalls    = [v["recall"] for v in mg_report.values()]
        m4.metric("Macro Precision", f"{np.mean(precisions):.4f}")

    if mg_report:
        st.markdown("**Per-Class Metrics**")
        rows = []
        for cls, metrics in mg_report.items():
            rows.append({
                "Class": cls,
                "Precision": f"{metrics['precision']:.4f}",
                "Recall":    f"{metrics['recall']:.4f}",
                "F1-Score":  f"{metrics['f1-score']:.4f}",
                "Support":   int(metrics.get("support", 0)),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Feature importance
    feat_imp = mg_res.get("feature_importance", {})
    if feat_imp:
        st.markdown("**Feature Importance (LightGBM Split Count)**")
        fi_df = pd.DataFrame({"Feature": feat_imp.keys(), "Importance": feat_imp.values()})
        fi_df = fi_df.sort_values("Importance", ascending=True)
        st.bar_chart(fi_df.set_index("Feature"), color="#00897b")

    st.markdown("---")

    # ── PretermGuard Performance ──
    st.subheader("👶 PretermGuard Performance")
    pg_best_name = pg_res.get("best_model", "LightGBM")
    pg_best_data = pg_res.get(pg_best_name, {})

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Best Model", pg_best_name)
    m2.metric("Macro F1-Score", f"{pg_best_data.get('macro_f1', 0):.4f}")
    m3.metric("AUROC (OVR Macro)", f"{pg_best_data.get('auroc_ovr_macro', 0):.4f}")
    pg_report = pg_best_data.get("classification_report", {})
    m4.metric("Overall Accuracy", f"{pg_report.get('accuracy', 0):.4f}")

    pg_per_class = pg_best_data.get("per_class", {})
    if pg_per_class:
        st.markdown("**Per-Class Metrics**")
        rows = []
        for cls, metrics in pg_per_class.items():
            rows.append({
                "Class": cls,
                "Precision": f"{metrics['precision']:.4f}",
                "Recall":    f"{metrics['recall']:.4f}",
                "F1-Score":  f"{metrics['f1-score']:.4f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # All-models comparison table
    st.markdown("---")
    st.subheader("📈 All Models Comparison")
    comparison_rows = [
        {"Model": f"FetalWatch ({fw_res.get('best_model', 'N/A')})", "Task": "Fetal Health", "Macro-F1": f"{fw_res.get(fw_res.get('best_model', ''), {}).get('macro_f1', 0):.4f}"},
        {"Model": f"MaternalGuard ({mg_res.get('best_model', 'N/A')})", "Task": "Maternal Risk", "Macro-F1": f"{mg_res.get('models', {}).get(mg_res.get('best_model', ''), {}).get('macro_f1', 0):.4f}"},
        {"Model": f"PretermGuard ({pg_res.get('best_model', 'N/A')})", "Task": "Preterm Risk", "Macro-F1": f"{pg_res.get(pg_res.get('best_model', ''), {}).get('macro_f1', 0):.4f}"},
    ]
    st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True, hide_index=True)

    # ── Model Training ──
    st.markdown("---")
    st.subheader("🔧 Retrain Models")
    st.markdown(
        "<p style='color:#555;'>Trigger model retraining from the app. "
        "Training runs <code>scripts/run_models.py</code> with the correct data path and updates the artifacts on disk.</p>",
        unsafe_allow_html=True,
    )

    with st.form("train_models_form"):
        tc1, tc2 = st.columns([2, 1])
        with tc1:
            train_fw = st.checkbox("FetalWatch (CTG fetal risk)", value=True, key="tr_fw")
            train_mg = st.checkbox("MaternalGuard (maternal vitals risk)", value=True, key="tr_mg")
            train_cr = st.checkbox("CareReach (ANC missed-visit risk)", value=False, key="tr_cr")
            train_gi = st.checkbox("GestationInsight (gestational complications)", value=False, key="tr_gi")
        with tc2:
            n_trials = st.number_input("Optuna trials", 1, 50, value=5, step=1, key="tr_trials")

        train_btn = st.form_submit_button("🚀 Start Training", use_container_width=True)

    if train_btn:
        if not (train_fw or train_mg or train_cr or train_gi):
            st.warning("Select at least one model to train.")
        else:
            import subprocess, sys as _sys

            # Build a small inline script that calls run_all_models() and
            # dumps the JSON-serialisable results to stdout so we can
            # capture them here.  Optuna / lightgbm logs are suppressed.
            _script = (
                "import sys, os, json\n"
                "os.environ['PYTHONIOENCODING']='utf-8'\n"
                f"sys.path.insert(0, {str(BASE_DIR)!r})\n"
                "from scripts.run_models import run_all_models\n"
                f"results = run_all_models(n_trials={n_trials}, "
                f"train_fetalwatch={train_fw}, train_maternalguard={train_mg}, "
                f"train_carereach={train_cr}, train_gestation={train_gi}, verbose=False)\n"
                # Serialise numpy floats/ints for JSON
                "def _ser(o):\n"
                "    import numpy as _np\n"
                "    if isinstance(o, (_np.floating, float)): return float(o)\n"
                "    if isinstance(o, (_np.integer, int)): return int(o)\n"
                "    if isinstance(o, _np.ndarray): return o.tolist()\n"
                "    return str(o)\n"
                "print(json.dumps(results, default=_ser))\n"
            )

            output_placeholder = st.empty()
            with st.spinner("⏳ Training models — this may take several minutes…"):
                proc = subprocess.run(
                    [_sys.executable, "-c", _script],
                    capture_output=True, text=True, cwd=str(BASE_DIR),
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                )

            if proc.returncode != 0:
                st.error("Training failed:")
                with st.expander("🔍 View stderr"):
                    st.code(proc.stderr[-3000:] if proc.stderr else "(no stderr)")
            else:
                st.success("✅ Training complete! Artifacts updated.")
                try:
                    # Last stdout line is the JSON blob
                    json_line = proc.stdout.strip().splitlines()[-1]
                    train_results = json.loads(json_line)

                    # Show per-model highlights
                    if train_fw and "fetalwatch" in train_results:
                        fw_r = train_results["fetalwatch"]
                        best = max(fw_r, key=lambda k: fw_r[k].get("macro_f1", 0))
                        st.info(f"🫀 **FetalWatch** — Best: `{best}`, Macro-F1: `{fw_r[best].get('macro_f1', 0):.4f}`")

                    if train_mg and "maternalguard" in train_results:
                        mg_r = train_results["maternalguard"]
                        st.info(f"🤱 **MaternalGuard** — Best: `{mg_r.get('best_model')}`, Macro-F1: `{mg_r.get('best_macro_f1', 0):.4f}`")

                    if train_cr and "carereach" in train_results:
                        cr_r = train_results["carereach"]
                        status = "✅" if cr_r.get("returncode") == 0 else "❌"
                        st.info(f"📅 **CareReach** — {status} return code: {cr_r.get('returncode')}")

                    if train_gi and "gestation_insight" in train_results:
                        gi_r = train_results["gestation_insight"]
                        status = "✅" if gi_r.get("returncode") == 0 else "❌"
                        st.info(f"🤰 **GestationInsight** — {status} return code: {gi_r.get('returncode')}")

                    # Artifact status
                    artifacts = train_results.get("artifacts", {})
                    if artifacts:
                        st.markdown("**Artifact Status:**")
                        art_rows = [{"Artifact": k, "Status": "✅ Present" if v else "❌ Missing"} for k, v in artifacts.items()]
                        st.dataframe(pd.DataFrame(art_rows), use_container_width=True, hide_index=True)

                except Exception as parse_err:
                    st.warning(f"Could not parse training output: {parse_err}")
                    with st.expander("🔍 Raw stdout"):
                        st.code(proc.stdout[-2000:] if proc.stdout else "")

                st.caption("💡 Refresh the page to see updated metrics in the performance tables above.")


# ─────────────────────────────────────────────
# Footer (rendered on every page)
# ─────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    """<div class='app-footer'>
    ⚠️ <strong>Disclaimer:</strong> This is an AI-based screening tool and does NOT replace professional medical diagnosis.
    Always consult a qualified healthcare professional for clinical decisions. &nbsp;|&nbsp;
    MaaHifazat AI © 2026
    </div>""",
    unsafe_allow_html=True,
)

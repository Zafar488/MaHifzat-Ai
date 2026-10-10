"""MaaHifazat AI: End-to-end clinical maternal care application backed by FastAPI.
Unified dashboard structured into exactly TWO main sections:
- Section A: Risk Assessment (Four expandable input groups, Output 1: Bilingual Reports, Output 2: Hospital Report & Map)
- Section B: Pregnancy Helper (Clinical RAG, DuckDuckGo search, danger signs, citations, assessment sharing)
With English/Urdu bilingual support, RTL layout, and numeral normalization.
"""
import json
import uuid
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pydantic import ValidationError

from ui.api_client import APIClient, APIError
from backend.schemas.assessment import WorkflowRequest
from backend.schemas.patient import PatientCreate
from backend.services.reporting import recommended_care_actions
from ui.i18n import apply_language_styles, normalize_numerals, t
from ui.pregnancy_helper_view import render_pregnancy_helper
from app_demo_scenarios import SCENARIOS

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="MaaHifazat AI", page_icon="🤱", layout="wide")

gps_component = components.declare_component("patient_geolocation", path=str(ROOT / "ui/geolocation"))


def api():
    return APIClient(st.session_state.get("token"))


def call(method, path, **kwargs):
    try:
        return api().request(method, path, **kwargs)
    except APIError as exc:
        if exc.status_code == 401 and st.session_state.get("token"):
            st.session_state.clear()
            st.rerun()
        st.error(str(exc))
        return None


def render_referral(referral, location=None, lang="en"):
    is_ur = (lang == "ur")
    st.subheader("2 · " + ("قریبی باصلاحیت ہسپتال اور نقشہ" if is_ur else "Reach a capable hospital"))
    st.write(referral.get("reason", "Referral not yet planned"))
    if referral.get("coverage_limited"):
        st.warning(referral.get("discovery_reason", "Hospital search coverage is limited."))
    facilities = referral.get("ranked_facilities", [])
    if not facilities:
        st.warning(
            "کوئی مطابقت رکھنے والا ہسپتال دستیاب نہیں۔ زچگی کی ہنگامی صورت حال میں دستی طور پر ہسپتال سے رابطہ کریں۔"
            if is_ur else
            "No matching hospital candidate available. Contact maternity services manually; emergency care must not wait."
        )
        return
    if referral.get("simulated"):
        st.warning("DEMO: fictional facilities and coordinates. These are not real care destinations.")
    selected = referral["selected_facility"]
    st.write("**" + ("تجویز کردہ ہسپتال: " if is_ur else "Suggested candidate: ") + "**" + selected["name"])
    columns = st.columns(3)
    columns[0].metric("Distance (فاصلہ)", f"{selected['distance_km']:.2f} km")
    columns[1].metric("Distance type", selected["distance_kind"].replace("_", " "))
    eta = selected.get("travel_time_minutes")
    columns[2].metric("Road ETA (تخمینی وقت)", f"{eta:.0f} min" if eta is not None else "Unavailable")

    if not selected.get("capabilities_verified") and not referral.get("simulated"):
        st.warning(
            "ہسپتال نقشے پر موجود ہے؛ زچگی، ایمرجنسی اور نوزائیدہ بچوں کے این آئی سی یو کی سہولیات کی براہ راست تصدیق ضروری ہے۔"
            if is_ur else
            "Actual mapped hospital; maternity, emergency and NICU capabilities require direct confirmation. This is a tentative referral candidate."
        )

    def service(f, key):
        if f.get("capabilities_verified") or f.get("simulated"):
            return str(f.get(key))
        value = (f.get("reported_services") or {}).get(key)
        return "Reported yes" if value is True else "Reported no" if value is False else "Unknown"

    rows = [{
        "Facility": f["name"],
        "Maternity": service(f, "has_maternity"),
        "Emergency": service(f, "has_emergency"),
        "Newborn/NICU": service(f, "has_nicu"),
        "Distance km": f"{f['distance_km']:.2f}",
        "Distance type": f["distance_kind"],
        "ETA min": f"{f['travel_time_minutes']:.0f}" if f.get("travel_time_minutes") is not None else "—",
        "Availability": f["availability"],
        "Confirmation needed": f["requires_availability_confirmation"]
    } for f in facilities]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    points = [{"lat": f["latitude"], "lon": f["longitude"]} for f in facilities]
    if location:
        points.append({"lat": location["latitude"], "lon": location["longitude"]})
    st.map(pd.DataFrame(points))

    if selected.get("directions_url"):
        st.link_button(
            "🗺️ گوگل میپس پر راستہ کھولیں (Open Google Maps Directions)" if is_ur else "Open directions (shares coordinates with Google Maps)",
            selected["directions_url"]
        )
    st.caption("Confirm service availability and acceptance by phone. Road ETA is an estimate; straight-line distance is not road distance.")

    # Supplementary Public Hospital Search via DuckDuckGo (No PII sent)
    with st.expander("🌐 " + ("ڈک ڈک گو پر عوامی ہسپتال کی اضافی معلومات (DuckDuckGo Public Search)" if is_ur else "Supplementary Public Hospital Information via DuckDuckGo")):
        st.caption("Live search for public hospital contacts and departments. No patient health information is sent.")
        hosp_query = st.text_input("Hospital search query", value=f"{selected['name']} hospital emergency maternity contact", key="hosp_q_input")
        if st.button("Search Public Hospital Web Info", key="search_ddg_hosp"):
            with st.spinner("Searching public medical listings..."):
                ddg_data = call("POST", "/helper/search", json={"query": hosp_query})
                if ddg_data and ddg_data.get("results"):
                    for item in ddg_data["results"]:
                        st.markdown(f"• **{item.get('title')}**: {item.get('snippet')} ([Web Link]({item.get('url')}))")
                else:
                    st.info("No supplementary public web listings found for this facility.")

    if referral.get("excluded_facilities"):
        with st.expander("Why nearer facilities were excluded"):
            st.dataframe(pd.DataFrame(referral["excluded_facilities"]), hide_index=True)


def render_result(result, case=None, lang="en"):
    is_ur = (lang == "ur")
    if result.get("provenance") == "demo":
        st.warning("SYNTHETIC DEMO CASE · This case is for the hackathon demonstration.")
    clinical = result.get("clinical_risk_result") or {}
    safety = clinical.get("who_red_flags") or {}
    maternal = clinical.get("maternal_risk") or {}
    fetal = result.get("fetal_result") or {}
    referral = result.get("referral_result") or {}
    anc = result.get("anc_result") or {}
    communication = result.get("communication_result") or {}
    location = result.get("location") or {}
    urgency_lvl = referral.get("urgency_level", "routine")

    # Primary Clinical Urgency Banner
    if result.get("emergency"):
        st.error(t("danger_alert_banner", lang))
    elif urgency_lvl == "urgent":
        st.warning(t("prompt_alert_banner", lang))
    else:
        st.success(t("routine_care_banner", lang))

    cols = st.columns(4)
    cols[0].metric("Rule Triage", safety.get("triage_level", "Unknown"))
    cols[1].metric("Maternal Model", maternal.get("risk_level", "Unknown").title())
    f_stat = fetal.get("fetal_status", "not_assessed")
    cols[2].metric("Fetal Model", f_stat.replace("_", " ").title() if f_stat != "not_assessed" else "Not assessed")
    cols[3].metric("Urgency Level", urgency_lvl.title())

    # Explicit Action: Share with Pregnancy Helper
    st.markdown("---")
    sc1, sc2 = st.columns([3, 1])
    sc1.info("💡 " + ("آپ اس طبی جائزے کے حقائق سیکشن 'ب — رہنما برائے حمل' کے ساتھ شیئر کر سکتے ہیں۔" if is_ur else "Share this assessment's verified findings with Section B — Pregnancy Helper to discuss guidance."))
    if sc2.button("💬 " + ("ہیلپر کے ساتھ شیئر کریں" if is_ur else "Share with Helper"), key="share_helper_btn", use_container_width=True):
        st.session_state["shared_assessment"] = result
        st.success(t("assessment_shared", lang))

    # Output 1: Prominent Two Bilingual Reports (English & Urdu Script)
    st.divider()
    st.markdown("### 📋 " + ("آؤٹ پٹ ۱ — دو طرفہ طبی رپورٹس (Output 1: Assessment & Next-Step Reports)" if is_ur else "Output 1 — Assessment and Next-Step Reports"))
    from ui.report_view import render_two_reports
    render_two_reports(result)

    st.divider()
    st.markdown("### 🏥 " + ("آؤٹ پٹ ۲ — ہسپتال رپورٹ اور تفصیلی کلینیکل کارڈز (Output 2: Hospital & Clinical Triage)" if is_ur else "Output 2 — Hospital Report & Clinical Triage Cards"))

    # CARD 1 & CARD 2: Mother's Assessment & Safety Alerts
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 👩 1. Mother’s Assessment")
        v_data = result.get("vitals", {})
        m_row = st.columns(3)
        m_row[0].metric("Systolic BP", f"{v_data.get('systolic_bp', '—')} mmHg")
        m_row[1].metric("Diastolic BP", f"{v_data.get('diastolic_bp', '—')} mmHg")
        m_row[2].metric("Heart Rate", f"{v_data.get('heart_rate', '—')} bpm")
        m_row2 = st.columns(3)
        m_row2[0].metric("Blood Sugar", f"{v_data.get('blood_sugar_mmol_l', '—')} mmol/L")
        m_row2[1].metric("Temperature", f"{v_data.get('temperature_celsius', '—')} °C")
        m_row2[2].metric("Maternal Risk", maternal.get("risk_level", "Unknown").title())
        if maternal.get("probabilities"):
            st.caption("Class probabilities: " + ", ".join(f"{k}: {v:.2f}" for k, v in maternal["probabilities"].items()))
        st.caption("MaternalGuard experimental pipeline · Uncalibrated probabilities.")

    with c2:
        st.markdown("#### 🛡️ 2. Safety Alerts & Reasons")
        for reason in safety.get("clinical_rationale", []):
            st.write("• " + reason)
        for action in recommended_care_actions(urgency_lvl, safety):
            st.info(action)
        if result.get("missing_fields"):
            st.warning("Missing measured vitals: " + ", ".join(result["missing_fields"]))

    # CARD 3 & CARD 4: Baby's Assessment & Suggested Hospital
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### 👶 3. Baby’s Assessment")
        f_cols = st.columns(2)
        f_cols[0].metric("Fetal Status", f_stat.replace("_", " ").title() if f_stat != "not_assessed" else "Not assessed")
        f_cols[1].metric("Fetal Movement", "Reduced" if v_data.get("fetal_movement_present") is False else "Normal" if v_data.get("fetal_movement_present") is True else "Unknown")
        if f_stat == "not_assessed":
            st.info("Fetal CTG assessment not performed. Movement safety information is still evaluated.")
        else:
            if fetal.get("probabilities"):
                st.caption("CTG probabilities: " + ", ".join(f"{k}: {v:.2f}" for k, v in fetal["probabilities"].items()))
            st.caption("FetalWatch measured CTG classifier.")

    with c4:
        st.markdown("#### 🏥 4. Suggested Hospital & Routing")
        selected = referral.get("selected_facility")
        if selected:
            h_cols = st.columns(3)
            h_cols[0].metric("Hospital", selected.get("name", "Unknown"))
            h_cols[1].metric("Distance", f"{selected.get('distance_km', 0):.2f} km")
            eta = selected.get("travel_time_minutes")
            h_cols[2].metric("Road ETA", f"{eta:.0f} min" if eta is not None else "Unavailable")
            if selected.get("phone"):
                st.write(f"📞 Contact: {selected['phone']}")
            if selected.get("directions_url"):
                st.link_button("🗺️ Open Google Maps Directions", selected["directions_url"])
        else:
            st.warning(referral.get("reason", "No hospital candidate available."))

    render_referral(referral, location, lang=lang)

    # CARD 5 & CARD 6: Follow-up & Notification Status
    c5, c6 = st.columns(2)
    with c5:
        st.markdown("#### 📅 5. Follow-up Recommendation")
        anc_cols = st.columns(3)
        anc_cols[0].metric("Outreach Priority", anc.get("priority", "Unknown").title())
        anc_cols[1].metric("Suggested Action", anc.get("recommended_action", "Unknown").replace("_", " ").title())
        anc_cols[2].metric("Next Appointment", anc.get("next_appointment_date") or "Needs scheduling")
        if anc.get("risk_factors"):
            st.write("Barriers: " + "; ".join(anc["risk_factors"]))
        st.caption(anc.get("reason", ""))

    with c6:
        st.markdown("#### 💬 6. Notification Status")
        st.info("Prepared Message: " + communication.get("draft_message", "No message draft available"))
        st.caption(f"Channel: {communication.get('recommended_channel', 'app').title()} · Draft prepared locally for health worker.")

    # CARD 7 & CARD 8: Doctor Handover & Audit Trail
    st.markdown("#### 📋 7. Doctor Handover & Audit Trail")
    summary = (result.get("clinician_result") or {}).get("case_summary_text") or (result.get("reporting_result") or {}).get("narrative", "Report unavailable")
    st.text(summary)
    d_cols = st.columns(2)
    d_cols[0].download_button("Download clinician handover", summary, f"handover-{result.get('case_id','case')}.txt", "text/plain")
    d_cols[1].download_button("Download case JSON", json.dumps(result, indent=2), f"case-{result.get('case_id','case')}.json", "application/json")

    assistance = (result.get("clinician_result") or {}).get("ai_assistance") or {}
    if assistance.get("llm_generated"):
        with st.expander("AI Roman Urdu Explanation & Clinician Follow-up Questions", expanded=False):
            st.write("**Family Roman Urdu:** " + assistance.get("explanation_roman_urdu", ""))
            st.write("**Clinician Context:** " + assistance.get("clinician_context", ""))
            for q in assistance.get("followup_questions", []):
                st.write("• " + q)
            st.caption(f"Groq · {assistance.get('model', '')} · Clinician review required.")

    with st.expander("Nine-Agent LangGraph Audit Trail", expanded=False):
        st.dataframe(pd.DataFrame(result.get("audit_trail", [])), hide_index=True, width="stretch")

    with st.expander("Data Quality & Research Models Evidence", expanded=False):
        st.json({"maternal": maternal, "fetal": fetal, "quality": result.get("data_quality_result"), "research": result.get("research_results")})
    for err in result.get("errors", []):
        st.error(f"{err['agent']}: {err['error']}")


def review_controls(case_id, result, review_status="pending"):
    role = st.session_state["user"]["role"]
    if role not in ("clinician", "admin"):
        st.info("An assigned clinician or admin must review this case.")
        return
    if review_status != "pending":
        st.success("Review decision: " + review_status)
        if review_status == "approved" and st.button("Complete reviewed case", key="complete_" + case_id):
            updated = call("POST", f"/agents/cases/{case_id}/resume")
            if updated:
                st.success("Reviewed case completed. Care delivery remains tracked separately.")
        return
    st.subheader("Clinician decision")
    fac = (result.get("referral_result") or {}).get("selected_facility") or {}
    with st.form("review_" + case_id):
        decision = st.selectbox("Decision", ["approved", "rejected"])
        notes = st.text_area("Clinical review notes")
        create = st.checkbox("Create referral after confirming facility services and acceptance")
        name = st.text_input("Confirmed facility name", value=fac.get("name", ""))
        urgency = st.selectbox(
            "Referral urgency", ["routine", "urgent", "emergency"],
            index=["routine", "urgent", "emergency"].index((result.get("referral_result") or {}).get("urgency_level", "routine"))
        )
        submitted = st.form_submit_button("Save review decision")
    if submitted:
        if not notes.strip():
            st.error("Add review notes.")
        else:
            reviewed = call("POST", f"/agents/cases/{case_id}/review", json={
                "decision": decision, "notes": notes, "create_referral": create, "facility_name": name or None, "urgency": urgency
            })
            if reviewed:
                st.success("Decision saved. Open Saved cases to complete or track the referral.")


# ─────────────────────────────────────────────────────────────────────────────
# APPLICATION LIFECYCLE & AUTHENTICATION
# ─────────────────────────────────────────────────────────────────────────────
try:
    health = APIClient().request("GET", "/health")
except APIError as exc:
    st.title("MaaHifazat AI")
    st.error(str(exc))
    st.code(".venv\\Scripts\\python.exe scripts/start_app.py")
    st.stop()

if "token" not in st.session_state:
    from ui.auth_view import render_auth
    render_auth(health.get("demo_mode", False))
    st.stop()

# Set and apply active language & styles
current_lang = st.session_state.get("language", "en")
apply_language_styles(current_lang)
is_ur = (current_lang == "ur")

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR CONTROLS & BILINGUAL SWITCH
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🤱 MaaHifazat AI")
st.sidebar.caption("Rural Maternal Care · Algo Titans")

user = st.session_state["user"]
role_label = {"patient": "Patient (مریضہ)", "lhw": "Lady Health Worker (ایل ایچ ڈبلیو)", "clinician": "Clinician (ڈاکٹر/کلینیشن)", "admin": "Administrator"}.get(user["role"], user["role"])
st.sidebar.markdown(f"**👤 {user['full_name']}**\n\n`< {role_label} >`", unsafe_allow_html=True)

# Language Toggle
lang_choice = st.sidebar.radio(
    "🌐 Language / زبان",
    ["English", "اردو"],
    index=0 if current_lang != "ur" else 1,
    horizontal=True
)
new_lang = "ur" if lang_choice == "اردو" else "en"
if new_lang != current_lang:
    st.session_state["language"] = new_lang
    try:
        api().request("PUT", "/auth/preferences", json={"language": new_lang, "email_notifications": True, "sms_notifications": False})
    except Exception:
        pass
    st.rerun()

if st.sidebar.button("🚪 " + ("لاگ آؤٹ (Sign out)" if is_ur else "Sign out"), use_container_width=True):
    call("POST", "/auth/logout")
    st.session_state.clear()
    st.rerun()

if health.get("demo_mode"):
    st.sidebar.warning("DEMO MODE · Synthetic cases and fictional facilities")

staff = user["role"] in ("lhw", "clinician", "admin")

# ─────────────────────────────────────────────────────────────────────────────
# EXACTLY TWO MAIN SECTIONS NAVIGATION + SUPPORTING PANELS
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("### " + ("معاون پینلز (Supporting Panels)" if is_ur else "Supporting Panels"))
supporting_view = st.sidebar.selectbox(
    "Supporting Panel",
    ["None (Main Sections)", "📁 Patient History & Saved Cases", "📅 ANC Follow-up Queue", "📊 Model Evidence & Capabilities"] + (["👥 Team Accounts"] if user["role"] == "admin" else []),
    format_func=lambda x: {
        "None (Main Sections)": "دو اہم سیکشنز (Two Main Sections)" if is_ur else "Two Main Sections",
        "📁 Patient History & Saved Cases": "📁 مریضہ کا ریکارڈ اور محفوظ کیسز" if is_ur else "📁 Patient History & Saved Cases",
        "📅 ANC Follow-up Queue": "📅 قبل از ولادت فالو اپ کیو" if is_ur else "📅 ANC Follow-up Queue",
        "📊 Model Evidence & Capabilities": "📊 ماڈل کی تحقیقی بنیاد" if is_ur else "📊 Model Evidence & Capabilities",
        "👥 Team Accounts": "👥 عملے کے اکاؤنٹس" if is_ur else "👥 Team Accounts"
    }.get(x, x)
)

# Header Title
st.title("🤱 " + ("ماں حفاظت اے آئی (MaaHifazat AI)" if is_ur else "MaaHifazat AI"))
st.caption(
    "طبی نگہداشت برائے حاملہ خواتین و کلینیکل فیصلہ سازی · کسی بھی ایمرجنسی کی صورت میں فوری ہسپتال رجوع فرمائیں۔"
    if is_ur else
    "Maternal care dashboard · Observations and model results require clinical interpretation. Emergency care must not wait."
)

# ─────────────────────────────────────────────────────────────────────────────
# ROUTING: MAIN SECTIONS VS SUPPORTING PANELS
# ─────────────────────────────────────────────────────────────────────────────
if supporting_view == "None (Main Sections)":
    # Prominent Primary Navigation for EXACTLY TWO MAIN SECTIONS
    section_options = [
        "A — Risk Assessment" if not is_ur else "الف — خطرات کا جائزہ (Risk Assessment)",
        "B — Pregnancy Helper" if not is_ur else "ب — رہنما برائے حمل (Pregnancy Helper)"
    ]
    active_section = st.radio(
        "Navigation",
        section_options,
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION A — RISK ASSESSMENT
    # ─────────────────────────────────────────────────────────────────────────
    if active_section.startswith("A") or active_section.startswith("الف"):
        st.subheader("🛡️ " + ("الف — خطرات کا جائزہ اور کلینیکل سفارشات" if is_ur else "Section A — Maternal & Fetal Risk Assessment"))
        st.caption(
            "چار توسیعی گروپس: مریضہ کی تفصیلات، ماں کی صحت، بچے کی جانچ، اور معائنے کا شیڈول۔"
            if is_ur else
            "Four expandable input groups covering patient history, mother vitals, baby movements/CTG, and follow-up care."
        )

        # Template & Draft Controls
        ctrl1, ctrl2, ctrl3 = st.columns([2, 1, 1])
        use_template = ctrl1.toggle("Use a pre-filled clinical test template", value=False)
        if use_template:
            scenario = ctrl1.selectbox("Clinical scenario template", list(SCENARIOS))
            preset = dict(SCENARIOS.get(scenario, {}))
            preset.update({"storing": True, "discover": True, "routing": True, "allow_ai": True, "run_research": True, "latitude": 34.015000, "longitude": 71.525000})
            demo = False
            key = scenario + "-template"
        else:
            demo = health.get("demo_mode")
            scenario = "Measured patient"
            preset = {}
            if st.session_state.get("case_draft"):
                preset = dict(st.session_state["case_draft"])
            key = "measured-patient"

        if ctrl2.button("💾 " + ("ڈرافٹ محفوظ کریں" if is_ur else "Save Draft"), key="btn_save_draft"):
            st.session_state["case_draft"] = preset
            st.success(t("draft_saved", current_lang))

        if st.session_state.get("case_draft") and ctrl3.button("🔄 " + ("ڈرافٹ بحال کریں" if is_ur else "Restore Draft"), key="btn_restore_draft"):
            preset = dict(st.session_state["case_draft"])
            st.info("Draft loaded into the form.")

        # Patient Profile Selection
        patients = call("GET", "/patients") or []
        options = {"Register a new patient": None, **{p["name"] + " · " + p["patient_id"][:8]: p for p in patients}}
        if not staff and patients:
            options = {p["name"] + " · " + p["patient_id"][:8]: p for p in patients}
        chosen = st.selectbox("Patient profile (مریضہ کی پروفائل)", list(options))
        patient = options[chosen]

        # Location Setup
        gps = st.session_state.get("current_location")
        if not demo:
            fresh_gps = gps_component(key="gps", default=None)
            gps = fresh_gps or gps
            if gps and (gps["latitude"], gps["longitude"], gps.get("captured_at")) != st.session_state.get("last_gps"):
                st.session_state[key + "_latitude"] = gps["latitude"]
                st.session_state[key + "_longitude"] = gps["longitude"]
                st.session_state["gps_value"] = gps
                st.session_state["last_gps"] = (gps["latitude"], gps["longitude"], gps.get("captured_at"))

        if demo and preset.get("ctg"):
            st.caption("Fetal demo uses a selected internal held-out pathological case correctly classified by the model.")

        from ui.assessment_form import render_assessment_form
        if demo and st.button("Load held-out fetal example"):
            example = call("GET", "/analytics/models/demo-ctg")
            if example:
                st.session_state["demo_ctg_json"] = json.dumps(example["features"], indent=2)
                st.rerun()

        # Render Assessment Form
        try:
            submission = render_assessment_form(patient, preset, key, demo, gps, staff)
            if submission:
                payload = submission["payload"]
                changes = submission["profile"]
                if patient is None:
                    patient = api().request("POST", "/patients", json={**changes, "location": "Synthetic demo village" if demo else "Manually recorded / GPS"})
                    payload["patient_id"] = patient["patient_id"]
                else:
                    profile = {field: patient[field] for field in PatientCreate.model_fields if field in patient}
                    profile.update(changes)
                    if any(profile[field] != patient.get(field) for field in profile):
                        patient = api().request("PUT", f"/patients/{patient['patient_id']}", json=profile)

                with st.spinner("Running the nine-agent assessment and generating both reports..."):
                    response = api().request("POST", "/agents/run" if staff else "/care/assess", json=payload)
                st.session_state["last_result"] = response["result"]
                st.session_state["last_case"] = payload["case_id"]
                st.session_state["last_submission_key"] = key
                st.success("Case saved. Mother/baby care and hospital referral reports generated.")
        except (ValueError, ValidationError, APIError) as exc:
            st.error(str(exc))

        # Show Output Reports & Hospital Referral
        if st.session_state.get("last_result") and st.session_state.get("last_submission_key") == key:
            render_result(st.session_state["last_result"], lang=current_lang)
            review_controls(st.session_state["last_case"], st.session_state["last_result"])

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION B — PREGNANCY HELPER
    # ─────────────────────────────────────────────────────────────────────────
    elif active_section.startswith("B") or active_section.startswith("ب"):
        render_pregnancy_helper(call, lang=current_lang)

# ─────────────────────────────────────────────────────────────────────────────
# SUPPORTING PANELS (COLLAPSIBLE / MODULAR)
# ─────────────────────────────────────────────────────────────────────────────
elif supporting_view == "📁 Patient History & Saved Cases":
    st.subheader("📁 " + ("مریضہ کا ریکارڈ اور محفوظ شدہ کیسز" if is_ur else "Patient History & Saved Cases"))
    patients = call("GET", "/patients") or []
    if not patients:
        st.info("Run a new assessment to create the first patient.")
    else:
        selected = st.selectbox("Patient", patients, format_func=lambda p: p["name"] + " · " + p["patient_id"][:8])
        history = call("GET", f"/patients/{selected['patient_id']}/assessments") or []
        if not history:
            st.info("No saved assessments yet.")
        else:
            encounter = st.selectbox("Saved case", history, format_func=lambda h: f"{h['created_at']} · {h['triage_level']} · {(h['case_id'] or '')[:8]}")
            if encounter["case_id"]:
                saved = call("GET", f"/agents/cases/{encounter['case_id']}")
                if saved:
                    render_result(saved["result"], saved, lang=current_lang)
                    review_controls(encounter["case_id"], saved["result"], saved["review_status"])
    referrals = call("GET", "/referrals") or []
    if referrals:
        st.subheader("Track referrals")
        st.dataframe(pd.DataFrame(referrals)[["id", "facility_name", "urgency_level", "status"]], hide_index=True)
        referral = st.selectbox("Referral", referrals, format_func=lambda r: r["facility_name"] + " · " + r["status"])
        with st.form("transition_referral"):
            status = st.selectbox("New status", ["accepted", "in_transit", "completed", "cancelled"])
            if st.form_submit_button("Record referral progress"):
                changed = call("PUT", f"/referrals/{referral['id']}/status", json={"status": status})
                if changed:
                    st.success("Referral progress saved.")

elif supporting_view == "📅 ANC Follow-up Queue":
    from ui.reminders import render_due_reminders
    render_due_reminders(call)
    st.subheader("ANC outreach queue")
    tasks = call("GET", "/followups") or []
    if not tasks:
        st.info("Follow-up tasks appear after a saved assessment.")
    else:
        patients = {p["patient_id"]: p["name"] for p in call("GET", "/patients") or []}
        rows = [{"Patient": patients.get(t["patient_id"], t["patient_id"]), "Priority": t["priority"], "Action": t["action"],
                 "Due": t["due_date"], "Status": t["status"], "Case": t["case_id"]} for t in tasks]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        pending = [t for t in tasks if t["status"] == "pending"]
        if pending and staff:
            task = st.selectbox("Pending task", pending, format_func=lambda t: f"{patients.get(t['patient_id'], t['patient_id'])} · {t['action']} · {t['priority']}")
            with st.form("resolve_task"):
                notes = st.text_area("Record actual call, visit or scheduling outcome")
                status = st.selectbox("Task outcome", ["completed", "cancelled"])
                if st.form_submit_button("Save task outcome"):
                    saved = call("PUT", f"/followups/{task['id']}", json={"status": status, "notes": notes})
                    if saved:
                        st.success("Outcome recorded.")
    profiles = call("GET", "/patients") or []
    if profiles:
        contact = st.selectbox("Contact patient / care team", profiles, format_func=lambda p: p["name"])
        if contact.get("phone"):
            from ui.contact_actions import render_contacts
            render_contacts(contact["phone"], "Please contact your maternity care team to arrange the due pregnancy checkup.", key="followup")
    st.caption("App reminders refresh while this page is open. SMS/WhatsApp composers and direct calls are user-operated; delivery is tracked locally.")

elif supporting_view == "📊 Model Evidence & Capabilities":
    from ui.model_workspace import render_workbench
    render_workbench(call)
    evidence = call("GET", "/analytics/models/evidence")
    if evidence:
        st.subheader("Clinical assessment pipelines")
        st.dataframe(pd.DataFrame(evidence["supported"]), hide_index=True, width="stretch")
        st.subheader("Clinical outcome limitations")
        st.dataframe(pd.DataFrame(evidence["disabled"]), hide_index=True, width="stretch")
        st.info("Holdout scores measure agreement with dataset labels. They do not establish clinical accuracy in rural Pakistan.")
        st.caption("All five executable tasks appear above with their actual target. Obstetric outcome validation is shown separately.")
        audit = ROOT / "docs/model_audit.json"
        if audit.exists():
            st.download_button("Download model and dataset audit", audit.read_text(encoding="utf-8"), "model_audit.json", "application/json")

elif supporting_view == "👥 Team Accounts" and user["role"] == "admin":
    st.subheader("Create a clinician or health-worker account")
    with st.form("team_account"):
        username = st.text_input("Team username")
        full_name = st.text_input("Team member name")
        password = st.text_input("Initial team password", type="password")
        role = st.selectbox("Role", ["clinician", "lhw"])
        if st.form_submit_button("Create team account"):
            created = call("POST", "/auth/users", json={"username": username, "full_name": full_name, "password": password, "role": role})
            if created:
                st.success("Account created. User ID: " + created["user_id"])
    st.subheader("Assign access to a patient")
    patients = call("GET", "/patients") or []
    if patients:
        with st.form("assign_team"):
            patient = st.selectbox("Patient to assign", patients, format_func=lambda p: p["name"])
            user_id = st.text_input("Team user ID")
            if st.form_submit_button("Assign staff access"):
                result = call("POST", f"/patients/{patient['patient_id']}/assign", json={"user_id": user_id, "is_owner": False})
                if result:
                    st.success("Staff access assigned.")

st.divider()
st.caption("MaaHifazat AI · Algo Titans · Measurements and reported symptoms require qualified clinical interpretation.")

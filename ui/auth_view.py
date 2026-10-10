"""Real account registration and sign-in with role verification and bilingual support."""
import re
import streamlit as st
from ui.api_client import APIClient, APIError

# Recognized staff verification codes for health-workers & demo clinician testing
VERIFIED_STAFF_CODES = {"MAA-CLINICIAN-2026", "LHW-VERIFIED-2026", "HACKATHON-DEMO"}


def establish_session(username, password):
    response = APIClient().request("POST", "/auth/login", data={"username": username, "password": password})
    st.session_state["token"] = response["access_token"]
    user = APIClient(response["access_token"]).request("GET", "/auth/me")
    st.session_state["user"] = user
    try:
        prefs = APIClient(response["access_token"]).request("GET", "/auth/preferences")
        if prefs and prefs.get("language"):
            st.session_state["language"] = prefs["language"]
    except Exception:
        pass
    st.rerun()


def render_auth(demo_mode=False):
    # Language selection for auth screen
    auth_lang = st.radio("Language / زبان", ["English", "اردو"], horizontal=True, index=0 if st.session_state.get("language") != "ur" else 1)
    is_ur = (auth_lang == "اردو")
    st.session_state["language"] = "ur" if is_ur else "en"

    if is_ur:
        st.title("🤱 ماں حفاظت اے آئی (MaaHifazat AI)")
        st.write("اپنا محفوظ اکاؤنٹ بنائیں، حمل کے معائنے ریکارڈ کریں اور مستند طبی رہنمائی حاصل کریں۔")
        tab_titles = ["سائن ان (Sign in)", "نیا اکاؤنٹ بنائیں (Create account)"]
    else:
        st.title("🤱 MaaHifazat AI")
        st.write("Sign in to record maternal observations, triage risk, discover verified hospitals, and access the Pregnancy Helper.")
        tab_titles = ["Sign in", "Create account"]

    signin, signup = st.tabs(tab_titles)

    with signin:
        with st.form("login"):
            username_label = "صارف کا نام یا ای میل (Username / Email)" if is_ur else "Username or Email"
            pwd_label = "پاس ورڈ (Password)" if is_ur else "Password"
            submit_label = "سائن ان کریں (Sign in)" if is_ur else "Sign in"

            username = st.text_input(username_label, value="demo-clinician" if demo_mode else "")
            password = st.text_input(pwd_label, type="password")
            submit = st.form_submit_button(submit_label, width="stretch")

        if submit:
            try:
                establish_session(username.strip(), password)
            except APIError as exc:
                st.error(f"غلطی: {exc}" if is_ur else str(exc))

        if demo_mode:
            st.caption("Optional isolated test login: `demo-clinician` · `MaaHifazat-Demo-2026!`")

    with signup:
        if is_ur:
            st.caption("مریضہ اکاؤنٹ سے آپ اپنی پروفائل اور معائنے محفوظ کر سکتے ہیں۔ کلینیشن اور ہیلتھ ورکر اکاؤنٹس کے لیے باقاعدہ تصدیق لازمی ہے۔")
        else:
            st.caption("Patients can register directly. Clinician and health-worker privileges require clinical verification rather than self-granting.")

        with st.form("signup"):
            name = st.text_input("پورا نام (Full name)" if is_ur else "Full name")
            email_or_user = st.text_input(
                "ای میل یا صارف نام (Email or Username)" if is_ur else "Email or Username",
                help="3–64 characters: letters, numbers, dot, hyphen or underscore"
            )
            preferred_lang_sel = st.selectbox(
                "ترجیحی زبان (Preferred Language)" if is_ur else "Preferred Language",
                ["ur", "en"],
                format_func=lambda l: "اردو (Urdu)" if l == "ur" else "English"
            )
            role_type = st.selectbox(
                "اکاؤنٹ کی قسم (Account Type)" if is_ur else "Account Type",
                ["Patient", "Community Health Worker (LHW)", "Clinician / Doctor"],
                help="Clinician privileges require hospital verification."
            )
            staff_code = ""
            if role_type != "Patient":
                staff_code = st.text_input(
                    "کلینیکل تصدیقی کوڈ (Clinician / Staff Verification Code)" if is_ur else "Clinician / Staff Verification Code",
                    help="Verification code issued by your health facility or hospital administration."
                )

            new_password = st.text_input(
                "پاس ورڈ بنائیں (Create password)" if is_ur else "Create password",
                type="password",
                help="At least 12 characters"
            )
            confirm = st.text_input("پاس ورڈ کی تصدیق (Confirm password)" if is_ur else "Confirm password", type="password")
            create_btn = st.form_submit_button("اکاؤنٹ بنائیں (Create my account)" if is_ur else "Create my account", width="stretch")

        if create_btn:
            sanitized_user = re.sub(r"[^a-zA-Z0-9_.-]", "_", email_or_user.strip().lower())
            if len(sanitized_user) < 3:
                st.error("صارف نام کم از کم 3 حروف پر مشتمل ہونا چاہیے۔" if is_ur else "Username/email must have at least 3 valid characters.")
            elif not name.strip():
                st.error("براہ کرم اپنا پورا نام درج کریں۔" if is_ur else "Please enter your full name.")
            elif len(new_password) < 12:
                st.error("پاس ورڈ کم از کم 12 حروف پر مشتمل ہونا چاہیے۔" if is_ur else "Password must be at least 12 characters long.")
            elif new_password != confirm:
                st.error("پاس ورڈز آپس میں میل نہیں کھاتے۔" if is_ur else "Passwords do not match.")
            elif role_type != "Patient" and staff_code.strip() not in VERIFIED_STAFF_CODES:
                st.error(
                    "کلینیشن یا ہیلتھ ورکر کی مراعات کے لیے درست تصدیقی کوڈ درکار ہے۔ بغیر تصدیق کے خود ساختہ رول کی اجازت نہیں۔"
                    if is_ur else
                    "Clinician and health-worker privileges require a valid facility verification code to prevent unauthorized privilege escalation."
                )
            else:
                try:
                    # Register standard patient identity through persistent backend endpoint
                    APIClient().request("POST", "/auth/signup", json={
                        "username": sanitized_user,
                        "password": new_password,
                        "full_name": name.strip(),
                    })
                    # Login
                    response = APIClient().request("POST", "/auth/login", data={"username": sanitized_user, "password": new_password})
                    token = response["access_token"]
                    st.session_state["token"] = token
                    st.session_state["user"] = APIClient(token).request("GET", "/auth/me")
                    st.session_state["language"] = preferred_lang_sel
                    # Save preferred language
                    try:
                        APIClient(token).request("PUT", "/auth/preferences", json={
                            "language": preferred_lang_sel,
                            "email_notifications": True,
                            "sms_notifications": False
                        })
                    except Exception:
                        pass
                    st.rerun()
                except APIError as exc:
                    st.error(str(exc))

"""Section B — Advanced Pregnancy Helper UI component.
Conversational medical education assistant grounded in WHO, NHS, and NICE clinical guidelines.
"""
import streamlit as st
from ui.api_client import APIClient, APIError
from ui.i18n import t

SUGGESTED_PROMPTS_EN = [
    "What are normal fetal movements in the 3rd trimester?",
    "Which foods and nutrients are essential during pregnancy?",
    "Is light walking or lifting safe in second trimester?",
    "What are the danger signs of pre-eclampsia?",
    "What happens during routine antenatal checkups?",
]

SUGGESTED_PROMPTS_UR = [
    "حمل کی تیسری سہ ماہی میں بچے کی حرکت کیسی ہونی چاہیے؟",
    "حاملہ خواتین کے لیے آئرن اور متوازن غذا کی کیا اہمیت ہے؟",
    "کیا حمل کے دوران ہلکی ورزش یا وزن اٹھانا محفوظ ہے؟",
    "پری ایکلیمپسیا (ہائی بلڈ پریشر) کی خطرے کی علامات کیا ہیں؟",
    "قبل از ولادت باقاعدہ معائنے (ANC) کا کیا شیڈول ہے؟",
]


def render_pregnancy_helper(call_fn, lang="en"):
    is_ur = (lang == "ur")

    st.subheader("🌸 " + ("ب — رہنما برائے حمل (Pregnancy Helper)" if is_ur else "Section B — Advanced Pregnancy Helper"))
    st.caption(
        "عالمی ادارہ صحت (WHO) اور برطانوی این ایچ ایس (NHS/NICE) کی مستند طبی ہدایات پر مبنی معلوماتی چیٹ۔"
        if is_ur else
        "Evidence-grounded education in English and Urdu, backed by WHO, NHS & NICE guidelines. Emergency care must not wait."
    )

    # 1. Shared Assessment Banner (if patient explicitly shared from Section A)
    shared = st.session_state.get("shared_assessment")
    if shared:
        vitals = shared.get("vitals", {})
        clinical = shared.get("clinical_risk_result", {})
        safety = clinical.get("who_red_flags", {})
        triage = safety.get("triage_level", "Unknown")
        bp = f"{vitals.get('systolic_bp', '—')}/{vitals.get('diastolic_bp', '—')} mmHg"
        ga = f"{vitals.get('gestational_age_weeks', '—')} weeks"

        banner_text = (
            f"📋 **شیئر شدہ طبی ریکارڈ موجود ہے:** حمل: {ga} · بلڈ پریشر: {bp} · ٹرائیج لیول: `{triage}`"
            if is_ur else
            f"📋 **Shared Patient Record Active:** Gestational Age: {ga} · BP: {bp} · Triage: `{triage}`"
        )
        st.info(banner_text)
        if st.button("شیئر شدہ ریکارڈ ہٹائیں (Clear shared record)" if is_ur else "Clear shared record", key="clear_shared"):
            st.session_state["shared_assessment"] = None
            st.rerun()

    # 2. Chat History State Management
    if "helper_chat_messages" not in st.session_state:
        st.session_state["helper_chat_messages"] = []

    # Quick Suggestion Chips
    prompts = SUGGESTED_PROMPTS_UR if is_ur else SUGGESTED_PROMPTS_EN
    st.markdown("**" + ("اکثر پوچھے جانے والے سوالات:" if is_ur else "Suggested Topics:") + "**")
    cols = st.columns(len(prompts))
    selected_prompt = None
    for idx, p in enumerate(prompts):
        if cols[idx].button(p[:28] + "...", key=f"prompt_{idx}", help=p):
            selected_prompt = p

    st.divider()

    # 3. Render Message Thread
    for msg in st.session_state["helper_chat_messages"]:
        with st.chat_message(msg["role"]):
            if msg.get("is_urgent"):
                urgent_alert = msg.get("urgent_alert") or {}
                st.error(
                    f"🚨 **{urgent_alert.get('alert_ur' if is_ur else 'alert_en', 'URGENT DANGER SIGN DETECTED')}**\n\n"
                    + (urgent_alert.get("action_ur" if is_ur else "action_en", "Seek immediate emergency hospital evaluation."))
                )
            st.markdown(msg["content"])
            citations = msg.get("citations", [])
            if citations:
                with st.expander("📚 " + ("مستند طبی حوالہ جات (Evidence & Citations)" if is_ur else "Evidence & Guidance Citations")):
                    for c in citations:
                        st.markdown(f"- **{c.get('source')}**: *{c.get('guideline')}* — {c.get('section', '')} ([View Source]({c.get('url', '#')}))")
            if msg.get("search_used"):
                st.caption("🌐 " + ("تلاش میں پبلک میڈیکل سرچ شامل کی گئی" if is_ur else "DuckDuckGo supplementary public search included"))

    # 4. User Input (from text or clicked chip)
    prompt_input = st.chat_input("اپنا سوال یہاں لکھیں... (Type your pregnancy or health question here...)" if is_ur else "Ask a pregnancy or health question...")
    user_query = selected_prompt or prompt_input

    if user_query:
        # Add User Message
        st.session_state["helper_chat_messages"].append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Call Assistant Backend via API
        with st.chat_message("assistant"):
            with st.spinner("طبی گائیڈ لائنز سے معلومات حاصل کی جا رہی ہیں..." if is_ur else "Consulting WHO/NHS guidelines and evidence..."):
                payload = {
                    "query": user_query,
                    "language": lang,
                    "shared_assessment": shared,
                    "chat_history": [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state["helper_chat_messages"][-6:]
                    ]
                }
                response = None
                try:
                    response = call_fn("POST", "/helper/chat", json=payload)
                except Exception:
                    response = None

                if not response:
                    import asyncio
                    from backend.services.pregnancy_rag import generate_pregnancy_advice
                    try:
                        response = asyncio.run(generate_pregnancy_advice(
                            query=user_query,
                            language=lang,
                            shared_assessment=shared,
                            chat_history=payload["chat_history"]
                        ))
                    except Exception as exc:
                        response = None

            if response:
                ans_text = response.get("answer", "")
                is_urgent = response.get("is_urgent", False)
                citations = response.get("citations", [])
                urgent_alert = response.get("urgent_alert") or {}

                if is_urgent:
                    st.error(
                        f"🚨 **{urgent_alert.get('alert_ur' if is_ur else 'alert_en', 'URGENT DANGER SIGN')}**\n\n"
                        + urgent_alert.get("action_ur" if is_ur else "action_en", "Seek immediate hospital evaluation.")
                    )

                st.markdown(ans_text)

                if citations:
                    with st.expander("📚 " + ("مستند طبی حوالہ جات (Evidence & Citations)" if is_ur else "Evidence & Guidance Citations")):
                        for c in citations:
                            st.markdown(f"- **{c.get('source')}**: *{c.get('guideline')}* — {c.get('section', '')} ([View Source]({c.get('url', '#')}))")

                # Store into state
                st.session_state["helper_chat_messages"].append({
                    "role": "assistant",
                    "content": ans_text,
                    "is_urgent": is_urgent,
                    "urgent_alert": urgent_alert,
                    "citations": citations,
                    "search_used": response.get("search_used", False)
                })
            else:
                st.error("طبی معاون سے جواب حاصل نہیں ہو سکا۔" if is_ur else "Could not retrieve response from Pregnancy Helper.")

    # 5. Clear Thread Button
    if st.session_state["helper_chat_messages"]:
        if st.button("گفتگو دوبارہ شروع کریں (Clear conversation)" if is_ur else "Clear conversation", key="clear_chat_btn"):
            st.session_state["helper_chat_messages"] = []
            st.rerun()

"""Bilingual localization, numeral normalization, and RTL layout styling."""
import re
import streamlit as st

URDU_NUMERAL_MAP = {
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
    "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
}

ASCII_TO_URDU_NUM_MAP = {
    "0": "۰", "1": "۱", "2": "۲", "3": "۳", "4": "۴",
    "5": "۵", "6": "۶", "7": "۷", "8": "۸", "9": "۹",
}


def normalize_numerals(value):
    """Convert Urdu/Arabic numerals to standard ASCII digits (0-9)."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    s = str(value)
    for urdu_digit, ascii_digit in URDU_NUMERAL_MAP.items():
        s = s.replace(urdu_digit, ascii_digit)
    return s.strip()


def parse_numeric(value, default=None):
    """Normalize and convert to float or int safely."""
    norm = normalize_numerals(value)
    if norm is None or norm == "":
        return default
    try:
        if "." in str(norm):
            return float(norm)
        return int(norm)
    except (ValueError, TypeError):
        return default


def format_urdu_number(num):
    """Optionally format ASCII number in Urdu digits for display."""
    if num is None:
        return ""
    s = str(num)
    for ascii_digit, urdu_digit in ASCII_TO_URDU_NUM_MAP.items():
        s = s.replace(ascii_digit, urdu_digit)
    return s


def apply_language_styles(lang="en"):
    """Inject CSS for RTL, Urdu typography, and technical LTR tags."""
    if lang == "ur":
        st.markdown("""
        <style>
        /* Urdu RTL Layout and Typography */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;600;700&display=swap');
        
        .stApp, div[data-testid="stMarkdownContainer"] p, .stRadio label, .stSelectbox label, .stTextInput label, .stNumberInput label {
            direction: rtl;
            text-align: right;
            font-family: 'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', 'Segoe UI', Tahoma, sans-serif !important;
        }
        
        /* Keep metrics, technical codes, and coordinates readable LTR */
        div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"], code, pre, .ltr-text, [data-testid="stCodeBlock"] {
            direction: ltr !important;
            text-align: left !important;
            unicode-bidi: embed !important;
            font-family: ui-monospace, Menlo, Consolas, monospace !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            direction: rtl;
        }
        
        .main-header-badge {
            background: #0f766e;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            display: inline-block;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp {
            direction: ltr;
            text-align: left;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        .main-header-badge {
            background: #0f766e;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85rem;
            display: inline-block;
        }
        </style>
        """, unsafe_allow_html=True)


MESSAGES = {
    "en": {
        "app_title": "MaaHifazat AI",
        "app_subtitle": "Clinical Maternal Care & Decision Support",
        "nav_section_a": "A — Risk Assessment",
        "nav_section_b": "B — Pregnancy Helper",
        "nav_saved_cases": "📁 Patient History & Saved Cases",
        "nav_evidence": "📊 Model Evidence & Capabilities",
        "nav_reminders": "📅 ANC Follow-up Queue",
        "nav_team": "👥 Team Provisioning",
        "sign_out": "Sign out",
        "role_badge": "Role",
        "lang_switch": "Language / زبان",
        "save_draft": "💾 Save Draft",
        "run_assessment": "⚡ Run Assessment (Save Case & Generate Both Reports)",
        "share_with_helper": "💬 Share this assessment with Pregnancy Helper",
        "draft_saved": "Draft assessment saved to local session.",
        "assessment_shared": "Current assessment shared with Section B Pregnancy Helper!",
        "danger_alert_banner": "🚨 URGENT EMERGENCY CONCERN: Seek immediate emergency maternity assessment.",
        "prompt_alert_banner": "⚠️ PROMPT CLINICIAN ASSESSMENT: Prompt maternity clinician assessment is recommended.",
        "routine_care_banner": "✅ ROUTINE CARE: No configured danger rules triggered. Continue scheduled ANC milestones.",
        "hospital_report_title": "Hospital Report & Interactive Road Route",
        "helper_title": "Section B — Advanced Pregnancy Helper",
        "helper_subtitle": "Evidence-grounded education in English and Urdu, backed by WHO, NHS & NICE guidelines.",
        "shared_case_banner": "Shared Case Active: Case {case_id} · Triage: {triage} · BP: {bp}",
    },
    "ur": {
        "app_title": "ماں حفاظت اے آئی (MaaHifazat AI)",
        "app_subtitle": "طبی نگہداشت برائے حاملہ خواتین و کلینیکل فیصلہ سازی",
        "nav_section_a": "الف — خطرات کا جائزہ (Risk Assessment)",
        "nav_section_b": "ب — رہنما برائے حمل (Pregnancy Helper)",
        "nav_saved_cases": "📁 مریضہ کا ریکارڈ اور محفوظ شدہ رپورٹس",
        "nav_evidence": "📊 ماڈل کی تحقیقی بنیاد اور صلاحیتیں",
        "nav_reminders": "📅 قبل از ولادت معائنہ جات کی فہرست",
        "nav_team": "👥 عملے کے اکاؤنٹس",
        "sign_out": "لاگ آؤٹ (Sign out)",
        "role_badge": "عہدہ",
        "lang_switch": "زبان (Language)",
        "save_draft": "💾 ڈرافٹ محفوظ کریں (Save Draft)",
        "run_assessment": "⚡ مکمل جائزہ لیں اور رپورٹس حاصل کریں",
        "share_with_helper": "💬 یہ جائزہ ہیلپر کے ساتھ شیئر کریں",
        "draft_saved": "کیس کا مسودہ (Draft) کامیابی سے محفوظ ہو گیا۔",
        "assessment_shared": "موجودہ طبی جائزہ سیکشن 'ب' کے رہنما برائے حمل کے ساتھ شیئر کر دیا گیا!",
        "danger_alert_banner": "🚨 ہنگامی خطرے کا الرٹ: فوری طور پر ایمرجنسی میٹرنٹی ہسپتال رجوع فرمائیں۔ سافٹ ویئر کا انتظار نہ کریں۔",
        "prompt_alert_banner": "⚠️ فوری معائنہ درکار: جلد از جلد لیڈی ڈاکٹر یا کلینیشن سے معائنہ کروائیں۔",
        "routine_care_banner": "✅ معمول کی نگہداشت: فی الوقت خطرے کی کوئی علامت ظاہر نہیں ہوئی۔ مقررہ شیڈول کے مطابق معائنے جاری رکھیں۔",
        "hospital_report_title": "قریبی ہسپتالوں کی رپورٹ اور نقشہ براستہ سڑک",
        "helper_title": "سیکشن ب — جدید رہنما برائے حمل (Pregnancy Helper)",
        "helper_subtitle": "عالمی ادارہ صحت (WHO) اور برطانوی این ایچ ایس (NHS/NICE) کی مستند طبی ہدایات پر مبنی معلوماتی چیٹ۔",
        "shared_case_banner": "شیئر شدہ طبی ریکارڈ: کیس {case_id} · ٹرائیج: {triage} · بی پی: {bp}",
    }
}


def t(key, lang="en", **kwargs):
    """Get localized text with optional formatting."""
    msgs = MESSAGES.get(lang, MESSAGES["en"])
    text = msgs.get(key, MESSAGES["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text

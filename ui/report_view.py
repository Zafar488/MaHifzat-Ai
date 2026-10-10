"""Display and download two bilingual reports without sending patient data to a renderer."""
import streamlit as st
from html import escape
from backend.services.bilingual_reports import build_two_reports,report_html


def render_two_reports(result):
    reports=(result.get("reporting_result") or {}).get("reports") or build_two_reports(result)
    st.subheader("Two reports · دو رپورٹس")
    st.caption("Mother/baby care and hospital referral · English + اردو · Pending clinician review")
    for kind,label in (("care","Report 1 · Mother and baby care"),("referral","Report 2 · Location and hospital referral")):
        report=reports[kind]
        with st.expander(label,expanded=True):
            english,urdu=st.tabs(["English","اردو"])
            for lang,tab in (("en",english),("ur",urdu)):
                with tab:
                    item=report["languages"][lang]
                    direction="rtl" if lang=="ur" else "ltr"
                    text=escape(item['text']).replace("\n","<br>")
                    st.markdown(f'<div lang="{lang}" dir="{direction}" style="text-align:{"right" if lang=="ur" else "left"};line-height:1.9">{text}</div>',unsafe_allow_html=True)
            st.caption("Groq bilingual explanation included" if report.get("llm_generated") else "Recorded-fact report available; bilingual Groq explanation was not generated for this case.")
            st.download_button("Download "+kind+" report · English + Urdu HTML",report_html(report),f"{kind}-report-{result.get('case_id','case')}.html","text/html",key="download_html_"+kind+str(result.get('case_id')))
            st.download_button("Download "+kind+" report · English + Urdu text","\n\n".join(report['languages'][lang]['text'] for lang in ('en','ur')),f"{kind}-report-{result.get('case_id','case')}.txt","text/plain; charset=utf-8",key="download_text_"+kind+str(result.get('case_id')))
    st.caption("HTML downloads support browser printing. Urdu text uses right-to-left layout; report facts remain on this device/server.")

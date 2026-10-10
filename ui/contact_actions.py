"""User-controlled phone actions; opening a composer is not message delivery."""
import re
from urllib.parse import quote
import streamlit as st

def contact_links(phone,message):
    cleaned=re.sub(r"[^+0-9]","",phone)
    if not re.fullmatch(r"\+?[0-9]{7,15}",cleaned):return None
    # Pakistan national numbers are normalized for WhatsApp only.
    international=cleaned.lstrip("+")
    if international.startswith("0") and len(international)==11:international="92"+international[1:]
    return {"call":"tel:"+cleaned,"sms":"sms:"+cleaned+"?body="+quote(message,safe=""),
            "whatsapp":"https://wa.me/"+international+"?text="+quote(message,safe="")}

def render_contacts(phone,message,key="contact"):
    links=contact_links(phone,message)
    if not links:
        st.caption("Valid phone number is required for phone actions.")
        return
    st.caption("Aap khud call/message initiate karte hain. WhatsApp link phone number aur prepared text WhatsApp ko share karega. SMS/call charges aapke network par depend karte hain.")
    consent=st.checkbox("I choose to open a phone or messaging app with this number and prepared text",key=key+"_contact_consent")
    st.text_area("Prepared text",value=message,key=key+"_message",height=90,disabled=True)
    if consent:
        cols=st.columns(3)
        cols[0].link_button("Call",links["call"])
        cols[1].link_button("Open SMS",links["sms"])
        cols[2].link_button("Open WhatsApp",links["whatsapp"])
    st.caption("Composer khulna delivery confirmation nahi hai. Send ya call aap apni app mein complete karein.")

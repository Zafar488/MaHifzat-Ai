"""Due tasks and urgent alerts refresh while the app is open."""
from backend.services.followup import local_today
import streamlit as st

@st.fragment(run_every="30s")
def render_due_reminders(call):
    tasks=call("GET","/followups") or []
    due=[t for t in tasks if t["status"]=="pending" and t["due_date"]<=local_today().isoformat()]
    if due:
        st.warning(f"{len(due)} care task(s) due: "+", ".join(dict.fromkeys(t["action"].replace("_"," ") for t in due)))
    alerts=call("GET","/alerts") or []
    urgent=[a for a in alerts if not a["acknowledged"] and a["type"]=="danger_sign"]
    if urgent:st.error(f"{len(urgent)} urgent care alert(s). Open Saved cases and arrange assessment.")

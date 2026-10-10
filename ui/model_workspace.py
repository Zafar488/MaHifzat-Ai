"""Run all five models through their documented input contracts."""
import json
import pandas as pd
import streamlit as st

def render_workbench(call):
    response=call("GET","/models/catalog")
    if not response:return
    models=response["models"]
    st.subheader("Five-model workspace")
    st.dataframe(pd.DataFrame([{k:m.get(k) for k in ("name","executable","target","internal_macro_f1","care_decision_use")} for m in models]),hide_index=True,width="stretch")
    available=[m for m in models if m["executable"]]
    if not available:st.warning("Models unavailable");return
    model=st.selectbox("Run a trained model",available,format_func=lambda m:m["name"])
    st.write(model["intended_use"])
    if not model["care_decision_use"]:st.info("Yeh model apne asal dataset target par prediction karta hai. Is output ko pregnancy diagnosis ya hospital urgency ke taur par use nahi kiya jata.")
    st.caption("Example input comes from the recorded artifact validation sample. Replace with compatible observations for your task.")
    with st.form("model_"+model["name"]):
        features=st.text_area("Model input JSON",value=json.dumps(model["example"],indent=2),height=220)
        if st.form_submit_button("Run model prediction"):
            try:
                data=json.loads(features)
                if not isinstance(data,dict):raise ValueError("Input must be a JSON object")
                output=call("POST","/models/predict",json={"model":model["name"],"features":data})
                if output:st.json(output)
            except ValueError as exc:st.error(str(exc))

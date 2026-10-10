"""Live patient location and actual nearby hospital discovery."""
import pandas as pd
import streamlit as st
from backend.schemas.care import PatientLocation
from pydantic import ValidationError

def distance_label(km):
    return f"{km*1000:.0f} m" if km<1 else f"{km:.2f} km"

def render_location_dashboard(call,gps_component):
    st.subheader("Live location & nearby hospitals")
    st.caption("Apni location on karein ya coordinates dein. Hospital search sirf aapki ijazat se chalegi.")
    gps=gps_component(key="dashboard_gps",default=None)
    if gps and gps.get("latitude") is not None:
        st.session_state["current_location"]=gps
    location=st.session_state.get("current_location") or {}
    share=st.checkbox("Allow coordinates to be shared with OpenStreetMap for hospital search",key="dashboard_discovery_consent")
    route=st.checkbox("Allow coordinates to be shared with openrouteservice for road distance and ETA",key="dashboard_routing_consent")
    with st.expander("Manual location / update coordinates",expanded=not bool(location)):
        with st.form("dashboard_manual_location"):
            cols=st.columns(2)
            lat=cols[0].number_input("Your latitude",min_value=-90.,max_value=90.,value=location.get("latitude"),format="%.6f")
            lon=cols[1].number_input("Your longitude",min_value=-180.,max_value=180.,value=location.get("longitude"),format="%.6f")
            if st.form_submit_button("Save my location"):
                try:
                    point=PatientLocation(latitude=lat,longitude=lon,source="manual")
                    st.session_state["current_location"]=point.model_dump(mode="json")
                    location=st.session_state["current_location"]
                    st.session_state.pop("nearby_hospitals",None)
                    st.success("Location saved.")
                except (ValidationError,TypeError):st.error("Valid latitude aur longitude dein.")
    radius=st.select_slider("Search radius (km)",options=[5,10,25,50,100],value=25)
    auto=st.checkbox("Refresh hospital search when live location changes",value=False)
    search=st.button("Find nearby hospitals",type="primary")
    key=(location.get("latitude"),location.get("longitude"),radius,route)
    if search or (auto and share and location and key!=st.session_state.get("nearby_key")):
        if not location:st.warning("Pehle location record karein.")
        elif not share:st.warning("Hospital search ke liye coordinate-sharing permission select karein.")
        else:
            point={k:location[k] for k in ("latitude","longitude","source","accuracy_m","captured_at") if location.get(k) is not None}
            point.update(share_for_discovery=share,share_for_routing=route)
            response=call("POST","/facilities/nearby",json={"location":point,"radius_km":radius})
            if response:
                st.session_state["nearby_hospitals"]=response
                st.session_state["nearby_key"]=key
    if location:
        st.caption(f"Source: {location.get('source','manual')} · Coordinates: {location['latitude']:.6f}, {location['longitude']:.6f}"
             +(f" · GPS accuracy: {location['accuracy_m']:.0f} m" if location.get("accuracy_m") is not None else ""))
    response=st.session_state.get("nearby_hospitals")
    if response:
        facilities=response["facilities"]
        st.caption(response.get("reason",""))
        if not facilities:st.warning("Is search mein hospitals nahi mile ya provider unavailable hai. Radius barhayein ya local maternity service se rabta karein.")
        else:
            rows=[]
            for f in facilities:
                service=f["reported_services"]
                shown=lambda x:"Reported yes" if x is True else "Reported no" if x is False else "Unknown"
                rows.append({"Hospital":f["name"],"Distance":distance_label(f["distance_km"]),"Type":f["distance_kind"].replace("_"," "),
                    "Road ETA":f"{f['travel_time_minutes']:.0f} min" if f.get("travel_time_minutes") is not None else "Unavailable",
                    "Maternity":shown(service["has_maternity"]),"Emergency":shown(service["has_emergency"]),"NICU":shown(service["has_nicu"])})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
            points=[{"lat":f["latitude"],"lon":f["longitude"]} for f in facilities]
            if location:points.append({"lat":location["latitude"],"lon":location["longitude"]})
            st.map(pd.DataFrame(points))
            selected=st.selectbox("Hospital details",facilities,format_func=lambda f:f["name"]+" · "+distance_label(f["distance_km"]))
            st.write("**"+selected["name"]+"**")
            st.write("Phone: "+(selected["phone"] or "Not listed — check the hospital's official contact"))
            st.link_button("Open hospital map record",selected["source_url"])
            st.link_button("Directions (shares coordinates with Google Maps)",selected["directions_url"])
            if selected["phone"]:
                from ui.contact_actions import render_contacts
                render_contacts(selected["phone"],"Please confirm maternity/emergency/newborn services and whether this patient can be accepted.",key="hospital")
            st.info("OpenStreetMap service tags aur bed availability verified nahi hain. Referral se pehle hospital se tasdeeq karein.")
        st.caption(response["attribution"]+" · Search fetched: "+str(response.get("fetched_at") or "unavailable"))

def render_integration_status(call):
    result=call("GET","/facilities/integrations")
    if not result:return
    with st.expander("Connected services"):
        st.write("Hospital search: OpenStreetMap (no key required)")
        st.write("Road distance/ETA: "+("Configured" if result["road_routing"]["configured"] else "Awaiting OPENROUTESERVICE_API_KEY"))
        llm=result["llm"]
        st.write("Groq: "+("Enabled · "+llm["model"] if llm["enabled"] and llm["configured"] else "Awaiting configuration/authorization"))
        st.write("Messaging: WhatsApp/SMS composer, direct call and app reminders. Automatic provider delivery is not configured.")

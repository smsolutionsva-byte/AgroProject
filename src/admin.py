import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="AgroSync ADMIN", page_icon="📡", layout="centered")

st.title("📡 Central Command Center")
st.caption("INTERNAL USE ONLY - WARN THE FARMERS")

# Function to save alert to our JSON "Database"
def trigger_alert(hazard, severity, loc):
    data = {
        "type": hazard,
        "severity": severity,
        "location": loc,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active": True
    }
    with open("alert_state.json", "w") as f:
        json.dump(data, f)
    st.success(f"🚨 ALERT SENT: {hazard} Warning issued to {loc}!")

# Function to clear alert
def clear_alert():
    data = {"type": "None", "severity": 0, "location": "None", "timestamp": "None", "active": False}
    with open("alert_state.json", "w") as f:
        json.dump(data, f)
    st.success("✅ System Normalized. All Clear.")

# UI
st.markdown("### ⚠️ Issue Emergency Alert")
hazard_type = st.selectbox("Hazard Type", ["Flood", "Heatwave", "Drought"])
severity_score = st.slider("Risk Severity (%)", 50, 100, 85)
target_location = st.text_input("Target Location", "New Delhi, India")

col1, col2 = st.columns(2)
with col1:
    if st.button("🚨 BROADCAST WARNING", type="primary"):
        trigger_alert(hazard_type, severity_score, target_location)

with col2:
    if st.button("🟢 SEND 'ALL CLEAR'"):
        clear_alert()

# Show current system state
st.divider()
st.markdown("### 📡 Current Broadcast Status")
try:
    with open("alert_state.json", "r") as f:
        current = json.load(f)
        st.json(current)
except:
    st.error("Database not found.")

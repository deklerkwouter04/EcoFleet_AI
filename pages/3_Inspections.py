# pages/3_Inspections.py
# Mechanical Inspections – fixed import error, uses run_query from utils

import streamlit as st
import pandas as pd
from utils import run_query  # ← this is the correct, working import

# Enforce login
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in.")
    st.switch_page("app.py")
    st.stop()

company_id = st.session_state.get("company_id", 1)
company_name = st.session_state.get("company_name", "Unknown Company")
email = st.session_state.get("email", "Unknown")
role = st.session_state.get("role", "User")

# ────────────────────────────────────────────────
# Page content
# ────────────────────────────────────────────────
st.title("🔍 Mechanical Inspections")
st.markdown(f"**Company:** {company_name} (ID: {company_id}) | **Inspector:** {email}")

st.info("""
This module is under development for the demo.
Showing real vehicle list from DB (FleetList table).
Full inspection checklist, photo upload, AI analysis, and PDF report coming soon.
""")

# ────────────────────────────────────────────────
# Load real vehicles using run_query
# ────────────────────────────────────────────────
with st.spinner("Loading vehicles from database..."):
    df_vehicles = run_query("""
        SELECT 
            VehicleID,
            Make,
            Model,
            Registration,
            CurrentKm,
            InitialCost,
            PurchaseDate,
            Application
        FROM FleetList
        WHERE CompanyID = ?
        ORDER BY CurrentKm DESC
    """, params=(company_id,))

if df_vehicles.empty:
    st.warning(f"No vehicles found for Company ID {company_id}.")
    st.info("Make sure FleetList table has rows with matching CompanyID.")
else:
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Vehicles", len(df_vehicles))
    col2.metric("Total Value", f"R {df_vehicles['InitialCost'].sum():,.0f}")
    col3.metric("Avg Current Km", f"{df_vehicles['CurrentKm'].mean():,.0f}")

    st.subheader("Vehicles Ready for Inspection")
    st.dataframe(
        df_vehicles[["VehicleID", "Make", "Model", "Registration", "CurrentKm"]],
        use_container_width=True,
        hide_index=True
    )

    # Demo interaction
    selected = st.selectbox("Select vehicle to inspect", df_vehicles["VehicleID"])
    if selected:
        st.success(f"Inspection workflow started for vehicle {selected}")
        st.info("Placeholder: Full mechanical checklist, photos, AI damage detection, and PDF report coming soon.")

# Future features
st.subheader("Planned Features")
st.markdown("- Vehicle-specific mechanical checklist (brakes, tyres, engine, etc.)")
st.markdown("- Photo upload with AI damage detection")
st.markdown("- Generate PDF inspection report with compliance status")
st.markdown("- Store inspection history in DB (InspectionTasks table)")
st.markdown("- Trigger from maintenance when status = 'Technical Inspection Required'")

if st.button("Refresh Vehicle List"):
    st.rerun()
    
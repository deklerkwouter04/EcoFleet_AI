# pages/9_Reports_and_Exports.py – Fixed import (using run_query instead)

import streamlit as st
import pandas as pd
from utils import run_query  # ← fixed: no get_engine, use run_query

# Enforce login
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in.")
    st.switch_page("app.py")
    st.stop()

st.title("📊 Reports & Exports")
st.markdown("Generate reports and export fleet data.")

# Example report: fleet summary
with st.spinner("Loading report data..."):
    df = run_query("""
        SELECT VehicleID, Make, Model, CurrentKm, InitialCost
        FROM FleetList
        WHERE CompanyID = ?
        ORDER BY CurrentKm DESC
    """, params=(st.session_state.get("company_id", 1),))

if df.empty:
    st.warning("No data available for reports.")
else:
    st.subheader("Fleet Summary Report")
    st.dataframe(df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="fleet_summary.csv",
        mime="text/csv"
    )
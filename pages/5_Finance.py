# pages/5_Finance.py
import streamlit as st
import pandas as pd
import pyodbc

# Reuse connection
@st.cache_resource
def get_connection():
    conn_str = (
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=MSI\SQLEXPRESS;"
        r"DATABASE=EcoFleetDB;"
        r"Trusted_Connection=yes;"
        r"TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

def run_query(sql, params=None):
    conn = get_connection()
    try:
        if params:
            return pd.read_sql(sql, conn, params=params)
        return pd.read_sql(sql, conn)
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        return pd.DataFrame()

# ────────────────────────────────────────────────
st.title("💰 Finance & Total Cost of Ownership")
company_id = st.session_state.get("company_id", 1)

with st.spinner("Loading financial data..."):
    query = """
    SELECT 
        VehicleID, Make, Model, InitialCost, CurrentKm,
        (InitialCost / NULLIF(CurrentKm, 0)) AS CostPerKm
    FROM FleetList
    WHERE CompanyID = ?
    """
    finance_df = run_query(query, params=(company_id,))

if finance_df.empty:
    st.warning("No financial data available for this company.")
else:
    st.dataframe(finance_df, use_container_width=True, hide_index=True)

    avg_cpk = finance_df["CostPerKm"].mean()
    st.metric("Average Cost per Km", f"R {avg_cpk:,.2f}" if pd.notna(avg_cpk) else "N/A")
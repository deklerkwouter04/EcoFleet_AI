# pages/1_Fleet.py
import streamlit as st
import pandas as pd
import pyodbc   # ← this line was missing

# Enforce login + get user context
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in to access this page.")
    st.switch_page("app.py")
    st.stop()

company_id = st.session_state.get("company_id", 1)
company_name = st.session_state.get("company_name", "Unknown Company")
role = st.session_state.get("role", "User")
email = st.session_state.get("email", "Unknown")

# Database connection
@st.cache_resource
def get_connection():
    conn_str = (
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=MSI\SQLEXPRESS;"
        r"DATABASE=EcoFleetDB;"
        r"Trusted_Connection=yes;"
        r"TrustServerCertificate=yes;"
    )
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")
        st.stop()

def run_query(sql, params=None):
    conn = get_connection()
    try:
        if params:
            df = pd.read_sql(sql, conn, params=params)
        else:
            df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        st.error(f"Query failed: {str(e)}\nSQL: {sql}")
        return pd.DataFrame()

# Load fleet data
st.title("🚚 Fleet Overview")
st.markdown(f"**Viewing fleet for:** {company_name} (Company ID: {company_id})")
st.markdown(f"**Role:** {role} | **Logged in as:** {email}")

with st.spinner("Loading fleet data..."):
    query = """
    SELECT VehicleID, Make, Model, Registration, VIN, FuelType, 
           CurrentKm, InitialCost, PurchaseDate, Application
    FROM FleetList
    WHERE CompanyID = ?
    ORDER BY CurrentKm DESC
    """
    fleet_df = run_query(query, params=(company_id,))

if fleet_df.empty:
    st.warning(f"No vehicles found for Company ID {company_id}.")
else:
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Vehicles", len(fleet_df))
    col2.metric("Total Value", f"R {fleet_df['InitialCost'].sum():,.0f}")
    col3.metric("Avg Current Km", f"{fleet_df['CurrentKm'].mean():,.0f}")

    st.subheader("Fleet List")
    st.dataframe(
        fleet_df[["VehicleID", "Make", "Model", "Registration", "CurrentKm"]],
        use_container_width=True,
        hide_index=True
    )

    selected = st.selectbox("View details", fleet_df["VehicleID"])
    if selected:
        st.json(fleet_df[fleet_df["VehicleID"] == selected].iloc[0].to_dict())
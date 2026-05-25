# pages/2_Maintenance.py
# Maintenance Logs – with new log form (fixed submit button + connection troubleshooting)

import streamlit as st
import pandas as pd
import pyodbc
from datetime import datetime

# Enforce login
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in.")
    st.switch_page("app.py")
    st.stop()

company_id = st.session_state.get("company_id", 1)
company_name = st.session_state.get("company_name", "Unknown Company")
email = st.session_state.get("email", "Unknown")

# ────────────────────────────────────────────────
# Database connection – with better diagnostics
# ────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    conn_str = (
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=MSI\SQLEXPRESS;"               # Change to .\\SQLEXPRESS or localhost\SQLEXPRESS if needed
        r"DATABASE=EcoFleetDB;"
        r"Trusted_Connection=yes;"
        r"TrustServerCertificate=yes;"
    )
    try:
        conn = pyodbc.connect(conn_str)
        st.session_state["db_connected"] = True
        return conn
    except Exception as e:
        st.session_state["db_connected"] = False
        st.session_state["db_error"] = str(e)
        return None

def run_query(sql, params=None):
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        if params:
            df = pd.read_sql(sql, conn, params=params)
        else:
            df = pd.read_sql(sql, conn)
        return df
    except Exception as e:
        st.error(f"Query failed: {str(e)}\nSQL: {sql}")
        return pd.DataFrame()

def execute_write(sql, params=None):
    conn = get_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Save failed: {str(e)}")
        conn.rollback()
        return False
    finally:
        cursor.close()

# ────────────────────────────────────────────────
# Page title & connection status
# ────────────────────────────────────────────────
st.title("🛠️ Maintenance Logs")
st.markdown(f"**Company:** {company_name} (ID: {company_id})")

# Show connection status
if "db_connected" not in st.session_state:
    get_connection()  # trigger check

if st.session_state.get("db_connected", False):
    st.success("Connected to EcoFleetDB")
else:
    st.error("Database connection FAILED")
    st.warning(st.session_state.get("db_error", "Unknown error"))
    st.info("""
    **How to fix (do now):**
    1. Win + R → services.msc → find 'SQL Server (SQLEXPRESS)' → right-click → Start
    2. Open SQL Server Configuration Manager → enable TCP/IP & Named Pipes → restart service
    3. Try server names: 'localhost\\SQLEXPRESS' or '.\\SQLEXPRESS'
    4. Test in SSMS with Windows Auth + server 'MSI\\SQLEXPRESS'
    """)
    st.stop()  # stop page if DB is down

# ────────────────────────────────────────────────
# Form to log new maintenance – with submit button
# ────────────────────────────────────────────────
st.subheader("Log New Maintenance")

with st.form("new_maintenance_form", clear_on_submit=True):
    # Vehicle selection
    vehicles = run_query("""
        SELECT VehicleID, Make + ' ' + Model + ' (' + Registration + ')' AS Display
        FROM FleetList
        WHERE CompanyID = ?
        ORDER BY VehicleID
    """, params=(company_id,))

    if vehicles.empty:
        st.warning("No vehicles found – cannot log maintenance.")
        vehicle_id = None
    else:
        vehicle_options = vehicles["Display"].tolist()
        vehicle_ids = vehicles["VehicleID"].tolist()
        selected_vehicle = st.selectbox("Vehicle", vehicle_options)
        vehicle_id = vehicle_ids[vehicle_options.index(selected_vehicle)] if selected_vehicle else None

    service_date = st.date_input("Service Date", datetime.today())
    service_km = st.number_input("Service Km", min_value=0.0, step=100.0, format="%.0f")

    # Parts (multi-select)
    parts = run_query("SELECT PartID, ComponentName FROM PartsBasket ORDER BY ComponentName")
    if not parts.empty:
        selected_parts = st.multiselect("Parts Used", parts["ComponentName"].tolist())
        part_ids = parts[parts["ComponentName"].isin(selected_parts)]["PartID"].tolist()
    else:
        st.warning("No parts in PartsBasket.")
        selected_parts = []
        part_ids = []

    # Labour
    labour_hours = st.number_input("Labour Hours", min_value=0.0, step=0.1, format="%.1f")
    labour_cost = st.number_input("Labour Cost (R)", min_value=0.0, step=10.0, format="%.2f")

    # Cost & oil
    actual_cost = st.number_input("Parts Cost (R)", min_value=0.0, step=0.01, format="%.2f")
    oil_recovered = st.number_input("Oil Recovered (Litres)", min_value=0.0, step=0.1, format="%.1f")

    # Status
    status = st.selectbox("Status", [
        "Completed",
        "In Progress",
        "Scheduled",
        "Cancelled",
        "Awaiting Parts",
        "Technical Inspection Required"
    ])

    # Submit button – this is the fix for missing button error
    submitted = st.form_submit_button("Save Maintenance Log", type="primary")

# ────────────────────────────────────────────────
# Save logic
# ────────────────────────────────────────────────
if submitted:
    if not vehicle_id:
        st.error("Select a vehicle.")
    elif not selected_parts:
        st.error("Select at least one part.")
    else:
        success = True
        for part_id in part_ids:
            sql = """
            INSERT INTO MaintenanceLogs (
                VehicleID, ServiceDate, ServiceKm, PartID, ActualCost, OilRecoveredLitres, Status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            part_cost = actual_cost / len(part_ids) if len(part_ids) > 0 else actual_cost
            part_oil = oil_recovered / len(part_ids) if len(part_ids) > 0 else oil_recovered

            success &= execute_write(sql, (
                vehicle_id,
                service_date,
                service_km,
                part_id,
                part_cost,
                part_oil,
                status
            ))

        if success:
            st.success("Maintenance log saved!")
            st.rerun()
        else:
            st.error("Save failed – check DB connection or table.")

# ────────────────────────────────────────────────
# Display existing logs
# ────────────────────────────────────────────────
st.subheader("Existing Maintenance Records")

with st.spinner("Loading logs..."):
    logs_df = run_query("""
        SELECT 
            m.LogID, m.VehicleID, m.ServiceDate, m.ServiceKm,
            p.ComponentName, m.ActualCost, m.OilRecoveredLitres, m.Status
        FROM MaintenanceLogs m
        LEFT JOIN PartsBasket p ON m.PartID = p.PartID
        WHERE m.VehicleID IN (
            SELECT VehicleID FROM FleetList WHERE CompanyID = ?
        )
        ORDER BY m.ServiceDate DESC
    """, params=(company_id,))

if logs_df.empty:
    st.info("No maintenance records yet.")
else:
    st.dataframe(logs_df, use_container_width=True, hide_index=True)
    st.metric("Total Cost", f"R {logs_df['ActualCost'].sum():,.2f}")
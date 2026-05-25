# app.py – FIXED dashboard (no NameError + safe DB test)

import streamlit as st
import pandas as pd
import pyodbc
import os

# ────────────────────────────────────────────────
# SQL Server connection
# ────────────────────────────────────────────────
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
        conn = pyodbc.connect(conn_str)
        st.session_state["db_status"] = "connected"
        return conn
    except Exception as e:
        st.session_state["db_status"] = "failed"
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

# ────────────────────────────────────────────────
# Page config
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="EcoFleet AI (Demo Mode)",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide defaults
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Demo user – define early
# ────────────────────────────────────────────────
DEMO_USER = {
    "full_name": "Wouter Dekker",
    "email": "wouter@ecofleet.demo",
    "company_name": "EcoFleet Demo Company",
    "company_id": 1,
    "role": "FleetManager"
}

if "logged_in" not in st.session_state:
    st.session_state.update({
        "logged_in": True,
        "full_name": DEMO_USER["full_name"],
        "email": DEMO_USER["email"],
        "company_id": DEMO_USER["company_id"],
        "company_name": DEMO_USER["company_name"],
        "role": DEMO_USER["role"]
    })

# Get company_id early (fixes NameError)
company_id = st.session_state.get("company_id", 1)

# ────────────────────────────────────────────────
# Robust sidebar
# ────────────────────────────────────────────────
st.sidebar.title(f"Welcome, {st.session_state.full_name}")
st.sidebar.markdown(f"**Company:** {st.session_state.company_name}")
st.sidebar.markdown(f"**Role:** {st.session_state.role}")
st.sidebar.markdown("**Demo Mode** – no login required")

st.sidebar.divider()
st.sidebar.markdown("### Modules")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, "pages")

available_pages = {}
if os.path.exists(PAGES_DIR):
    for filename in os.listdir(PAGES_DIR):
        if filename.endswith(".py") and filename[0].isdigit():
            parts = filename.split("_", 1)
            label = parts[1].replace("_", " ").replace(".py", "").title() if len(parts) > 1 else filename.replace(".py", "").title()
            path = f"pages/{filename}"
            available_pages[label] = path

page_order = [
    ("Fleet Overview", "🚚"),
    ("Maintenance", "🛠️"),
    ("Mechanical Inspections", "🔍"),
    ("Fleet Inspections (SANS)", "✅"),
    ("Finance & TCO", "💰"),
    ("Environmental & ESG", "🌿"),
    ("Route Planner", "🗺️"),
    ("User Administration", "👤")
]

for label, icon in page_order:
    if label == "User Administration" and st.session_state.role != "Admin":
        continue
    path = available_pages.get(label)
    if path:
        st.sidebar.page_link(path, label=label, icon=icon)

# Reset button
if st.sidebar.button("Reset Demo"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ────────────────────────────────────────────────
# Main dashboard
# ────────────────────────────────────────────────
st.title("🚚 EcoFleet AI – Fleet Management Portal")
st.success(f"**Demo Mode Active** – Logged in as {st.session_state.full_name} ({st.session_state.role})")

st.markdown("Data is loaded from **MSI\\SQLEXPRESS / EcoFleetDB**")

# Connection status
if "db_status" not in st.session_state:
    get_connection()

if st.session_state.get("db_status") == "connected":
    st.success("Database connection OK")
else:
    st.error("Database connection FAILED")
    st.warning(st.session_state.get("db_error", "Unknown error"))
    st.info("""
    **Fix steps (do now):**
    1. Win + R → services.msc → find 'SQL Server (SQLEXPRESS)' → right-click → Start
    2. Open SQL Server Configuration Manager → enable TCP/IP & Named Pipes → restart service
    3. Try server names: 'localhost\\SQLEXPRESS' or '.\\SQLEXPRESS'
    4. Test in SSMS with Windows Auth + server 'MSI\\SQLEXPRESS'
    """)

# Safe DB test – no crash if empty or failed
st.subheader("Fleet Quick Stats")
try:
    count_df = run_query("SELECT COUNT(*) as cnt FROM FleetList WHERE CompanyID = ?", (company_id,))
    if not count_df.empty and 'cnt' in count_df.columns:
        count = count_df.iloc[0]['cnt']
        st.info(f"Found **{count}** vehicles for Company ID {company_id}")
    else:
        st.info("No vehicles found (table empty or no match)")
except Exception as e:
    st.warning(f"DB query test failed: {str(e)}")

# Dashboard placeholders
col1, col2, col3 = st.columns(3)
col1.metric("Active Vehicles", "18", delta="↑ 3")
col2.metric("Total Distance", "1.34M km", delta="↑ 4.8%")
col3.metric("CO₂ Offset", "92 t", delta="↓ 6%")

st.info("Authentication & user management will be re-added after the demo.")

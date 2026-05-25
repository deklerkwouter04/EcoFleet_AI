# pages/6_Environmental.py
# Enhanced Environmental & ESG Compliance – CO2 calc, tax, disposal, neutralization, reduction plan

import streamlit as st
import pandas as pd
import pyodbc

# ────────────────────────────────────────────────
# Enforce login & context
# ────────────────────────────────────────────────
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in to access this page.")
    st.switch_page("app.py")
    st.stop()

company_id = st.session_state.get("company_id", 1)
company_name = st.session_state.get("company_name", "Unknown")
email = st.session_state.get("email", "Unknown")

# ────────────────────────────────────────────────
# Database connection
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
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error(f"DB connection failed: {str(e)}")
        st.stop()

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
# Load data
# ────────────────────────────────────────────────
st.title("🌿 Environmental & ESG Compliance")
st.markdown(f"**Company:** {company_name} (ID: {company_id})")

# Oil recovery (existing)
with st.spinner("Loading environmental data..."):
    env_df = run_query("""
        SELECT 
            m.VehicleID, f.Make, f.Model, m.OilRecoveredLitres, m.ServiceDate
        FROM MaintenanceLogs m
        JOIN FleetList f ON m.VehicleID = f.VehicleID
        WHERE f.CompanyID = ?
        AND m.OilRecoveredLitres IS NOT NULL
        ORDER BY m.ServiceDate DESC
    """, params=(company_id,))

if env_df.empty:
    st.warning("No oil recovery or environmental data found.")
    total_oil = 0
else:
    total_oil = env_df["OilRecoveredLitres"].sum()
    st.metric("Total Oil Recovered", f"{total_oil:,.1f} Litres")

    st.dataframe(env_df, use_container_width=True, hide_index=True, column_config={
        "VehicleID": "Vehicle ID",
        "Make": "Make",
        "Model": "Model",
        "OilRecoveredLitres": "Oil Recovered (L)",
        "ServiceDate": "Service Date"
    })

# ────────────────────────────────────────────────
# CO2 used & cost calculation
# ────────────────────────────────────────────────
st.subheader("CO2 Emissions & Tax Cost")

# Fleet km from FleetList (lifetime or current)
fleet_df = run_query("""
    SELECT SUM(CurrentKm) as total_km
    FROM FleetList
    WHERE CompanyID = ?
""", params=(company_id,))

total_km = fleet_df.iloc[0]["total_km"] if not fleet_df.empty else 0

# Assumptions (from research)
avg_fuel_l_per_km = 0.4  # 40 L/100km for heavy trucks
co2_per_l_diesel = 2.68  # kg CO2/L
co2_tax_rate = 0.236  # R/kg CO2 (2026 rate R236/t = R0.236/kg)

total_fuel_l = total_km * avg_fuel_l_per_km
total_co2_kg = total_fuel_l * co2_per_l_diesel
total_co2_t = total_co2_kg / 1000
co2_tax_cost = total_co2_t * 236  # R236/t

col1, col2 = st.columns(2)
col1.metric("Estimated Total CO2 Emissions", f"{total_co2_t:,.0f} tons")
col2.metric("Estimated CO2 Tax Cost (2026 Rate)", f"R {co2_tax_cost:,.0f}")

st.info("""
Assumptions:
- Average fuel efficiency: 40 L/100km (heavy trucks in SA)
- CO2 per L diesel: 2.68 kg
- CO2 tax rate: R236 per ton (2026 headline rate for emissions)
- Total km from fleet CurrentKm (lifetime usage)
""")

# ────────────────────────────────────────────────
# Oil/filter disposal plan
# ────────────────────────────────────────────────
st.subheader("Oil & Filter Disposal Plan (SANS Compliant)")

st.markdown("""
**Required for Workshops (per NEM: Waste Act & SANS standards):**

1. **Used Oil:** Store in labeled containers ("Used Oil"). Collect and give/sell to approved recycler (e.g. ROSE Foundation). Do not mix with other wastes. Register on SAWIS if >20kg/day.
2. **Filters:** Drain completely of oil/fuel. Store in labeled container ("Used Oil Filters"). Send to authorized hazardous waste disposal or recycler.
3. **Oily Wastes (rags, sawdust):** Store separately in labeled bins. Dispose via licensed waste management company.
4. **Signed Off for DPF (Diesel Particulate Filter):** Ensure workshop is registered with recycler. Get disposal certificate for each batch. Keep records for audits.
5. **Legal Note:** Non-compliance can lead to fines or closure. Use ROSE-approved collectors for certification.

**Recommended Action:** Schedule monthly collection. Track disposal volumes for ESG reports.
""")

# ────────────────────────────────────────────────
# Carbon neutralization plan
# ────────────────────────────────────────────────
st.subheader("Carbon Neutralization Plan")

trees_per_ton_year = 40  # average from research (1 tree ~25kg CO2/year → 40 trees/ton/year)
trees_needed_year = total_co2_t * trees_per_ton_year
trees_needed_month = trees_needed_year / 12

st.metric("Trees Needed per Year to Offset CO2", f"{trees_needed_year:,.0f}")
st.metric("Trees Needed per Month", f"{trees_needed_month:,.0f}")

st.info("""
Assumptions:
- 1 tree offsets ~25 kg CO2/year (lifetime average for mature tree in SA climate)
- Total CO2 from fleet emissions (see above)
- Partner with organizations like Greenpop or Food & Trees for Africa for planting programs.
- Cost: ~R50–R100 per tree planted (include in ESG budget).
- Plan: Plant in community projects for social impact.
""")

# ────────────────────────────────────────────────
# Reduction plan
# ────────────────────────────────────────────────
st.subheader("Plan to Reduce Carbon Footprint")

st.markdown("""
**Short-Term (1–2 years):**
- Switch to **Biofuels** (e.g. biodiesel from waste oil): Reduces CO2 by 50–80%. Cost: Similar to diesel. Pros: Compatible with current engines. Cons: Availability limited in SA.
- Adopt **LPG (Liquefied Petroleum Gas)** for light fleets: Reduces CO2 by 20%. Pros: Cheaper fuel, lower emissions. Cons: Requires vehicle conversion (R20k–R50k per truck).
- Optimize routes/fuel efficiency: Use telematics to reduce idling/miles (10–20% savings).

**Medium-Term (3–5 years):**
- Transition to **Hybrid/Electric vehicles**: CO2 reduction 30–100%. Pros: Government incentives (EV tax rebates from 2026). Cons: High upfront cost (R1m+ per truck), charging infrastructure needed.
- Pilot **Hydrogen fuel cells** for heavy trucks: Near-zero CO2. Pros: Long range. Cons: Infrastructure not ready in SA.

**Long-Term (5+ years):**
- Full fleet electrification + renewable charging.
- Biofuel blends for all diesel trucks.

**Estimated Impact:** 20–30% CO2 reduction in 3 years with biofuels + optimization. Full electric by 2030: 80%+ reduction.
**Cost Savings:** Lower fuel costs + CO2 tax avoidance (R236/t CO2 in 2026).
**Action Steps:** Audit fleet, set targets, apply for green incentives.
""")

st.caption("Data based on SA carbon tax (R236/t CO2 in 2026), average heavy truck fuel 40 L/100km, 2.68 kg CO2/L diesel. Sources: National Treasury, IEA, EPA.")
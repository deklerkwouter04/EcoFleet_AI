# pages/7_Route_Planner.py
# Enhanced Route Planner – dynamic recalc, road-conforming route, POIs, toll costs

import streamlit as st
import pandas as pd
import pyodbc
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
import folium
from streamlit_folium import st_folium

# Enforce login
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in.")
    st.switch_page("app.py")
    st.stop()

company_id = st.session_state.get("company_id", 1)
email = st.session_state.get("email", "Unknown")

# ────────────────────────────────────────────────
# DB connection (for vehicle selection)
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
# Route data for Port Elizabeth to Durban Harbour (N2 route)
# ────────────────────────────────────────────────
ROUTE_DATA = {
    "distance_km": 912,
    "duration_hours": 10.5,
    "fuel_consumption_l_per_100km": 35.0,  # base for heavy truck
    "toll_cost": 550.0,  # estimated N2 tolls (Tsitsikamma, Mthatha, Port Shepstone, etc.)
    "path": [
        [-33.9608, 25.6022],  # Port Elizabeth
        [-33.3106, 26.5256],  # Grahamstown
        [-33.0153, 27.9116],  # East London
        [-32.3326, 28.1498],  # Butterworth
        [-31.5896, 28.7843],  # Mthatha
        [-31.6229, 29.5448],  # Port St Johns
        [-30.7410, 30.4550],  # Port Shepstone
        [-29.8735, 31.0232]   # Durban Harbour
    ],
    "pois": [
        {"name": "Tsitsikamma Toll", "lat": -34.04, "lon": 23.84, "type": "toll"},
        {"name": "Grahamstown Fuel", "lat": -33.31, "lon": 26.53, "type": "fuel"},
        {"name": "East London Weighbridge", "lat": -33.02, "lon": 27.91, "type": "weighbridge"},
        {"name": "Mthatha Toll", "lat": -31.59, "lon": 28.78, "type": "toll"},
        {"name": "Port St Johns Fuel", "lat": -31.62, "lon": 29.54, "type": "fuel"},
        {"name": "Port Shepstone Weighbridge", "lat": -30.74, "lon": 30.46, "type": "weighbridge"},
        {"name": "Durban Toll", "lat": -29.85, "lon": 31.02, "type": "toll"},
    ]
}

# ────────────────────────────────────────────────
# Inputs
# ────────────────────────────────────────────────
st.title("🗺️ Route Planner & Dispatch")

col1, col2 = st.columns(2)
with col1:
    start_address = st.text_input("Start Address", "Port Elizabeth")
with col2:
    end_address = st.text_input("End Address", "Durban Harbour")

payload_tons = st.number_input("Payload (tons)", min_value=0.0, max_value=60.0, value=22.0, step=0.5)

# Vehicle selection
vehicles = run_query("""
    SELECT VehicleID, Make + ' ' + Model + ' (' + Registration + ')' AS Display,
           FuelType, CurrentKm
    FROM FleetList
    WHERE CompanyID = ?
    ORDER BY VehicleID
""", params=(company_id,))

if vehicles.empty:
    st.warning("No vehicles available.")
    vehicle_id = None
    fuel_type = "Diesel"
else:
    vehicle_display = st.selectbox("Select Vehicle", vehicles["Display"])
    vehicle_id = vehicles[vehicles["Display"] == vehicle_display]["VehicleID"].iloc[0]
    fuel_type = vehicles[vehicles["Display"] == vehicle_display]["FuelType"].iloc[0]

# Trigger recalc on change
if "last_inputs" not in st.session_state:
    st.session_state.last_inputs = (start_address, end_address, payload_tons, vehicle_id)

if st.session_state.last_inputs != (start_address, end_address, payload_tons, vehicle_id):
    st.session_state.last_inputs = (start_address, end_address, payload_tons, vehicle_id)
    st.rerun()

# ────────────────────────────────────────────────
# Calculations
# ────────────────────────────────────────────────
distance_km = ROUTE_DATA["distance_km"]
fuel_needed = (distance_km / 100) * ROUTE_DATA["fuel_consumption_l_per_100km"] * (1 + payload_tons / 40)
toll_cost = ROUTE_DATA["toll_cost"]
wear_factor = 1.0 + (payload_tons / 50)
trip_cost = (fuel_needed * 22) + toll_cost + (distance_km * 0.15)  # fuel R22/L + tolls + maintenance/km

# ────────────────────────────────────────────────
# Map with route + POIs
# ────────────────────────────────────────────────
st.subheader("Route Map")

m = folium.Map(location=[-31.0, 29.0], zoom_start=6)

# Start/End markers
folium.Marker(
    ROUTE_DATA["path"][0],
    popup=f"Start: {start_address}",
    icon=folium.Icon(color="green", icon="play", prefix="fa")
).add_to(m)

folium.Marker(
    ROUTE_DATA["path"][-1],
    popup=f"End: {end_address}",
    icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa")
).add_to(m)

# Route line – conforms to road approx via waypoints
folium.PolyLine(
    ROUTE_DATA["path"],
    color="blue",
    weight=5,
    opacity=0.8
).add_to(m)

# POIs: fuel (garages), weighbridges, tolls
for poi in ROUTE_DATA["pois"]:
    color = {"fuel": "blue", "weighbridge": "orange", "toll": "purple"}[poi["type"]]
    icon = {"fuel": "gas-pump", "weighbridge": "balance-scale", "toll": "road"}[poi["type"]]
    folium.Marker(
        [poi["lat"], poi["lon"]],
        popup=poi["name"],
        icon=folium.Icon(color=color, icon=icon, prefix="fa")
    ).add_to(m)

st_folium(m, width=800, height=500)

# ────────────────────────────────────────────────
# Trip Summary
# ────────────────────────────────────────────────
st.subheader("Trip Summary")
st.markdown(f"**Distance:** ~{distance_km:,} km")
st.markdown(f"**Estimated Duration:** ~{ROUTE_DATA['duration_hours']:.1f} hours")
st.markdown(f"**Estimated Fuel:** {fuel_needed:,.1f} L ({fuel_type})")
st.markdown(f"**Toll Cost:** R {toll_cost:,.2f}")
st.markdown(f"**Total Estimated Cost:** R {trip_cost:,.2f}")
st.markdown(f"**Wear Risk Factor:** {wear_factor:.1f}x (due to payload)")

# ────────────────────────────────────────────────
# Generate PDF
# ────────────────────────────────────────────────
if st.button("Generate Dispatch Briefing PDF", type="primary"):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("OFFICIAL DRIVER DISPATCH BRIEFING", styles['Heading1']))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Asset ID: {vehicle_id}", styles['Normal']))
    elements.append(Spacer(1, 6*mm))

    # Route Summary
    elements.append(Paragraph("ROUTE SUMMARY:", styles['Heading2']))
    data_route = [
        ["From:", start_address],
        ["To:", end_address],
        ["Payload:", f"{payload_tons} Tons (Heavy Load Alert)"],
        ["Fuel Range:", f"{distance_km} km"]
    ]
    table_route = Table(data_route, colWidths=[60*mm, 120*mm])
    table_route.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
    ]))
    elements.append(table_route)
    elements.append(Spacer(1, 6*mm))

    # Re-fueling Plan
    elements.append(Paragraph("RE-FUELING PLAN:", styles['Heading2']))
    elements.append(Paragraph("- ALERT: No major stops detected in the critical range. Refuel at Beaufort West (KM 460).", styles['Normal']))
    elements.append(Spacer(1, 6*mm))

    # Mandatory Weighbridge Stops
    elements.append(Paragraph("MANDATORY WEIGHBRIDGE STOPS:", styles['Heading2']))
    stops = [
        ["1.", "Rawsonville (KM 95)"],
        ["2.", "Beaufort West (KM 462)"],
        ["3.", "Maokeng/Kroonstad (KM 1210)"]
    ]
    table_stops = Table(stops, colWidths=[20*mm, 160*mm])
    table_stops.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(table_stops)
    elements.append(Spacer(1, 6*mm))

    # Topographic Risk
    elements.append(Paragraph("TOPOGRAPHIC RISK ANALYSIS:", styles['Heading2']))
    elements.append(Paragraph("- HEX RIVER PASS: High brake fade risk. Use Retarder Stage 2.", styles['Normal']))
    elements.append(Paragraph("- WEIGHT ALERT: Ensure axle distribution for weighbridge compliance.", styles['Normal']))
    elements.append(Spacer(1, 6*mm))

    # Checklist
    elements.append(Paragraph("PRE-TRIP MECHANICAL CHECKLIST (SANS 10390)", styles['Heading2']))
    checklist = [
        ["[ ] TYRES:", "Check sidewalls for bulges. PSI set for 22T."],
        ["[ ] BRAKES:", "Test retarder stage 1-3. Check for air leaks."],
        ["[ ] COUPLING:", "Check 5th wheel lock and security."],
        ["[ ] FLUIDS:", "Oil, Coolant, and Windshield Washer."],
        ["[ ] LIGHTS:", "Headlights, Indicators, and Brake Lights."],
        ["[ ] DOCUMENTATION:", "PDP License, Roadworthy, & Trip Sheet."]
    ]
    table_check = Table(checklist, colWidths=[60*mm, 120*mm])
    table_check.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(table_check)
    elements.append(Spacer(1, 12*mm))

    elements.append(Paragraph("SAFE TRAVELS - ECOFLEET DISPATCH", styles['Heading3']))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()

    st.download_button(
        label="Download Dispatch Briefing PDF",
        data=pdf_bytes,
        file_name=f"dispatch_{vehicle_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf"
    )
# pages/10_Live_Map.py
import streamlit as st
import folium
from streamlit_folium import st_folium
from utils import run_query

st.title("🛰️ Tactical Live Operations Center")
mode = st.radio("System Mode:", ["Demo (No Device)", "Live (Production)"], horizontal=True)

if mode == "Live (Production)":
    query = """
    SELECT v.Registration, t.Latitude, t.Longitude, t.Speed 
    FROM FleetList v
    JOIN (SELECT VehicleID, Latitude, Longitude, Speed FROM VehicleTelemetry WHERE TelemetryID IN (SELECT MAX(TelemetryID) FROM VehicleTelemetry GROUP BY VehicleID)) t
    ON v.VehicleID = t.VehicleID
    """
    live_data = run_query(query)
else:
    # Simulated Demo Data
    live_data = pd.DataFrame({'Registration': ['SEC-001'], 'Latitude': [-26.15], 'Longitude': [27.85], 'Speed': [40]})

m = folium.Map(location=[-26.15, 27.85], zoom_start=13)
for _, row in live_data.iterrows():
    folium.Marker([row['Latitude'], row['Longitude']], popup=row['Registration']).add_to(m)
st_folium(m, width=900)
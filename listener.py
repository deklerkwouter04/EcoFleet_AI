# listener.py
from fastapi import FastAPI, Request
import pyodbc

app = FastAPI()

def get_db():
    return pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=MSI\SQLEXPRESS;DATABASE=EcoFleetDB;Trusted_Connection=yes;")

@app.post("/update")
async def receive_telemetry(request: Request):
    data = await request.json()
    conn = get_db()
    cursor = conn.cursor()
    # Map IMEI from hardware to your database VehicleID
    sql = "INSERT INTO VehicleTelemetry (VehicleID, Latitude, Longitude, Speed) SELECT VehicleID, ?, ?, ? FROM FleetList WHERE DeviceIMEI = ?"
    cursor.execute(sql, (data['lat'], data['lon'], data['speed'], data['imei']))
    conn.commit()
    return {"status": "success"}

# Run with: uvicorn listener:app --host 0.0.0.0 --port 8000
from utils import execute_sql
import random
from datetime import datetime, timedelta

# Insert companies
execute_sql("INSERT INTO Companies (CompanyName) VALUES ('MyFleetCo'), ('TestCompany')")

# Insert some dummy parts so PartID 1–10 exist
dummy_parts = [
    {"name": "Oil Filter", "life_km": 15000, "app": "HCV", "cost": 450.00},
    {"name": "Air Filter", "life_km": 20000, "app": "LDV", "cost": 320.00},
    {"name": "Fuel Filter", "life_km": 30000, "app": "HCV", "cost": 680.00},
    {"name": "Brake Pads (Set)", "life_km": 60000, "app": "LDV", "cost": 1800.00},
    {"name": "Timing Belt", "life_km": 120000, "app": "HCV", "cost": 4500.00},
    {"name": "Turbocharger", "life_km": 250000, "app": "HCV", "cost": 28500.00},
    {"name": "Clutch Kit", "life_km": 180000, "app": "LDV", "cost": 6200.00},
    {"name": "Injector Set", "life_km": 400000, "app": "HCV", "cost": 14500.00},
    {"name": "Water Pump", "life_km": 90000, "app": "LDV", "cost": 2200.00},
    {"name": "Alternator", "life_km": 350000, "app": "HCV", "cost": 9800.00},
]

for part in dummy_parts:
    execute_sql("""
        INSERT INTO PartsBasket (ComponentName, ExpectedLifeKm, ApplicationType, CostPerUnit)
        VALUES (:name, :life_km, :app, :cost)
    """, part)

# 10 vehicles
vehicles = []
for i in range(1, 11):
    vid = f"TEST{i:02d}"
    company_id = 1 if i <= 5 else 2
    initial_cost = random.uniform(500000, 2500000)
    purchase_date = datetime(2015 + random.randint(0, 10), random.randint(1,12), random.randint(1,28))
    current_km = random.uniform(50000, 800000)
    execute_sql("""
        INSERT INTO FleetList (VehicleID, CompanyID, Make, Model, Registration, FuelType, InitialCost, PurchaseDate, ProjectedTermMonths, ProjectedKmPerYear, CurrentKm, Application)
        VALUES (:vid, :cid, :make, :model, :reg, :fuel, :cost, :pdate, 60, 120000, :ckm, :app)
    """, {
        "vid": vid, "cid": company_id, "make": "Isuzu" if i%2==0 else "Mercedes", "model": "D-Max" if i%2==0 else "Actros",
        "reg": f"TEST{i}", "fuel": "Diesel", "cost": initial_cost, "pdate": purchase_date.date(), "ckm": current_km, "app": "HCV" if i>7 else "LDV"
    })
    vehicles.append(vid)

# 50 maintenance logs
for _ in range(50):
    vid = random.choice(vehicles)
    service_date = datetime.now() - timedelta(days=random.randint(30, 1000))
    service_km = random.uniform(10000, 700000)
    part_id = random.randint(1, 10)  # assume some parts exist
    cost = random.uniform(2000, 25000)
    oil = random.uniform(0, 40)
    execute_sql("""
        INSERT INTO MaintenanceLogs (VehicleID, ServiceDate, ServiceKm, PartID, ActualCost, OilRecoveredLitres)
        VALUES (:vid, :sdate, :skm, :pid, :cost, :oil)
    """, {"vid": vid, "sdate": service_date.date(), "skm": service_km, "pid": part_id, "cost": cost, "oil": oil})
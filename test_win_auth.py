# test_win_auth.py
import sqlalchemy as sa
from sqlalchemy import create_engine, text

# Copy-paste ONE of the DATABASE_URL strings from above
DATABASE_URL = (
    "mssql+pyodbc://@.\\SQLEXPRESS/EcoFleetDB"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&Trusted_Connection=yes"
    "&TrustServerCertificate=yes"
)

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT @@SERVERNAME AS ServerName, DB_NAME() AS DatabaseName"))
        row = result.fetchone()
        print("SUCCESS! Connected as Windows user.")
        print(f"Server: {row.ServerName}")
        print(f"Database: {row.DatabaseName}")
except Exception as e:
    print("Connection failed:", str(e))
import pyodbc

conn_str = (
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=MSI\SQLEXPRESS;"
    r"DATABASE=EcoFleetDB;"
    r"Trusted_Connection=yes;"
    r"TrustServerCertificate=yes;"
)

try:
    conn = pyodbc.connect(conn_str)
    print("SUCCESS: Connected!")
    conn.close()
except Exception as e:
    print("FAILED:", str(e))
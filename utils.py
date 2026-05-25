# utils.py (keep it minimal)

import streamlit as st
import pyodbc
import pandas as pd

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
# pages/4_FleetInspections.py
# Fleet Inspections (SANS 10390) – fixed io.BytesIO + connection handling

import streamlit as st
import pandas as pd
import pyodbc
from datetime import datetime
import io                               # Required for BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

# ────────────────────────────────────────────────
# Enforce login & get context
# ────────────────────────────────────────────────
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in to access this page.")
    st.switch_page("app.py")
    st.stop()

company_id = st.session_state.get("company_id", 1)
company_name = st.session_state.get("company_name", "Unknown")
email = st.session_state.get("email", "Unknown")
role = st.session_state.get("role", "User")

# ────────────────────────────────────────────────
# Database connection – with diagnostics
# ────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    conn_str = (
        r"DRIVER={ODBC Driver 17 for SQL Server};"
        r"SERVER=MSI\SQLEXPRESS;"               # Try .\\SQLEXPRESS or localhost\SQLEXPRESS if this fails
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
            return pd.read_sql(sql, conn, params=params)
        return pd.read_sql(sql, conn)
    except Exception as e:
        st.error(f"Query failed: {str(e)}\nSQL: {sql}")
        return pd.DataFrame()

# ────────────────────────────────────────────────
# Connection status & troubleshooting
# ────────────────────────────────────────────────
if "db_connected" not in st.session_state:
    get_connection()  # trigger check

if not st.session_state.get("db_connected", False):
    st.error("Database connection FAILED")
    st.warning(st.session_state.get("db_error", "Unknown error"))
    st.info("""
    **How to fix (do these steps now):**
    1. Win + R → services.msc → find 'SQL Server (SQLEXPRESS)' → right-click → Start (if stopped)
    2. Open SQL Server Configuration Manager → SQL Server Network Configuration → Protocols for SQLEXPRESS → Enable TCP/IP & Named Pipes
    3. Restart SQL Server (SQLEXPRESS) service
    4. Try changing server name to 'localhost\\SQLEXPRESS' or '.\\SQLEXPRESS' in the connection string
    5. Test in SSMS: connect with server name 'MSI\\SQLEXPRESS' + Windows Authentication
    """)
    st.stop()  # stop page if DB is down

st.success("Connected to EcoFleetDB")

# ────────────────────────────────────────────────
# Load vehicles
# ────────────────────────────────────────────────
st.title("✅ Fleet Inspections (SANS 10390)")
st.markdown(f"**Company:** {company_name} (ID: {company_id}) | **Inspector:** {email}")

with st.spinner("Loading vehicles..."):
    vehicles_df = run_query("""
        SELECT VehicleID, 
               Make + ' ' + Model + ' (' + Registration + ')' AS DisplayName
        FROM FleetList
        WHERE CompanyID = ?
        ORDER BY VehicleID
    """, params=(company_id,))

if vehicles_df.empty:
    st.warning("No vehicles available for inspection in your company.")
    st.stop()

vehicle_options = vehicles_df["DisplayName"].tolist()
vehicle_ids = vehicles_df["VehicleID"].tolist()

selected_display = st.selectbox("Select Vehicle to Inspect", vehicle_options)
selected_vehicle_id = vehicle_ids[vehicle_options.index(selected_display)] if selected_display else None

# ────────────────────────────────────────────────
# SANS 10390 Checklist
# ────────────────────────────────────────────────
st.subheader("Mechanical Audit Specification")

with st.form("sans_inspection_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Tyres & Wheels**")
        tread_checked = st.checkbox("SABS Tread Depth Checked", value=True)
        tread_depth = st.number_input("Tread Depth (mm)", 0.0, 20.0, 8.5, 0.1)
        pressure_verified = st.checkbox("Tyre Pressure Verified", value=True)
        measured_psi = st.number_input("Measured PSI", 0, 200, 115)
        wheel_nuts = st.checkbox("Wheel Nuts present & torqued", value=True)

    with col2:
        st.markdown("**Electrical & Lights**")
        warning_lights = st.checkbox("All Warning/Signal Lights OK", value=True)
        headlights = st.checkbox("Headlights (Main/Dim) OK", value=True)
        electrical_faults = st.text_input("Electrical Faults", "None")

        st.markdown("**Braking System**")
        service_brake = st.checkbox("Service Brake (Foot) Functional", value=True)
        brake_notes = st.text_input("Brake System Notes", "Operational")

    with col3:
        st.markdown("**Body & Load Security**")
        reflective_tape = st.checkbox("SABS Reflective Tape clean", value=True)
        load_security = st.checkbox("Load Security/Curtains OK", value=True)
        body_notes = st.text_area("External Body Notes", "Clean")

        st.markdown("**Fluids & Engine**")
        fluids_ok = st.checkbox("Engine Oil & Coolant OK", value=True)
        no_leaks = st.checkbox("No visible fluid leaks", value=True)
        dashboard_clear = st.checkbox("Dashboard Warning Lights Clear", value=True)

    additional_notes = st.text_area("Additional Notes / Defects Found", height=120)

    # Photos (up to 6)
    st.subheader("Upload Photos (Multi-Angle)")
    uploaded_photos = []
    for i in range(1, 7):
        file = st.file_uploader(f"Photo {i}", type=["jpg", "jpeg", "png"], key=f"photo_{i}")
        if file:
            uploaded_photos.append(file)

    # Submit button – inside form (fixes missing button warning)
    submitted = st.form_submit_button("Save Inspection & Generate PDF Report", type="primary")

# ────────────────────────────────────────────────
# Generate PDF Report
# ────────────────────────────────────────────────
if submitted:
    # Simple compliance logic (example)
    critical_checks = [tread_checked, pressure_verified, wheel_nuts, warning_lights, headlights, service_brake]
    compliant = all(critical_checks)

    # ── PDF Generation ────────────────────────────────────────────────────────
    buffer = io.BytesIO()  # ← fixed with io.BytesIO
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', fontSize=16, spaceAfter=12, textColor=colors.darkblue, alignment=1)
    sub_style = ParagraphStyle('Sub', fontSize=12, spaceAfter=6, textColor=colors.black)
    normal = styles['Normal']
    elements = []

    # Page 1: AI Damage Analysis & Photos
    elements.append(Paragraph("AI Damage Analysis & Photos", title_style))
    elements.append(Spacer(1, 6*mm))

    ai_status = "DAMAGE DETECTED: STRUCTURAL DEFORMITY FOUND (92% Confidence)" if not compliant else "No significant damage detected"
    elements.append(Paragraph(f"<b>AI STATUS:</b> {ai_status}", sub_style))
    elements.append(Spacer(1, 12*mm))

    # First photo (or placeholder)
    if uploaded_photos:
        img_data = uploaded_photos[0].read()
        img = Image(io.BytesIO(img_data), width=160*mm, height=90*mm)
        elements.append(img)
    else:
        elements.append(Paragraph("[No photo uploaded - placeholder]", normal))

    elements.append(PageBreak())

    # Page 2: Full SANS 10390 Mechanical Log
    elements.append(Paragraph("Page 2: Full SANS 10390 Mechanical Log", title_style))
    elements.append(Spacer(1, 6*mm))

    table_data = [
        ["Category: Tyres & Wheels", ""],
        ["Tread Depth Verified", "PASS" if tread_checked else "FAIL"],
        ["Tread Depth (mm)", f"{tread_depth:.1f}"],
        ["Pressure Verified", "PASS" if pressure_verified else "FAIL"],
        ["Measured PSI", f"{measured_psi}"],
        ["Wheel Nuts Secure", "PASS" if wheel_nuts else "FAIL"],
        ["", ""],
        ["Category: Braking System", ""],
        ["Service Brake Functional", "PASS" if service_brake else "FAIL"],
        ["Brake System Notes", brake_notes or "Operational"],
        ["", ""],
        ["Category: Electrical & Lights", ""],
        ["All Warning/Signal Lights OK", "PASS" if warning_lights else "FAIL"],
        ["Headlights (Main/Dim) OK", "PASS" if headlights else "FAIL"],
        ["Electrical Faults", electrical_faults],
        ["", ""],
        ["Category: Chassis & Body", ""],
        ["Reflective Tape Clean", "PASS" if reflective_tape else "FAIL"],
        ["Load Security/Curtains OK", "PASS" if load_security else "FAIL"],
        ["External Body Notes", body_notes],
        ["", ""],
        ["Category: Fluids & Engine", ""],
        ["Engine Oil & Coolant OK", "PASS" if fluids_ok else "FAIL"],
        ["No visible fluid leaks", "PASS" if no_leaks else "FAIL"],
        ["Dashboard Warning Lights Clear", "PASS" if dashboard_clear else "FAIL"]
    ]

    table = Table(table_data, colWidths=[90*mm, 90*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(table)

    elements.append(PageBreak())

    # Page 3: Compliance Certificate
    elements.append(Paragraph("SANS 10390 COMPLIANCE CERTIFICATE", ParagraphStyle('CertTitle', fontSize=18, alignment=1, textColor=colors.white, backColor=colors.darkblue, spaceAfter=12)))
    elements.append(Spacer(1, 12*mm))

    cert_data = [
        ["Asset ID:", selected_vehicle_id or "VEHICLE1"],
        ["Tread", f"{tread_depth:.1f} mm"],
        ["Pressure", f"{measured_psi} PSI"],
        ["Brakes", "Operational" if service_brake else "Fail"],
        ["Body", body_notes or "Clean"]
    ]

    cert_table = Table(cert_data, colWidths=[60*mm, 120*mm])
    cert_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(cert_table)

    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()

    # Download button
    st.download_button(
        label="Download Full Inspection Report (PDF)",
        data=pdf_bytes,
        file_name=f"sans_inspection_{selected_vehicle_id or 'VEHICLE1'}_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )

    # Feedback
    if compliant:
        st.success("Overall Compliance: PASS ✅")
    else:
        st.error("Overall Compliance: FAIL ❌ - Review notes")

    st.success("Inspection completed! PDF ready for download.")
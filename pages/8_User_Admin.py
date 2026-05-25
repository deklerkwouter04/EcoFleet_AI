# pages/8_User_Admin.py
import streamlit as st
import json
import os
import pandas as pd

# ────────────────────────────────────────────────
#  Enforce login + role access
# ────────────────────────────────────────────────
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Access denied. Please log in.")
    st.switch_page("app.py")
    st.stop()

current_role = st.session_state.get("role", "User")
allowed_roles = ["Admin", "FleetManager"]

if current_role not in allowed_roles:
    st.error(f"Access restricted. Only {', '.join(allowed_roles)} can view this page.")
    st.stop()

# ────────────────────────────────────────────────
#  Load user data file
# ────────────────────────────────────────────────
USER_DATA_FILE = "user_extra_data.json"
SECRET_AUTH_FILE = "_secret_auth_.json"  # created by streamlit_login_auth_ui

def load_user_extra_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_extra_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_registered_emails():
    """Get list of registered emails from the auth file"""
    if os.path.exists(SECRET_AUTH_FILE):
        with open(SECRET_AUTH_FILE, "r") as f:
            auth_data = json.load(f)
            return list(auth_data.keys())  # keys are emails
    return []

# Load data
user_extra = load_user_extra_data()
registered_emails = load_registered_emails()

# ────────────────────────────────────────────────
#  Page UI
# ────────────────────────────────────────────────
st.title("👤 User Administration")
st.markdown(f"**Logged in as:** {st.session_state.get('email')} ({current_role})")

st.info("""
This page allows administrators to manage user roles and company assignments.  
Changes take effect immediately on next login.
""")

# ── Sync check: warn if registered users not in extra data ─────────────────────
missing_users = [email for email in registered_emails if email not in user_extra]
if missing_users:
    st.warning(f"**{len(missing_users)} new user(s) detected** without assigned role/company.")
    if st.button("Auto-assign default role (DataAnalyst) to new users"):
        for email in missing_users:
            user_extra[email] = {
                "company_id": 1,
                "company_name": "Default Company",
                "role": "DataAnalyst",
                "full_name": email.split("@")[0].title()
            }
        save_user_extra_data(user_extra)
        st.success("New users assigned default settings.")
        st.rerun()

# ── Build user table ───────────────────────────────────────────────────────────
if not user_extra:
    st.info("No users configured yet. New users will appear here after first login.")
    st.stop()

# Convert to DataFrame for nice display/edit
users_list = []
for email, info in user_extra.items():
    users_list.append({
        "Email": email,
        "Full Name": info.get("full_name", ""),
        "Company ID": info.get("company_id", 1),
        "Company Name": info.get("company_name", "Default Company"),
        "Role": info.get("role", "User")
    })

df = pd.DataFrame(users_list)

# ── Editable table ─────────────────────────────────────────────────────────────
st.subheader("Manage Users")

edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Email": st.column_config.TextColumn("Email", disabled=True),
        "Full Name": st.column_config.TextColumn("Full Name", required=False),
        "Company ID": st.column_config.NumberColumn("Company ID", min_value=1, max_value=999),
        "Company Name": st.column_config.TextColumn("Company Name"),
        "Role": st.column_config.SelectboxColumn(
            "Role",
            options=["DataAnalyst", "FleetManager", "Inspector", "Executive", "Admin"],
            required=True
        )
    },
    hide_index=True
)

# ── Save changes ───────────────────────────────────────────────────────────────
if st.button("💾 Save All Changes", type="primary"):
    # Convert back to dict
    new_data = {}
    for _, row in edited_df.iterrows():
        email = row["Email"]
        new_data[email] = {
            "full_name": row["Full Name"],
            "company_id": int(row["Company ID"]),
            "company_name": row["Company Name"],
            "role": row["Role"]
        }
    save_user_extra_data(new_data)
    st.success("All user changes saved successfully!")
    st.rerun()

# ── Delete user ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Delete User (Irreversible)")

delete_email = st.selectbox("Select user to delete", options=[""] + list(user_extra.keys()))
if st.button("🗑️ Delete Selected User", type="secondary"):
    if delete_email:
        confirm = st.text_input("Type the email to confirm deletion", key="confirm_delete")
        if confirm == delete_email:
            user_extra.pop(delete_email, None)
            save_user_extra_data(user_extra)
            st.success(f"User {delete_email} deleted.")
            st.rerun()
        else:
            st.error("Email does not match. Deletion cancelled.")
    else:
        st.info("Select a user to delete.")

# ── Summary ───────────────────────────────────────────────────────────────────
st.divider()
col1, col2, col3 = st.columns(3)
col1.metric("Total Users", len(user_extra))
col2.metric("Admins", len([u for u in user_extra.values() if u.get("role") == "Admin"]))
col3.metric("Companies", len(set(u.get("company_id") for u in user_extra.values())))

st.caption("Note: Passwords cannot be changed here — users must use 'Forgot Password' on login page.")
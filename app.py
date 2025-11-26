import streamlit as st
import pandas as pd

# -------------------------------------------------------
# INIT
# -------------------------------------------------------
if "sites" not in st.session_state:
    st.session_state.sites = {}

st.title("CER Wage Tool – Base Engine")
st.write("This is the stable base structure for all future calculations.")


# -------------------------------------------------------
# STEP 1 — ADD SITE DATA
# -------------------------------------------------------
st.header("Step 1: Add / Update Site")

site_name = st.text_input("Site Name (Example: Rajahmundry, Nabha, etc.)")

emp_file = st.file_uploader("Upload Employee Dump (Excel)", type=["xlsx", "xls"])
wage_file = st.file_uploader("Upload Wage / LTS Sheet (Excel)", type=["xlsx", "xls"])

if st.button("Save Site"):
    if site_name == "":
        st.error("Please enter a site name.")
    elif emp_file is None or wage_file is None:
        st.error("Please upload BOTH employee dump and wage sheet.")
    else:
        try:
            emp_df = pd.read_excel(emp_file)
            wage_df = pd.read_excel(wage_file)

            st.session_state.sites[site_name] = {
                "employees": emp_df,
                "wages": wage_df
            }

            st.success(f"Saved site: {site_name}")
            st.write("### Employee File Preview")
            st.dataframe(emp_df.head())
            st.write("### Wage/LTS File Preview")
            st.dataframe(wage_df.head())

        except Exception as e:
            st.error(f"Error loading Excel files: {e}")


sites_list = list(st.session_state.sites.keys())

if len(sites_list) > 0:
    st.write("### Sites Loaded:", sites_list)
else:
    st.info("No sites added yet.")


st.markdown("---")


# -------------------------------------------------------
# STEP 2 — SELECT TRANSACTION TYPE
# -------------------------------------------------------
st.header("Step 2: Select Transaction Type")

transaction_options = [
    "Home to Home → Promotion",
    "Home to Home → New Joinee wage",
    "Home to Home → Confirmation",
    "Home to Home → Probation",
    "Home to Host → Transfer"
]

transaction = st.selectbox("Transaction Type", transaction_options)


st.markdown("---")


# -------------------------------------------------------
# STEP 3 — SITE SELECTION LOGIC
# -------------------------------------------------------
st.header("Step 3: Select Site(s)")

if len(sites_list) == 0:
    st.warning("Please add a site first.")
else:
    if transaction.startswith("Home to Home"):
        home_site = st.selectbox("Home Site", sites_list)
        st.success(f"Home Site Selected: {home_site}")

    if transaction.startswith("Home to Host"):
        col1, col2 = st.columns(2)
        home_site = col1.selectbox("Home Site", sites_list, key="home")
        host_site = col2.selectbox("Host Site", sites_list, key="host")
        st.success(f"Home: {home_site} → Host: {host_site}")


st.markdown("---")


# -------------------------------------------------------
# INTERNAL BASIC SCALE INTERPRETER (NOT DISPLAYED)
# -------------------------------------------------------
# This interprets LTS scale strings like:
# "10-2-30-3-90"
# Produces internal scale list: [10,12,14,...,30,33,36...]
def interpret_scale(scale_str):
    try:
        numbers = [int(x.strip()) for x in scale_str.split("-")]
        if len(numbers) < 3:
            return None

        values = [numbers[0]]
        current = numbers[0]
        i = 1
        steps = 0
        max_steps = 2000

        while i < len(numbers) and steps < max_steps:
            inc = numbers[i]
            end = numbers[i+1] if i+1 < len(numbers) else None

            if end is None:
                # Only increment once — no range
                current += inc
                values.append(current)
                break

            # Increment until reaching the end point
            while current < end:
                current += inc
                values.append(current)
                steps += 1
                if steps >= max_steps:
                    break

            i += 2

        return values

    except:
        return None


# NOTE: This function is intentionally NOT shown to the user.
# It will be used for:
# - Grade fitment checks
# - Promotion logic
# - New joinee validation
# - Transfer wage fitment (Home vs Host)
# - Red flag warnings


st.success("Internal scale interpretation engine is ready (not displayed).")


st.markdown("---")
st.info("Base system running. Now ready to add full transaction logic.")

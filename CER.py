import streamlit as st
import pandas as pd

# ---------- Helpers ----------

def init_state():
"""Initialize session_state containers."""
if "sites" not in st.session_state:
# sites = {
# "SiteName": {
# "employees": DataFrame,
# "wages": DataFrame
# },
# ...
# }
st.session_state.sites = {}


def expand_scale(scale_str, max_value=None, max_steps=200):
"""
Interpret scale string like '10-2-30-3-90' into a list:
10, 12, 14, ..., 30, 33, 36, ..., 90

Format assumption (most common):
start - inc1 - end1 - inc2 - end2 - [inc3 - end3] ...

If max_value is given, stops when values exceed that.
If the string is malformed, returns an empty list.
"""
try:
parts = [int(p.strip()) for p in scale_str.split("-")]
except Exception:
return []

if len(parts) < 3:
# Not enough info
return []

values = []
start = parts[0]
current = start
values.append(current)

# Remaining parts are (inc, end, inc, end, ...)
i = 1
steps = 0

while i < len(parts) and steps < max_steps:
inc = parts[i]
end = parts[i + 1] if i + 1 < len(parts) else None

while True:
current += inc
steps += 1

# If max_value is set and we've exceeded it, stop
if max_value is not None and current > max_value:
return values

values.append(current)

if end is not None and current >= end:
break

# If there's no explicit end given, just keep going
# until max_steps or max_value stops us
if end is None and steps >= max_steps:
return values

i += 2

return values


# ---------- Main App ----------

def main():
init_state()

st.title("Wage Tool Prototype (v0)")
st.write("Prototype to manage **sites** and **transaction types** for wage logic.")

# ----------------- Section 1: Add / Update Site Data -----------------
st.header("Step 1: Add / Update Site Data")

with st.expander("Add a new site (upload Excel dumps)", expanded=True):
site_name = st.text_input("Site name (e.g., Rajahmundry, Nabha, etc.)")

st.markdown("**Upload Employee Dump (Excel)**")
emp_file = st.file_uploader(
"Employee dump file (employee id, name, grade, dob, doj, retirement date, etc.)",
type=["xlsx", "xls"],
key="emp_upload"
)

st.markdown("**Upload Wage / LTS Info (Excel)**")
wage_file = st.file_uploader(
"Wage / scale / settlement info file (grades & scales, standard days 26/30, allowances, etc.)",
type=["xlsx", "xls"],
key="wage_upload"
)

if st.button("Save site data"):
if not site_name:
st.error("Please enter a site name.")
elif emp_file is None or wage_file is None:
st.error("Please upload BOTH employee dump and wage info files.")
else:
try:
emp_df = pd.read_excel(emp_file)
wage_df = pd.read_excel(wage_file)

st.session_state.sites[site_name] = {
"employees": emp_df,
"wages": wage_df,
}

st.success(f"Saved data for site: **{site_name}**")
st.write("Employee dump preview:")
st.dataframe(emp_df.head())
st.write("Wage / LTS sheet preview:")
st.dataframe(wage_df.head())

except Exception as e:
st.error(f"Error reading Excel files: {e}")

# Show current sites
if st.session_state.sites:
st.markdown("### Current Sites Loaded")
st.write(list(st.session_state.sites.keys()))
else:
st.info("No sites loaded yet. Add at least one site above to proceed.")

st.markdown("---")

# ----------------- Section 2: Transaction Selection -----------------
st.header("Step 2: Select Transaction Type")

transaction_options = [
"Home to Home → Promotion",
"Home to Home → New Joinee wage",
"Home to Home → Confirmation",
"Home to Home → Probation",
"Home to Host → Transfer",
]

transaction_type = st.selectbox("Transaction type", transaction_options)

# ----------------- Section 3: Site Selection -----------------
st.header("Step 3: Select Site(s) for this Transaction")

if not st.session_state.sites:
st.warning("Please add at least one site in Step 1 to select here.")
return

site_names = list(st.session_state.sites.keys())

if transaction_type.startswith("Home to Home"):
home_site = st.selectbox("Select Home site", site_names, key="home_site")
st.write(f"Using site **{home_site}** for this transaction.")

# You can access data like this:
home_emp_df = st.session_state.sites[home_site]["employees"]
home_wage_df = st.session_state.sites[home_site]["wages"]

else: # Home to Host → Transfer
col1, col2 = st.columns(2)
with col1:
home_site = st.selectbox("Home site", site_names, key="home_site_transfer")
with col2:
host_site = st.selectbox("Host site", site_names, key="host_site_transfer")

st.write(f"Home: **{home_site}**, Host: **{host_site}**")

home_emp_df = st.session_state.sites[home_site]["employees"]
home_wage_df = st.session_state.sites[home_site]["wages"]

host_emp_df = st.session_state.sites[host_site]["employees"]
host_wage_df = st.session_state.sites[host_site]["wages"]

st.markdown("---")

# ----------------- Section 4: Scale Interpretation Demo -----------------
st.header("Step 4: Scale Interpretation (Prototype)")

st.write(
"For now, we'll just test the interpretation of **Basic scale information** "
"like `Grade 5: 10-2-30-3-90`."
)

scale_str = st.text_input(
"Enter a scale string to test (e.g., 10-2-30-3-90)", value="10-2-30-3-90"
)

if st.button("Expand scale"):
values = expand_scale(scale_str)
if values:
st.success("Scale expanded successfully:")
st.write(values[:50]) # show first 50 steps just in case
st.write(f"Min: {min(values)}, Max: {max(values)}")
else:
st.error("Could not interpret this scale string. Please check the format.")

st.info(
"Next step will be: for each Grade in the site's wage sheet, we'll parse the "
"scale string and use it in the logic for each transaction type."
)


if __name__ == "__main__":
main()

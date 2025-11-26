import streamlit as st
import pandas as pd

# -------------------------------------------------------
# Session init
# -------------------------------------------------------
if "sites" not in st.session_state:
    st.session_state.sites = {}

st.title("CER Wage Tool")


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def interpret_scale(scale_str: str):
    """
    Internal: Interpret a scale string like '10-2-30-3-90' into a list of values.
    Pattern assumed: start - inc1 - end1 - inc2 - end2 - ...
    """
    try:
        nums = [int(n.strip()) for n in scale_str.split("-")]
        if len(nums) < 3:
            return None

        values = [nums[0]]
        current = nums[0]
        i = 1
        steps = 0
        max_steps = 2000

        while i < len(nums) and steps < max_steps:
            inc = nums[i]
            end = nums[i + 1] if i + 1 < len(nums) else None

            # If there is no explicit end → apply increment once
            if end is None:
                current += inc
                values.append(current)
                break

            while current < end and steps < max_steps:
                current += inc
                values.append(current)
                steps += 1

            i += 2

        return values
    except Exception:
        return None


def find_column(df: pd.DataFrame, candidates):
    """
    Find a column in df whose normalized name matches any of the candidates.
    candidates = list of lowercase names without spaces, e.g. ["empid", "employeeid"]
    """
    norm_map = {col: col.lower().replace(" ", "").replace("_", "") for col in df.columns}
    for col, norm in norm_map.items():
        if norm in candidates:
            return col
    return None


def get_site_data(site_name: str):
    site = st.session_state.sites.get(site_name)
    if not site:
        return None, None
    return site.get("employees"), site.get("wages")


# -------------------------------------------------------
# 1. Transaction selection
# -------------------------------------------------------
st.subheader("Select Transaction Type")

transaction_types = [
    "Home to Home → Promotion",
    "Home to Home → New Joinee Wage",
    "Home to Home → Confirmation",
    "Home to Home → Probation",
    "Home to Host → Transfer",
]

transaction = st.selectbox("Transaction", transaction_types)

sites = list(st.session_state.sites.keys())
need_two_sites = transaction.startswith("Home to Host")

st.markdown("---")

# -------------------------------------------------------
# 2. Site selection / creation
# -------------------------------------------------------
st.subheader("Sites")

# Home → Home transactions (including Promotion)
home_site = None
host_site = None

if not need_two_sites:
    # Single-site transaction
    if len(sites) > 0:
        home_site = st.selectbox("Select Site", ["Add new site"] + sites)
    else:
        home_site = "Add new site"

    if home_site == "Add new site":
        st.markdown("### Add New Site")
        site_name = st.text_input("Site Name")

        upload_file = st.file_uploader(
            "Upload combined Excel (Sheet1 = Employees, Sheet2 = LTS/Wage info)",
            type=["xlsx"],
            key="site_upload_single",
        )

        if st.button("Save Site Data"):
            if site_name == "":
                st.error("Please enter a site name.")
            elif upload_file is None:
                st.error("Please upload the Excel file.")
            else:
                try:
                    xls = pd.ExcelFile(upload_file)
                    emp_df = pd.read_excel(xls, xls.sheet_names[0])
                    wage_df = pd.read_excel(xls, xls.sheet_names[1])

                    st.session_state.sites[site_name] = {
                        "employees": emp_df,
                        "wages": wage_df,
                    }
                    st.success(f"Site '{site_name}' saved successfully.")
                    sites = list(st.session_state.sites.keys())
                except Exception as e:
                    st.error(f"Error reading Excel file: {e}")
    else:
        st.success(f"Using Site: {home_site}")

# Home → Host (Transfer) – still just UI, logic later
else:
    st.write("Home → Host Transfer")

    if len(sites) > 0:
        home_site = st.selectbox("Home Site", ["Add new site"] + sites, key="home_site_transfer")
        host_site = st.selectbox("Host Site", ["Add new site"] + sites, key="host_site_transfer")
    else:
        home_site = "Add new site"
        host_site = "Add new site"

    for label, chosen_key in [("Home", "home_add"), ("Host", "host_add")]:
        chosen = home_site if label == "Home" else host_site
        if chosen == "Add new site":
            st.markdown(f"### Add {label} Site")
            site_name = st.text_input(f"{label} Site Name", key=f"{label}_name")

            upload_file = st.file_uploader(
                f"Upload combined Excel for {label} Site (Sheet1 = Employees, Sheet2 = LTS/Wage info)",
                type=["xlsx"],
                key=f"{label}_upload",
            )

            if st.button(f"Save {label} Site", key=f"{label}_save_btn"):
                if site_name == "":
                    st.error("Please enter a site name.")
                elif upload_file is None:
                    st.error("Please upload the Excel file.")
                else:
                    try:
                        xls = pd.ExcelFile(upload_file)
                        emp_df = pd.read_excel(xls, xls.sheet_names[0])
                        wage_df = pd.read_excel(xls, xls.sheet_names[1])

                        st.session_state.sites[site_name] = {
                            "employees": emp_df,
                            "wages": wage_df,
                        }
                        st.success(f"{label} Site '{site_name}' saved successfully.")
                        sites = list(st.session_state.sites.keys())
                    except Exception as e:
                        st.error(f"Error reading Excel file: {e}")

    if home_site != "Add new site" and host_site != "Add new site":
        st.success(f"Selected Home: {home_site} → Host: {host_site}")

st.markdown("---")


# -------------------------------------------------------
# 3. HOME TO HOME → PROMOTION LOGIC
# -------------------------------------------------------
if transaction.startswith("Home to Home") and "Promotion" in transaction and home_site and home_site != "Add new site":
    st.subheader("Home → Home Promotion – Upload Promotion List")

    emp_df, wage_df = get_site_data(home_site)
    if emp_df is None or wage_df is None:
        st.error("Site data not found or incomplete. Please re-upload site Excel.")
    else:
        promo_file = st.file_uploader(
            "Upload Promotion Excel (Employee list)",
            type=["xlsx", "xls"],
            key="promo_upload",
        )

        st.caption("Expected columns (names can vary slightly): Employee ID, Name, Current Grade, New Grade.")

        if promo_file is not None:
            try:
                promo_df = pd.read_excel(promo_file)
            except Exception as e:
                st.error(f"Error reading Promotion Excel: {e}")
                promo_df = None

            if promo_df is not None:
                # Map columns in promotion file
                promo_emp_col = find_column(promo_df, ["empid", "employeeid", "employee_no", "employeecode"])
                promo_name_col = find_column(promo_df, ["name", "employeename"])
                promo_curr_grade_col = find_column(promo_df, ["currentgrade", "grade", "presentgrade"])
                promo_new_grade_col = find_column(promo_df, ["newgrade", "promotedgrade"])

                if not all([promo_emp_col, promo_curr_grade_col, promo_new_grade_col]):
                    st.error(
                        "Promotion file is missing required columns. "
                        "Need at least Employee ID, Current Grade, New Grade."
                    )
                    st.write("Columns found:", list(promo_df.columns))
                else:
                    # Map columns in employee master
                    emp_id_col = find_column(emp_df, ["empid", "employeeid", "employee_no", "employeecode"])
                    emp_grade_col = find_column(emp_df, ["grade", "empgrade"])
                    emp_basic_col = find_column(emp_df, ["basic", "basicpay", "currentbasic"])

                    if not all([emp_id_col, emp_grade_col, emp_basic_col]):
                        st.error(
                            "Employee dump for the site does not have required columns "
                            "(Employee ID, Grade, Basic). Please check the site Excel."
                        )
                        st.write("Employee columns:", list(emp_df.columns))
                    else:
                        # Map columns in wage/LTS sheet
                        wage_grade_col = find_column(wage_df, ["grade", "gradecode", "gradeid"])
                        wage_scale_col = find_column(wage_df, ["scale", "basicscale", "payscale", "pay_scale"])

                        if not all([wage_grade_col, wage_scale_col]):
                            st.error(
                                "Wage/LTS sheet does not have Grade and Scale columns. "
                                "Please ensure grade and scale strings are present."
                            )
                            st.write("Wage/LTS columns:", list(wage_df.columns))
                        else:
                            # Merge promotion list with employee master for validation and current basic
                            merged = promo_df.merge(
                                emp_df[[emp_id_col, emp_grade_col, emp_basic_col]],
                                left_on=promo_emp_col,
                                right_on=emp_id_col,
                                how="left",
                                suffixes=("", "_emp"),
                            )

                            # Grade mismatch check
                            grade_mismatch_mask = merged[promo_curr_grade_col] != merged[emp_grade_col]
                            grade_mismatches = merged[grade_mismatch_mask]

                            if not grade_mismatches.empty:
                                st.error("Grade mismatch found between promotion file and site employee master.")
                                st.write("Mismatched rows:")
                                st.dataframe(
                                    grade_mismatches[
                                        [promo_emp_col, promo_curr_grade_col, emp_grade_col]
                                    ].rename(
                                        columns={
                                            promo_emp_col: "Employee ID",
                                            promo_curr_grade_col: "Grade in Promotion File",
                                            emp_grade_col: "Grade in Master",
                                        }
                                    )
                                )
                            else:
                                st.success("All current grades in promotion file match the site employee data.")

                            # Proceed with fitment for rows where we have current basic and new grade
                            valid_rows = merged[merged[emp_basic_col].notna()]

                            if valid_rows.empty:
                                st.error("No rows with valid current basic found for fitment.")
                            else:
                                results = []

                                # Build a dict of grade → scale list for quick use
                                grade_to_scale = {}
                                for _, row in wage_df[[wage_grade_col, wage_scale_col]].dropna().iterrows():
                                    g = str(row[wage_grade_col]).strip()
                                    s = str(row[wage_scale_col]).strip()
                                    scale_vals = interpret_scale(s)
                                    if scale_vals:
                                        grade_to_scale[g] = sorted(set(scale_vals))

                                for _, row in valid_rows.iterrows():
                                    emp_id = row[promo_emp_col]
                                    name_val = row[promo_name_col] if promo_name_col else ""
                                    curr_grade = row[promo_curr_grade_col]
                                    new_grade = row[promo_new_grade_col]
                                    curr_basic = row[emp_basic_col]

                                    new_grade_str = str(new_grade).strip()
                                    scale_vals = grade_to_scale.get(new_grade_str)

                                    if not scale_vals:
                                        results.append(
                                            {
                                                "Employee ID": emp_id,
                                                "Name": name_val,
                                                "Current Grade": curr_grade,
                                                "New Grade": new_grade,
                                                "Current Basic": curr_basic,
                                                "New Basic (Promoted)": None,
                                                "Fitment Cost": None,
                                                "Remark": f"No scale found for grade {new_grade_str}",
                                            }
                                        )
                                        continue

                                    # Fitment logic: place in the promoted scale
                                    # If current basic in scale → keep
                                    # Else → go to next higher basic in the scale
                                    new_basic = None
                                    remark = ""

                                    if curr_basic in scale_vals:
                                        new_basic = curr_basic
                                        remark = "No fitment; already in scale"
                                    else:
                                        higher_vals = [v for v in scale_vals if v >= curr_basic]
                                        if higher_vals:
                                            new_basic = higher_vals[0]
                                            remark = "Fitted to next higher basic in promoted scale"
                                        else:
                                            # Current basic above max scale: keep current basic, no negative fitment
                                            new_basic = curr_basic
                                            remark = "Above max scale; retained current basic"

                                    fitment_cost = float(new_basic) - float(curr_basic)

                                    results.append(
                                        {
                                            "Employee ID": emp_id,
                                            "Name": name_val,
                                            "Current Grade": curr_grade,
                                            "New Grade": new_grade,
                                            "Current Basic": curr_basic,
                                            "New Basic (Promoted)": new_basic,
                                            "Fitment Cost": fitment_cost,
                                            "Remark": remark,
                                        }
                                    )

                                if results:
                                    result_df = pd.DataFrame(results)
                                    st.subheader("Promotion Fitment Result (Basic only)")
                                    st.dataframe(result_df)

                                    total_fitment = result_df["Fitment Cost"].fillna(0).sum()
                                    st.write(f"**Total Fitment Cost (Basic only) for this file: {total_fitment:.2f}**")


# -------------------------------------------------------
# Final note
# -------------------------------------------------------
st.markdown("---")
st.info("Home → Home Promotion basic fitment engine is ready. Other allowances can be layered on top later.")

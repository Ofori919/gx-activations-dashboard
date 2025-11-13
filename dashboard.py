
import streamlit as st
import pandas as pd
import plotly.express as px
import time
import os
import json
from typing import Dict, Any

# Third-party dependencies that must appear in requirements.txt
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode
import gspread
from google.oauth2.service_account import Credentials

# ------------------------------
# CONFIG / CONSTANTS
# ------------------------------
SHEET_ID = "1IHHtOFCFs6SdE88L3ZrUfbg_rmXgF8kHrhbmE4Yk3Y0"
WORKSHEET_NAME = "GX Dashboard Data"

DEFAULT_DATA = {
    "hcp_educated": 28, "hcp_family": 19, "hcp_internal": 18, "hcp_general": 28,
    "hcp_md_do": 75, "hcp_np_pa": 25,
    "confidence_diagnosing": 85, "confidence_treating": 78, "confidence_managing": 82,
    "intent_to_test": 90,
    "attendees_educated": 98,
    "demo_black": 55, "demo_hispanic": 25, "demo_white": 17, "demo_other": 3,
    "age_55_plus": 45, "age_35_54": 28, "age_18_34": 27,
    "gender_male": 75,
    "aware_ldlc": 88, "understand_risk": 84, "intent_test": 91, "intent_followup": 79,
    "ldlc_0_54": 0.54, "ldlc_55_70": 0.70, "ldlc_70_99": 0.99,
    "ldlc_100_139": 1.39, "ldlc_140_189": 1.89, "ldlc_190_plus": 1.90,
}

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ------------------------------
# AUTH / GSPREAD HELPERS
# ------------------------------

def _creds_from_st_secrets() -> Credentials | None:
    """Return google Credentials object from st.secrets if available."""
    try:
        if "gcp_service_account" in st.secrets:
            sa = st.secrets["gcp_service_account"]
            # st.secrets might return a TOML-like mapping or a JSON string
            if isinstance(sa, str):
                sa = json.loads(sa)
            creds = Credentials.from_service_account_info(sa, scopes=SCOPES)
            return creds
    except Exception as e:
        st.error(f"Error parsing st.secrets gcp_service_account: {e}")
    return None


def _creds_from_file_env() -> Credentials | None:
    """Try loading credentials from GOOGLE_APPLICATION_CREDENTIALS env var or local file.
    Returns None if no usable file was found.
    """
    json_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
    if not os.path.exists(json_path):
        return None
    try:
        creds = Credentials.from_service_account_file(json_path, scopes=SCOPES)
        return creds
    except Exception as e:
        st.error(f"Failed loading credentials from file {json_path}: {e}")
        return None


def get_gspread_client() -> gspread.Client:
    """Return an authorized gspread client.

    Priority:
    1) st.secrets['gcp_service_account'] (recommended for Streamlit Cloud)
    2) GOOGLE_APPLICATION_CREDENTIALS env var or service_account.json (local/dev)
    """
    # 1) try st.secrets
    creds = _creds_from_st_secrets()
    if creds is not None:
        return gspread.authorize(creds)

    # 2) try env / local file
    creds = _creds_from_file_env()
    if creds is not None:
        return gspread.authorize(creds)

    # 3) nothing worked
    raise RuntimeError("No Google service account credentials found. Add credentials to st.secrets or set GOOGLE_APPLICATION_CREDENTIALS to a local JSON file.")

# ------------------------------
# DATA IO
# ------------------------------

@st.cache_data(ttl=60)
def load_data_from_sheet() -> Dict[str, Any]:
    """Load key/value pairs from Google Sheet. Cached for 60 seconds.

    Returns DEFAULT_DATA copy on errors.
    """
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet(WORKSHEET_NAME)
        rows = ws.get_all_values()  # returns list of lists
        # Expect header row: [key, value]
        if len(rows) < 2:
            return DEFAULT_DATA.copy()

        data: Dict[str, Any] = {}
        for row in rows[1:]:
            if len(row) < 2:
                continue
            key = row[0]
            val = row[1]
            if key == "":
                continue
            # try converting numeric values
            try:
                if val is None or val == "":
                    parsed = ""
                elif isinstance(val, (int, float)):
                    parsed = val
                elif "." in val:
                    parsed = float(val)
                else:
                    parsed = int(val)
            except Exception:
                parsed = val
            data[key] = parsed
        # combine with defaults for missing keys
        out = DEFAULT_DATA.copy()
        out.update(data)
        return out
    except Exception as e:
        st.error(f"⚠️ Could not load data from Google Sheets: {e}")
        return DEFAULT_DATA.copy()


def save_data_to_sheet(data: Dict[str, Any]) -> bool:
    """Save the provided dict to Google Sheet as two-column rows (key, value).

    This function writes all rows in a single batch update for speed.
    Returns True on success, False on failure.
    """
    try:
        client = get_gspread_client()
        sh = client.open_by_key(SHEET_ID)
        ws = sh.worksheet(WORKSHEET_NAME)
        rows = [["key", "value"]]
        for k, v in data.items():
            rows.append([k, str(v)])
        # Write starting from A1
        ws.clear()
        ws.update("A1", rows)
        # Invalidate cache
        load_data_from_sheet.clear()
        return True
    except Exception as e:
        st.error(f"⚠️ Could not save data to Google Sheets: {e}")
        return False

# ------------------------------
# UI HELPERS
# ------------------------------

def render_metric_card(label: str, value: Any, color: str = "#1f77b4", bg_color: str = "#f0f8ff"):
    st.markdown(f"""
        <div style='text-align:center; background-color:{bg_color}; border-radius:12px; padding:14px; margin:8px 0; min-height:120px; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
            <div style='font-size:13px; color:#444; font-weight:600; margin-bottom:6px;'>{label}</div>
            <div style='font-size:32px; font-weight:bold; color:{color};'>{value}%</div>
        </div>
    """, unsafe_allow_html=True)

# ------------------------------
# SECTION RENDERS
# ------------------------------

def render_hcp_section(data: Dict[str, Any]):
    st.markdown("### TOTAL HCPs EDUCATED in GX")
    hcp_val = int(float(data.get("hcp_educated", 0)))
    new_hcp = st.number_input("Running Total", min_value=0, value=hcp_val, key="hcp_educated_input")
    if st.session_state.get("hcp_educated_input") != hcp_val:
        st.session_state.modified = True
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric_card("Confidence<br>Diagnosing", int(float(data.get("confidence_diagnosing", 0))), "#1f77b4", "#f0f8ff")
    with c2: render_metric_card("Confidence<br>Treating", int(float(data.get("confidence_treating", 0))), "#ff7f0e", "#fff8f0")
    with c3: render_metric_card("Confidence<br>Managing", int(float(data.get("confidence_managing", 0))), "#2ca02c", "#f0fff0")
    with c4: render_metric_card("Intent<br>to Test", int(float(data.get("intent_to_test", 0))), "#d62728", "#fff0f0")

    st.markdown("#### Practice Type")
    cols = st.columns(3)
    keys = ["hcp_family", "hcp_internal", "hcp_general"]
    practice_vals = {}
    for key, col in zip(keys, cols):
        with col:
            val = int(float(data.get(key, 0)))
            practice_vals[key] = st.number_input(key.replace("hcp_", "").capitalize(), min_value=0, value=val, key=f"inp_{key}")
            if st.session_state.get(f"inp_{key}") != val:
                st.session_state.modified = True
    practice_df = pd.DataFrame({"Type": ["Family", "Internal", "General"], "Count": list(practice_vals.values())})
    fig = px.bar(practice_df, x="Count", y="Type", orientation="h", text="Count")
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=220)
    st.plotly_chart(fig, use_container_width=True)


def render_attendees_section(data: Dict[str, Any]):
    st.markdown("### TOTAL ATTENDEES EDUCATED in GX")
    curr = int(float(data.get("attendees_educated", 0)))
    val = st.number_input("Running Total", min_value=0, value=curr, key="inp_attendees")
    if st.session_state.get("inp_attendees") != curr:
        st.session_state.modified = True


def render_demographics_section(data: Dict[str, Any]):
    st.markdown("#### Demographics")
    demo_keys = ["demo_black", "demo_hispanic", "demo_white", "demo_other"]
    labels = ["Black %", "Hispanic %", "White %", "Other %"]
    demo_vals = {}
    cols = st.columns(4)
    for key, label, col in zip(demo_keys, labels, cols):
        with col:
            val = int(float(data.get(key, 0)))
            demo_vals[key] = st.number_input(label, min_value=0, max_value=100, value=val, key=f"inp_{key}")
            if st.session_state.get(f"inp_{key}") != val:
                st.session_state.modified = True

    df = pd.DataFrame({"Group": ["Black/African American", "Hispanic/Latino", "White/Caucasian", "Other"], "Percent": list(demo_vals.values())})
    total = df["Percent"].sum()
    if total != 100 and total > 0:
        st.warning(f"Sum: {total}%. Normalizing...")
        df["Percent"] = (df["Percent"] / total * 100).round(1)
    fig = px.bar(df, x="Percent", y="Group", orientation="h", text="Percent")
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=240)
    st.plotly_chart(fig, use_container_width=True)


def render_age_gender_section(data: Dict[str, Any]):
    col_age, col_gender = st.columns(2)
    with col_age:
        st.markdown("**Age Distribution**")
        age_keys = ["age_55_plus", "age_35_54", "age_18_34"]
        age_labels = ["55+ yrs", "35-54 yrs", "18-34 yrs"]
        age_vals = {}
        for key, label in zip(age_keys, age_labels):
            val = int(float(data.get(key, 0)))
            age_vals[key] = st.number_input(label, min_value=0, value=val, key=f"inp_{key}")
            if st.session_state.get(f"inp_{key}") != val:
                st.session_state.modified = True
        age_df = pd.DataFrame({"Age": age_labels, "Count": list(age_vals.values())})
        fig = px.pie(age_df, values="Count", names="Age", hole=0.4)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=420, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=False)

    with col_gender:
        st.markdown("**Gender**")
        male_val = int(float(data.get("gender_male", 0)))
        male = st.number_input("Male %", min_value=0, max_value=100, value=male_val, key="inp_gender_male")
        if st.session_state.get("inp_gender_male") != male_val:
            st.session_state.modified = True
        female = max(0, 100 - male)
        fig = px.pie(values=[male, female], names=["Male", "Female"], hole=0.4)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=420, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=False)


def render_knowledge_intent_section(data: Dict[str, Any]):
    st.markdown("#### Knowledge / Intent")
    col1, col2, col3, col4 = st.columns(4)
    metric_info = [
        ("aware_ldlc", "LDL-c Awareness"),
        ("understand_risk", "LDL-c Risk Understanding"),
        ("intent_test", "Intent to Test"),
        ("intent_followup", "Intent to Follow-up"),
    ]
    for (key, label), col in zip(metric_info, [col1, col2, col3, col4]):
        with col:
            val = int(float(data.get(key, 0)))
            rv = st.number_input(label + " %", min_value=0, max_value=100, value=val, key=f"inp_{key}")
            if st.session_state.get(f"inp_{key}") != val:
                st.session_state.modified = True
            render_metric_card(label, rv)


def render_ldlc_matrix(data: Dict[str, Any]):
    st.markdown("#### LDL-c (mg/dL) Distribution")
    rows = [
        ["0-54", float(data.get("ldlc_0_54", 0))],
        ["55-70", float(data.get("ldlc_55_70", 0))],
        ["70-99", float(data.get("ldlc_70_99", 0))],
        ["100-139", float(data.get("ldlc_100_139", 0))],
        ["140-189", float(data.get("ldlc_140_189", 0))],
        [">=190", float(data.get("ldlc_190_plus", 0))],
    ]
    matrix = pd.DataFrame(rows, columns=["Range", "Value"])

    gb = AgGrid(
        matrix,
        editable=True,
        fit_columns_on_grid_load=True,
        height=220,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.AS_INPUT,
    )
    edited = pd.DataFrame(gb["data"])
    # Normalize to 100 if needed
    total = edited["Value"].sum()
    if total != 100 and total > 0:
        edited["Value"] = (edited["Value"] / total * 100).round(2)

    range_to_key = {
        "0-54": "ldlc_0_54", "55-70": "ldlc_55_70", "70-99": "ldlc_70_99",
        "100-139": "ldlc_100_139", "140-189": "ldlc_140_189", ">=190": "ldlc_190_plus"
    }
    # store edited values into session state so Save button can persist them in one batch
    for _, row in edited.iterrows():
        key = range_to_key[row["Range"]]
        st.session_state[f"inp_{key}"] = float(row["Value"])

    st.table(edited.style.format({"Value": "{:.2f}"}))

# ------------------------------
# MAIN
# ------------------------------

def collect_changes_into_dict(original: Dict[str, Any]) -> Dict[str, Any]:
    """Build a new data dict from original + any inputs present in session_state."""
    out = original.copy()
    # general keys we used with prefix inp_
    for k in list(out.keys()):
        sk = f"inp_{k}"
        if sk in st.session_state:
            # try cast numbers where appropriate
            val = st.session_state[sk]
            try:
                if isinstance(out[k], int):
                    out[k] = int(val)
                elif isinstance(out[k], float):
                    out[k] = float(val)
                else:
                    out[k] = val
            except Exception:
                out[k] = val
    # hcp_educated special
    if "hcp_educated_input" in st.session_state:
        try:
            out["hcp_educated"] = int(st.session_state["hcp_educated_input"])
        except Exception:
            pass
    return out


def main():
    st.set_page_config(page_title="GX Activations Dashboard", layout="wide")
    st.title("GX ACTIVATIONS (CITIES) – Real-time Dashboard")

    # Load data (cached)
    data = load_data_from_sheet()

    # small toolbar
    col1, col2, col3 = st.columns([4, 1, 1])
    with col3:
        if st.button("🔄 Reload now"):
            load_data_from_sheet.clear()
            st.experimental_rerun()
    with col2:
        auto_refresh = st.checkbox("Auto-refresh 30s", value=True)

    # Auto refresh logic (non-blocking) — stores last refresh time in session_state
    if auto_refresh:
        last = st.session_state.get("last_refresh", 0)
        if time.time() - last > 30:
            st.session_state.last_refresh = time.time()
            load_data_from_sheet.clear()
            # don't immediately rerun to avoid infinite loops, but update 'data' ref
            data = load_data_from_sheet()

    # track whether user has made any edits
    if "modified" not in st.session_state:
        st.session_state.modified = False

    # Render sections
    st.markdown("---")
    render_hcp_section(data)
    st.markdown("---")
    render_attendees_section(data)
    render_demographics_section(data)
    render_age_gender_section(data)
    render_knowledge_intent_section(data)
    st.markdown("---")
    render_ldlc_matrix(data)

    st.markdown("---")
    cols = st.columns([1, 1, 1, 6])
    save_col, reset_col, info_col, _ = cols

    with save_col:
        if st.button("💾 Save to Google Sheets"):
            new_data = collect_changes_into_dict(data)
            success = save_data_to_sheet(new_data)
            if success:
                st.success("✅ Data saved successfully!")
                st.session_state.modified = False
                # refresh cached data
                load_data_from_sheet.clear()
    with reset_col:
        if st.button("↺ Reset (discard local edits)"):
            # clear input keys we created
            keys_to_remove = [k for k in st.session_state.keys() if k.startswith("inp_") or k == "hcp_educated_input"]
            for k in keys_to_remove:
                del st.session_state[k]
            st.session_state.modified = False
            load_data_from_sheet.clear()
            st.experimental_rerun()

    # Inform user about unsaved changes
    if st.session_state.modified:
        st.warning("You have unsaved changes. Click 'Save to Google Sheets' to persist them.")

    # Debug / admin: show loaded secrets present (do not show in public)
    if st.sidebar.checkbox("Show debug info"):
        st.sidebar.write("Loaded data keys:", list(data.keys()))
        st.sidebar.write("st.secrets contains gcp_service_account:", "gcp_service_account" in st.secrets)


if __name__ == "__main__":
    main()


import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode
import time
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# =============================================================================
# DATA MANAGEMENT (MULTI-CITY SUPPORT)
# =============================================================================
DATA_FILE = Path("gx_dashboard_data.csv")

# Default data per city (expandable)
DEFAULT_DATA_PER_CITY = {
    "New York": {
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
        "ldlc_0_75": 0.75, "ldlc_76_125": 1.25, "ldlc_126_plus": 1.26,
    },
    "Los Angeles": {
        "hcp_educated": 15, "hcp_family": 12, "hcp_internal": 10, "hcp_general": 15,
        "hcp_md_do": 70, "hcp_np_pa": 30,
        "confidence_diagnosing": 80, "confidence_treating": 75, "confidence_managing": 78,
        "intent_to_test": 85,
        "attendees_educated": 75,
        "demo_black": 20, "demo_hispanic": 45, "demo_white": 25, "demo_other": 10,
        "age_55_plus": 35, "age_35_54": 40, "age_18_34": 25,
        "gender_male": 60,
        "aware_ldlc": 82, "understand_risk": 78, "intent_test": 88, "intent_followup": 75,
        "ldlc_0_54": 0.50, "ldlc_55_70": 0.65, "ldlc_70_99": 0.95,
        "ldlc_100_139": 1.35, "ldlc_140_189": 1.85, "ldlc_190_plus": 1.85,
        "ldlc_0_75": 0.70, "ldlc_76_125": 1.20, "ldlc_126_plus": 1.22,
    },
    # Add more cities here (e.g., "Chicago": {...})
}

# City coordinates (lat, lon) for map pins
CITY_COORDS = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    # Add more: "Chicago": (41.8781, -87.6298), etc.
}

def load_data():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE, index_col=0, header=None).squeeze("columns")
        data_dict = df.to_dict()
        # Migrate old single-city data to "New York" if needed
        if "hcp_educated" in data_dict and len(data_dict) < 50:  # Rough check for old format
            data_dict = {"New York": data_dict}
            save_data(data_dict)
        return data_dict
    return {city: DEFAULT_DATA_PER_CITY.get(city, {}) for city in CITY_COORDS.keys()}

def save_data(data):
    # Flatten to Series for CSV (city_key as index)
    flat_data = {}
    for city, metrics in data.items():
        for k, v in metrics.items():
            flat_data[f"{city}_{k}"] = v
    pd.Series(flat_data).to_csv(DATA_FILE, header=False)

def get_city_data(data, city):
    return data.get(city, {})

def update_value(data, city, key, value):
    if city not in data:
        data[city] = {}
    data[city][key] = value
    save_data(data)

def get_city_coords(city):
    return CITY_COORDS.get(city, (0, 0))

# =============================================================================
# MAP SECTION
# =============================================================================
@st.cache_data  # Cache map for performance
def create_city_map(data):
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)  # US center

    for city in CITY_COORDS.keys():
        city_data = get_city_data(data, city)
        hcp = city_data.get("hcp_educated", 0)
        lat, lon = get_city_coords(city)

        # Color by activation level (hcp_educated)
        color = "green" if hcp > 20 else "orange" if hcp > 10 else "red"
        folium.Marker(
            [lat, lon],
            popup=f"<b>{city}</b><br>HCPs Educated: {hcp}<br>Attendees: {city_data.get('attendees_educated', 0)}<br><a href='#'>View Details</a>",
            tooltip=city,
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)

    return m

# =============================================================================
# UI COMPONENTS (UNCHANGED)
# =============================================================================
def render_metric_card(label, value, color="#1f77b4", bg_color="#f0f8ff"):
    st.markdown(f"""
        <div style='
            text-align: center;
            background-color: {bg_color};
            border-radius: 12px;
            padding: 20px 12px;
            margin: 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            min-height: 150px;
            height: 150px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        '>
            <div style='font-size: 13px; color: #444; font-weight: 600; margin-bottom: 8px;'>{label}</div>
            <div style='font-size: 36px; font-weight: bold; color: {color};'>{value}%</div>
        </div>
    """, unsafe_allow_html=True)

# [All your existing render_* functions remain the SAME - render_hcp_section, render_attendees_section, etc.]
# ... (Omit for brevity - copy from your current code)

# ----------------------------------------------------------------------
# HCP SECTION (CITY-AWARE)
# ----------------------------------------------------------------------
def render_hcp_section(data, city):
    city_data = get_city_data(data, city)
    st.markdown("### TOTAL HCPs EDUCATED in GX")
    hcp_educated = st.number_input("Running Total", min_value=0, value=int(float(city_data.get("hcp_educated", 0))), key=f"{city}_hcp_educated_input")
    if f"{city}_hcp_educated_input" in st.session_state and st.session_state[f"{city}_hcp_educated_input"] != city_data.get("hcp_educated", 0):
        update_value(data, city, "hcp_educated", st.session_state[f"{city}_hcp_educated_input"])

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric_card("Confidence<br>Diagnosing", int(float(city_data.get("confidence_diagnosing", 0))), "#1f77b4", "#f0f8ff")
    with c2: render_metric_card("Confidence<br>Treating", int(float(city_data.get("confidence_treating", 0))), "#ff7f0e", "#fff8f0")
    with c3: render_metric_card("Confidence<br>Managing", int(float(city_data.get("confidence_managing", 0))), "#2ca02c", "#f0fff0")
    with c4: render_metric_card("Intent<br>to Test", int(float(city_data.get("intent_to_test", 0))), "#d62728", "#fff0f0")

    st.markdown("#### Practice Type")
    practice_data = {
        "hcp_family": st.number_input("Family", min_value=0, value=int(float(city_data.get("hcp_family", 0))), key=f"{city}_hcp_family"),
        "hcp_internal": st.number_input("Internal", min_value=0, value=int(float(city_data.get("hcp_internal", 0))), key=f"{city}_hcp_internal"),
        "hcp_general": st.number_input("General", min_value=0, value=int(float(city_data.get("hcp_general", 0))), key=f"{city}_hcp_general"),
    }
    for key in practice_data:
        if f"{city}_{key}" in st.session_state and st.session_state[f"{city}_{key}"] != city_data.get(key, 0):
            update_value(data, city, key, st.session_state[f"{city}_{key}"])

    practice_df = pd.DataFrame({
        "Type": ["Family", "Internal", "General"],
        "Count": [practice_data["hcp_family"], practice_data["hcp_internal"], practice_data["hcp_general"]]
    })
    fig_practice = px.bar(practice_df, x="Count", y="Type", orientation='h', color="Type", text="Count")
    fig_practice.update_layout(showlegend=False, height=220, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_practice, use_container_width=True)

# [Update other sections similarly: render_attendees_section(data, city), etc. - pass 'city' param and prefix keys with city_]
# For brevity, assume you adapt them like above (e.g., key=f"{city}_attendees")

# ----------------------------------------------------------------------
# LDL-C MATRIX (CITY-AWARE)
# ----------------------------------------------------------------------
def render_ldlc_matrix(data, city):
    city_data = get_city_data(data, city)
    st.markdown("#### LDL-c (mg/dL) Distribution")
    matrix = pd.DataFrame({
        "Range": ["0-54", "55-70", "70-99", "100-139", "140-189", "≥190"],
        "Value": [city_data.get("ldlc_0_54", 0), city_data.get("ldlc_55_70", 0), city_data.get("ldlc_70_99", 0), 
                  city_data.get("ldlc_100_139", 0), city_data.get("ldlc_140_189", 0), city_data.get("ldlc_190_plus", 0)]
    })

    gb = AgGrid(
        matrix,
        editable=True,
        fit_columns_on_grid_load=True,
        height=220,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.AS_INPUT,
    )
    edited = gb["data"]

    total = edited["Value"].sum()
    if total != 100 and total > 0:
        edited["Value"] = (edited["Value"] / total * 100).round(2)

    range_to_key = {
        "0-54": "ldlc_0_54", "55-70": "ldlc_55_70", "70-99": "ldlc_70_99",
        "100-139": "ldlc_100_139", "140-189": "ldlc_140_189", "≥190": "ldlc_190_plus"
    }
    for _, row in edited.iterrows():
        key = range_to_key[row["Range"]]
        if city_data.get(key) != row["Value"]:
            update_value(data, city, key, row["Value"])

    def color_ldlc(val):
        if val <= 0.75: return "background-color: #d4edda"
        elif val <= 1.25: return "background-color: #c3e6cb"
        else: return "background-color: #bbe5b3"

    styled = edited.style.applymap(color_ldlc, subset=["Value"])
    st.table(styled)

# =============================================================================
# MAIN APP (MULTI-CITY + MAP)
# =============================================================================
def main():
    st.set_page_config(page_title="GX Activations Dashboard", layout="wide")
    data = load_data()

    st.markdown("<h1 style='text-align: center;'>GX ACTIVATIONS (CITIES) – Real-time Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # City selector (default: New York)
    selected_city = st.selectbox("Select City", options=list(CITY_COORDS.keys()), index=0)

    col_title, col_toggle = st.columns([6, 1])
    with col_toggle:
        dark_mode = st.toggle("Dark Mode", value=False)

    refresh = st.checkbox("Auto-refresh (30s)", value=True)
    if refresh:
        time.sleep(30)
        st.rerun()

    csv_data = pd.Series({
        f"{city}__{k}": v 
        for city, metrics in data.items() 
        for k, v in metrics.items()
    }).to_csv().encode()

    st.download_button(
        "Download All Cities Data",
        data=csv_data,
        file_name=f"gx_dashboard_all_cities_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

    # Interactive Map
    st.markdown("### City Activation Map")
    city_map = create_city_map(data)
    map_data = st_folium(city_map, width=700, height=400)

    # Auto-switch city if map click (from popup - note: requires JS for full interactivity, but selector works)
    if "last_clicked_city" in st.session_state:
        selected_city = st.session_state.last_clicked_city
        st.session_state.pop("last_clicked_city", None)  # Clear after use

    col_left, col_right = st.columns([1, 1])
    with col_left:
        render_attendees_section(data, selected_city)
        st.markdown("---")
        render_demographics_section(data, selected_city)
        st.markdown("---")
        render_age_gender_section(data, selected_city)
        st.markdown("---")
        render_knowledge_intent_section(data, selected_city)

    with col_right:
        render_hcp_section(data, selected_city)
        st.markdown("---")
        render_ldlc_matrix(data, selected_city)

    st.caption("*All percentages reflect the percent increase from pre-survey to post-survey results. | Switch cities via dropdown or map pins.")

# =============================================================================
# RUN
# =============================================================================
if __name__ == "__main__":
    main()



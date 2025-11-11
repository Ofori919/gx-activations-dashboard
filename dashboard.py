import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode
import time
import folium
from streamlit_folium import st_folium

# =============================================================================
# DATA MANAGEMENT
# =============================================================================
DATA_FILE = Path("gx_dashboard_data.csv")

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
}

CITY_COORDS = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
}

def load_data():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE, index_col=0, header=None).squeeze("columns")
        data_dict = df.to_dict()
        if "hcp_educated" in data_dict and len(data_dict) < 50:
            data_dict = {"New York": data_dict}
            save_data(data_dict)
        nested = {}
        for key, val in data_dict.items():
            if "__" in key:
                city, metric = key.split("__", 1)
                if city not in nested:
                    nested[city] = {}
                nested[city][metric] = val
        return nested
    return {city: DEFAULT_DATA_PER_CITY.get(city, {}) for city in CITY_COORDS.keys()}

def save_data(data):
    flat_data = {}
    for city, metrics in data.items():
        for k, v in metrics.items():
            flat_data[f"{city}__{k}"] = v
    pd.Series(flat_data).to_csv(DATA_FILE, header=False)

def get_city_data(data, city):
    return data.get(city, {})

def update_value(data, city, key, value):
    if city not in data:
        data[city] = {}
    data[city][key] = value
    save_data(data)

# =============================================================================
# MAP
# =============================================================================
@st.cache_data
def create_city_map(data):
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
    for city in CITY_COORDS.keys():
        city_data = get_city_data(data, city)
        hcp = city_data.get("hcp_educated", 0)
        lat, lon = CITY_COORDS[city]
        color = "green" if hcp > 20 else "orange" if hcp > 10 else "red"
        folium.Marker(
            [lat, lon],
            popup=f"<b>{city}</b><br>HCPs: {hcp}<br>Attendees: {city_data.get('attendees_educated', 0)}",
            tooltip=city,
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)
    return m

# =============================================================================
# UI
# =============================================================================
def render_metric_card(label, value, color="#1f77b4", bg_color="#f0f8ff"):
    st.markdown(f"""
        <div style='text-align: center; background-color: {bg_color}; border-radius: 12px; padding: 20px; margin: 8px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); min-height: 150px; display: flex; flex-direction: column; justify-content: center; font-family: sans-serif;'>
            <div style='font-size: 13px; color: #444; font-weight: 600; margin-bottom: 8px;'>{label}</div>
            <div style='font-size: 36px; font-weight: bold; color: {color};'>{value}%</div>
        </div>
    """, unsafe_allow_html=True)

# RENDER FUNCTIONS
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
        "hcp_family":   st.number_input("Family",   min_value=0, value=int(float(city_data.get("hcp_family", 0))),   key=f"{city}_hcp_family"),
        "hcp_internal": st.number_input("Internal", min_value=0, value=int(float(city_data.get("hcp_internal", 0))), key=f"{city}_hcp_internal"),
        "hcp_general":  st.number_input("General",  min_value=0, value=int(float(city_data.get("hcp_general", 0))),  key=f"{city}_hcp_general"),
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

def render_attendees_section(data, city):
    city_data = get_city_data(data, city)
    st.markdown("### TOTAL ATTENDEES EDUCATED in GX")
    attendees = st.number_input("Running Total", min_value=0, value=int(float(city_data.get("attendees_educated", 0))), key=f"{city}_attendees")
    if f"{city}_attendees" in st.session_state and st.session_state[f"{city}_attendees"] != city_data.get("attendees_educated"):
        update_value(data, city, "attendees_educated", st.session_state[f"{city}_attendees"])

def render_demographics_section(data, city):
    city_data = get_city_data(data, city)
    st.markdown("#### Demographics")
    demo_inputs = {
        "demo_black":    st.number_input("Black %",     min_value=0, max_value=100, value=int(float(city_data.get("demo_black", 0))),    key=f"{city}_demo_b"),
        "demo_hispanic": st.number_input("Hispanic %",  min_value=0, max_value=100, value=int(float(city_data.get("demo_hispanic", 0))), key=f"{city}_demo_h"),
        "demo_white":    st.number_input("White %",     min_value=0, max_value=100, value=int(float(city_data.get("demo_white", 0))),    key=f"{city}_demo_w"),
        "demo_other":    st.number_input("Other %",     min_value=0, max_value=100, value=int(float(city_data.get("demo_other", 0))),    key=f"{city}_demo_o"),
    }
    for (key, _), sk in zip(demo_inputs.items(), [f"{city}_demo_b", f"{city}_demo_h", f"{city}_demo_w", f"{city}_demo_o"]):
        if sk in st.session_state and st.session_state[sk] != city_data.get(key):
            update_value(data, city, key, st.session_state[sk])

    demo_df = pd.DataFrame({
        "Group": ["Black/African American", "Hispanic/Latino", "White/Caucasian", "Other"],
        "Percent": list(demo_inputs.values())
    })
    total = demo_df["Percent"].sum()
    if total != 100 and total > 0:
        st.warning(f"Sum: {total}%. Normalizing...")
        demo_df["Percent"] = (demo_df["Percent"] / total * 100).round(1)

    fig_demo = px.bar(demo_df, x="Percent", y="Group", orientation='h', color="Group", text="Percent")
    fig_demo.update_layout(showlegend=False, height=240, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_demo, use_container_width=True)

def render_age_gender_section(data, city):
    city_data = get_city_data(data, city)
    col_age, col_gender = st.columns(2)
    with col_age:
        st.markdown("**Age Distribution**")
        age_inputs = {
            "age_55_plus": st.number_input("55+ yrs", min_value=0, value=int(float(city_data.get("age_55_plus", 0))), key=f"{city}_age55"),
            "age_35_54":   st.number_input("35-54 yrs", min_value=0, value=int(float(city_data.get("age_35_54", 0))), key=f"{city}_age35"),
            "age_18_34":   st.number_input("18-34 yrs", min_value=0, value=int(float(city_data.get("age_18_34", 0))), key=f"{city}_age18"),
        }
        for k, sk in zip(age_inputs, [f"{city}_age55", f"{city}_age35", f"{city}_age18"]):
            if sk in st.session_state and st.session_state[sk] != city_data.get(k):
                update_value(data, city, k, st.session_state[sk])

        age_df = pd.DataFrame({"Age": ["55+ yrs", "35-54 yrs", "18-34 yrs"], "Count": list(age_inputs.values())})
        fig_age = px.pie(age_df, values="Count", names="Age", hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_age.update_traces(textposition="inside", textinfo="percent+label", textfont_size=18, pull=[0.07, 0.07, 0.07])
        fig_age.update_layout(height=560, width=560, margin=dict(l=20, r=20, t=40, b=20),
                              legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, font=dict(size=14)))
        st.plotly_chart(fig_age, use_container_width=False)

    with col_gender:
        st.markdown("**Gender**")
        male = st.number_input("Male %", min_value=0, max_value=100, value=int(float(city_data.get("gender_male", 0))), key=f"{city}_male")
        if f"{city}_male" in st.session_state and st.session_state[f"{city}_male"] != city_data.get("gender_male"):
            update_value(data, city, "gender_male", st.session_state[f"{city}_male"])
        female = 100 - male
        fig_gender = px.pie(values=[male, female], names=["Male", "Female"], hole=0.4, color_discrete_sequence=["#1f77b4", "#ff7f0e"])
        fig_gender.update_traces(textposition="inside", textinfo="percent+label", textfont_size=18, pull=[0.07, 0.07])
        fig_gender.update_layout(height=560, width=560, margin=dict(l=20, r=20, t=40, b=20),
                                 legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, font=dict(size=14)))
        st.plotly_chart(fig_gender, use_container_width=False)

def render_knowledge_intent_section(data, city):
    city_data = get_city_data(data, city)
    st.markdown("#### Knowledge / Intent")
    k1, k2, k3, k4 = st.columns(4)
    metrics = [
        ("aware_ldlc", "aware", "LDL-c<br>Awareness", "#1f77b4", "#f0f8ff", k1),
        ("understand_risk", "risk", "LDL-c Risk<br>Understanding", "#ff7f0e", "#fff8f0", k2),
        ("intent_test", "intent_test", "Intent<br>to Test", "#2ca02c", "#f0fff0", k3),
        ("intent_followup", "followup", "Intent to<br>Follow-up", "#d62728", "#fff0f0", k4),
    ]
    for dkey, skey, label, col, bg, col_obj in metrics:
        with col_obj:
            val = st.number_input(f"{label.replace('<br>', ' ')} %", min_value=0, max_value=100, value=int(float(city_data.get(dkey, 0))), key=f"{city}_{skey}", label_visibility="collapsed")
            if f"{city}_{skey}" in st.session_state and st.session_state[f"{city}_{skey}"] != city_data.get(dkey):
                update_value(data, city, dkey, st.session_state[f"{city}_{skey}"])
            render_metric_card(label, val, col, bg)

def render_ldlc_matrix(data, city):
    city_data = get_city_data(data, city)
    st.markdown("#### LDL-c (mg/dL) Distribution")
    matrix = pd.DataFrame({
        "Range": ["0-54", "55-70", "70-99", "100-139", "140-189", "≥190"],
        "Value": [city_data.get("ldlc_0_54", 0), city_data.get("ldlc_55_70", 0), city_data.get("ldlc_70_99", 0),
                  city_data.get("ldlc_100_139", 0), city_data.get("ldlc_140_189", 0), city_data.get("ldlc_190_plus", 0)]
    })

    gb = AgGrid(matrix, editable=True, fit_columns_on_grid_load=True, height=220, update_mode=GridUpdateMode.MODEL_CHANGED, data_return_mode=DataReturnMode.AS_INPUT)
    edited = gb["data"]

    total = edited["Value"].sum()
    if total != 100 and total > 0:
        edited["Value"] = (edited["Value"] / total * 100).round(2)

    range_to_key = {"0-54": "ldlc_0_54", "55-70": "ldlc_55_70", "70-99": "ldlc_70_99", "100-139": "ldlc_100_139", "140-189": "ldlc_140_189", "≥190": "ldlc_190_plus"}
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
# MAIN
# =============================================================================
def main():
    st.set_page_config(page_title="GX Activations Dashboard", layout="wide")
    data = load_data()

    st.markdown("<h1 style='text-align: center;'>GX ACTIVATIONS (CITIES) – Real-time Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("---")

    selected_city = st.selectbox("Select City", options=list(CITY_COORDS.keys()), index=0)
    col_title, col_toggle = st.columns([6, 1])
    with col_toggle:
        dark_mode = st.toggle("Dark Mode", value=False)

    refresh = st.checkbox("Auto-refresh (30s)", value=True)
    if refresh:
        time.sleep(30)
        st.rerun()

    csv_data = pd.Series({f"{city}__{k}": v for city, metrics in data.items() for k, v in metrics.items()}).to_csv().encode()
    st.download_button("Download All Cities Data", data=csv_data, file_name=f"gx_dashboard_all_cities_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")

    st.markdown("### City Activation Map")
    city_map = create_city_map(data)
    st_folium(city_map, width=700, height=400)

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

    st.caption("*All percentages reflect the percent increase from pre-survey to post-survey results.")

if __name__ == "__main__":
    main()

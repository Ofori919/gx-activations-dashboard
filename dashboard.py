import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode

# =============================================================================
# DATA MANAGEMENT
# =============================================================================
DATA_FILE = Path("gx_dashboard_data.csv")
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
    "ldlc_0_75": 0.75, "ldlc_76_125": 1.25, "ldlc_126_plus": 1.26,
}

def load_data():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE, index_col=0, header=None).squeeze("columns")
        return df.to_dict()
    return DEFAULT_DATA.copy()

def save_data(data):
    pd.Series(data).to_csv(DATA_FILE, header=False)

def update_value(data, key, value):
    data[key] = value
    save_data(data)

# =============================================================================
# UI COMPONENTS
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

# ----------------------------------------------------------------------
# HCP SECTION
# ----------------------------------------------------------------------
def render_hcp_section(data):
    st.markdown("### TOTAL HCPs EDUCATED in GX")
    hcp_educated = st.number_input("Running Total", min_value=0, value=int(float(data["hcp_educated"])), key="hcp_educated_input")
    if st.session_state.hcp_educated_input != data["hcp_educated"]:
        update_value(data, "hcp_educated", st.session_state.hcp_educated_input)

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_metric_card("Confidence<br>Diagnosing", int(float(data.get("confidence_diagnosing", 0))), "#1f77b4", "#f0f8ff")
    with c2: render_metric_card("Confidence<br>Treating", int(float(data.get("confidence_treating", 0))), "#ff7f0e", "#fff8f0")
    with c3: render_metric_card("Confidence<br>Managing", int(float(data.get("confidence_managing", 0))), "#2ca02c", "#f0fff0")
    with c4: render_metric_card("Intent<br>to Test", int(float(data.get("intent_to_test", 0))), "#d62728", "#fff0f0")

    st.markdown("#### Practice Type")
    practice_data = {
        "hcp_family":   st.number_input("Family",   min_value=0, value=int(float(data["hcp_family"])),   key="hcp_family"),
        "hcp_internal": st.number_input("Internal", min_value=0, value=int(float(data["hcp_internal"])), key="hcp_internal"),
        "hcp_general":  st.number_input("General",  min_value=0, value=int(float(data["hcp_general"])),  key="hcp_general"),
    }
    for key in practice_data:
        if st.session_state[key] != data[key]:
            update_value(data, key, st.session_state[key])

    practice_df = pd.DataFrame({
        "Type": ["Family", "Internal", "General"],
        "Count": [practice_data["hcp_family"], practice_data["hcp_internal"], practice_data["hcp_general"]]
    })
    fig_practice = px.bar(practice_df, x="Count", y="Type", orientation='h', color="Type", text="Count")
    fig_practice.update_layout(showlegend=False, height=220, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_practice, use_container_width=True)

# ----------------------------------------------------------------------
# ATTENDEES SECTION
# ----------------------------------------------------------------------
def render_attendees_section(data):
    st.markdown("### TOTAL ATTENDEES EDUCATED in GX")
    attendees = st.number_input("Running Total", min_value=0, value=int(float(data["attendees_educated"])), key="attendees")
    if st.session_state.attendees != data["attendees_educated"]:
        update_value(data, "attendees_educated", st.session_state.attendees)

def render_demographics_section(data):
    st.markdown("#### Demographics")
    demo_inputs = {
        "demo_black":    st.number_input("Black %",     min_value=0, max_value=100, value=int(float(data["demo_black"])),    key="demo_b"),
        "demo_hispanic": st.number_input("Hispanic %",  min_value=0, max_value=100, value=int(float(data["demo_hispanic"])), key="demo_h"),
        "demo_white":    st.number_input("White %",     min_value=0, max_value=100, value=int(float(data["demo_white"])),    key="demo_w"),
        "demo_other":    st.number_input("Other %",     min_value=0, max_value=100, value=int(float(data["demo_other"])),    key="demo_o"),
    }
    for (key, _), sk in zip(demo_inputs.items(), ["demo_b", "demo_h", "demo_w", "demo_o"]):
        if st.session_state[sk] != data[key]:
            update_value(data, key, st.session_state[sk])

    demo_df = pd.DataFrame({
        "Group": ["Black/African American", "Hispanic/Latino", "White/Caucasian", "Other"],
        "Percent": list(demo_inputs.values())
    })
    total = demo_df["Percent"].sum()
    if total != 100:
        st.warning(f"Sum: {total}%. Normalizing...")
        demo_df["Percent"] = (demo_df["Percent"] / total * 100).round(1)

    fig_demo = px.bar(demo_df, x="Percent", y="Group", orientation='h', color="Group", text="Percent")
    fig_demo.update_layout(showlegend=False, height=240, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_demo, use_container_width=True)

def render_age_gender_section(data):
    col_age, col_gender = st.columns(2)
    with col_age:
        st.markdown("**Age Distribution**")
        age_inputs = {
            "age_55_plus": st.number_input("55+ yrs", min_value=0, value=int(float(data.get("age_55_plus", 0))), key="age55"),
            "age_35_54":   st.number_input("35-54 yrs", min_value=0, value=int(float(data.get("age_35_54", 0))), key="age35"),
            "age_18_34":   st.number_input("18-34 yrs", min_value=0, value=int(float(data.get("age_18_34", 0))), key="age18"),
        }
        for k, sk in zip(age_inputs, ["age55", "age35", "age18"]):
            if st.session_state[sk] != data.get(k):
                update_value(data, k, st.session_state[sk])

        age_df = pd.DataFrame({"Age": ["55+ yrs", "35-54 yrs", "18-34 yrs"], "Count": list(age_inputs.values())})
        fig_age = px.pie(age_df, values="Count", names="Age", hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_age.update_traces(textposition="inside", textinfo="percent+label", textfont_size=18, pull=[0.07, 0.07, 0.07])
        fig_age.update_layout(height=560, width=560, margin=dict(l=20, r=20, t=40, b=20),
                              legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, font=dict(size=14)))
        st.plotly_chart(fig_age, use_container_width=False)

    with col_gender:
        st.markdown("**Gender**")
        male = st.number_input("Male %", min_value=0, max_value=100, value=int(float(data.get("gender_male", 0))), key="male")
        if st.session_state.male != data.get("gender_male"):
            update_value(data, "gender_male", st.session_state.male)
        female = 100 - male
        fig_gender = px.pie(values=[male, female], names=["Male", "Female"], hole=0.4, color_discrete_sequence=["#1f77b4", "#ff7f0e"])
        fig_gender.update_traces(textposition="inside", textinfo="percent+label", textfont_size=18, pull=[0.07, 0.07])
        fig_gender.update_layout(height=560, width=560, margin=dict(l=20, r=20, t=40, b=20),
                                 legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, font=dict(size=14)))
        st.plotly_chart(fig_gender, use_container_width=False)

def render_knowledge_intent_section(data):
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
            val = st.number_input(f"{label.replace('<br>', ' ')} %", min_value=0, max_value=100, value=int(float(data[dkey])), key=skey, label_visibility="collapsed")
            if st.session_state[skey] != data[dkey]:
                update_value(data, dkey, st.session_state[skey])
            render_metric_card(label, val, col, bg)

# ----------------------------------------------------------------------
# LDL-C MATRIX (ONLY ONCE!)
# ----------------------------------------------------------------------
def render_ldlc_matrix(data):
    st.markdown("#### LDL-c (mg/dL) Distribution")
    matrix = pd.DataFrame({
        "Range": ["0-54", "55-70", "70-99", "100-139", "140-189", "≥190"],
        "Value": [data["ldlc_0_54"], data["ldlc_55_70"], data["ldlc_70_99"], data["ldlc_100_139"], data["ldlc_140_189"], data["ldlc_190_plus"]]
    })
    gb = AgGrid(matrix, editable=True, fit_columns_on_grid_load=True, height=200,
                update_mode=GridUpdateMode.MODEL_CHANGED, data_return_mode=DataReturnMode.AS_INPUT)
    edited = gb["data"]
    for _, row in edited.iterrows():
        key = f"ldlc_{row['Range'].replace('≥', 'ge').replace('-', '_').lower()}"
        if key == "ldlc_ge190": key = "ldlc_190_plus"
        if key in data:
            update_value(data, key, row["Value"])

    def color_ldlc(val):
        if val <= 0.75: return "background-color: #d4edda"
        elif val <= 1.25: return "background-color: #c3e6cb"
        else: return "background-color: #bbe5b3"

    styled = edited.style.applymap(color_ldlc, subset=["Value"])
    st.table(styled)




    st.caption("*All percentages reflect the percent increase from pre-survey to post-survey results.")

# =============================================================================
# RUN (ONLY ONCE!)
# =============================================================================
if __name__ == "__main__":

    main()

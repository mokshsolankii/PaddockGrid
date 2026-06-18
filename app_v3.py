import streamlit as st
import pandas as pd
import pickle
import os
import base64
from datetime import datetime

# Set page config for a widescreen racing dashboard layout
st.set_page_config(page_title="F1 Race Predictor V3", page_icon="🏎️", layout="wide")

# Custom global UI overrides for an elite F1 Telemetry Dashboard
st.markdown(
    """
    <style>
    /* Hide Sidebar Elements completely to enforce central layout */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    
    /* Global Background and Typography */
    .stApp {
        background-color: #0F0F14 !important;
        color: #F3F4F6 !important;
    }
    h1, h2, h3, h4, p, .stMarkdown {
        text-align: center !important;
        font-family: 'Titillium Web', 'Segoe UI', sans-serif !important;
    }
    
    /* Center aligning container blocks */
    div[data-testid="stVerticalBlock"] {
        align-items: center !important;
        text-align: center !important;
    }
    
    /* Premium Minimalist 3D Podium Cards */
    [data-testid="stHorizontalBlock"] > div {
        background: #181820 !important;
        border-radius: 16px !important;
        padding: 24px 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.03) !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.45) !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    
    /* Interactive Hover Glow */
    [data-testid="stHorizontalBlock"] > div:hover {
        transform: translateY(-8px) !important;
        border-color: rgba(255, 24, 1, 0.2) !important;
        box-shadow: 0 30px 60px rgba(255, 24, 1, 0.1) !important;
    }
    
    /* Pristine Center-Aligned Driver Images */
    div[data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 20px auto !important;
        filter: drop-shadow(0 10px 15px rgba(0,0,0,0.5)) !important;
    }
    
    /* Custom Badge Styles for Positions */
    .pos-badge {
        background: #FF1801;
        color: white;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Official F1 Website Live Web URLs
OFFICIAL_F1_IMAGES = {
    "RUS": "https://media.formula1.com/content/dam/fom-website/drivers/G/GEORUS01_George_Russell/georus01.png",
    "HAM": "https://media.formula1.com/content/dam/fom-website/drivers/L/LEWHAM01_Lewis_Hamilton/lewham01.png",
    "NOR": "https://media.formula1.com/content/dam/fom-website/drivers/L/LANNOR01_Lando_Norris/lannor01.png",
    "PIA": "https://media.formula1.com/content/dam/fom-website/drivers/O/OSCPIA01_Oscar_Piastri/oscpia01.png",
    "LEC": "https://media.formula1.com/content/dam/fom-website/drivers/C/CHALEC01_Charles_Leclerc/chalec01.png",
    "VER": "https://media.formula1.com/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png",
    "GAS": "https://media.formula1.com/content/dam/fom-website/drivers/P/PIEGAS01_Pierre_Gasly/piegas01.png",
    "COL": "https://media.formula1.com/content/dam/fom-website/drivers/F/FRACOL01_Franco_Colapinto/fracol01.png",
    "LAW": "https://media.formula1.com/content/dam/fom-website/drivers/L/LIALAW01_Liam_Lawson/lialaw01.png",
    "BEA": "https://media.formula1.com/content/dam/fom-website/drivers/O/OLIBEA01_Oliver_Bearman/olibea01.png",
    "OCO": "https://media.formula1.com/content/dam/fom-website/drivers/E/ESTOCO01_Esteban_Ocon/estoco01.png",
    "SAI": "https://media.formula1.com/content/dam/fom-website/drivers/C/CARSAI01_Carlos_Sainz/carsai01.png",
    "HUL": "https://media.formula1.com/content/dam/fom-website/drivers/N/NICHUL01_Nico_Hulkenberg/nichul01.png",
    "BOR": "https://media.formula1.com/content/dam/fom-website/drivers/G/GABBOR01_Gabriel_Bortoleto/gabbor01.png",
    "ALO": "https://media.formula1.com/content/dam/fom-website/teams/Aston-Martin-Aramco-F1-Team/Logo.png",
    "STR": "https://media.formula1.com/content/dam/fom-website/drivers/L/LANSTR01_Lance_Stroll/lanstr01.png",
    "PER": "https://media.formula1.com/content/dam/fom-website/drivers/S/SERPER01_Sergio_Perez/serper01.png",
    "BOT": "https://media.formula1.com/content/dam/fom-website/drivers/V/VALBOT01_Valtteri_Bottas/valbot01.png",
}

TEAM_COLORS = {
    "Mercedes": "#27F4D2", "Ferrari": "#E8002D", "McLaren": "#FF8000", "Red Bull Racing": "#3671C6",
    "BWT Alpine F1 Team": "#FF87BC", "Visa Cash App Racing Bulls F1 Team": "#66C2FF", "TGR Haas F1 Team": "#B6BABD",
    "Atlassian Williams F1 Team": "#37BEDD", "Audi Revolut F1 Team": "#780016", "Aston Martin Aramco F1 Team": "#229971",
    "Cadillac F1 Team": "#FCE300", "Unknown": "#FFFFFF"
}

TEAM_LOGOS = {
    "Mercedes": "team_logos/mercedes.png",
    "Ferrari": "team_logos/ferrari.png",
    "McLaren": "team_logos/mclaren.png",
    "Red Bull Racing": "team_logos/redbull.png",
    "BWT Alpine F1 Team": "team_logos/alpine.png",
    "Visa Cash App Racing Bulls F1 Team": "team_logos/rb.png",
    "TGR Haas F1 Team": "team_logos/haas.png",
    "Atlassian Williams F1 Team": "team_logos/williams.png",
    "Aston Martin Aramco F1 Team": "team_logos/astonmartin.png",
    "Audi Revolut F1 Team": "team_logos/audi.png",
    "Cadillac F1 Team": "team_logos/cadillac.png",
    "Unknown": "team_logos/Unknown.png"
}

def get_base64_image(image_path):
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            return f"data:image/png;base64,{encoded}"
        except Exception:
            pass
    return ""

@st.cache_resource
def load_model_bundle():
    model_path = "f1_model_v3.pkl"
    if not os.path.exists(model_path): return None
    with open(model_path, "rb") as f: return pickle.load(f)

bundle = load_model_bundle()
if bundle is None:
    st.error("❌ f1_model_v3.pkl not found!")
    st.stop()

model, ALL_FEATURES = bundle["model"], bundle["features"]

# --- UI Header ---
st.markdown("<h1 style='color: #FF1801; font-family: sans-serif; margin-top: -20px;'>🏎️ Formula 1 Race Outcome Predictor V3</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1em; color: #BBBBBB;'>Powered by CatBoost & Dynamic Rolling Form Analytics</p>", unsafe_allow_html=True)
st.markdown("---")

year = 2026

# Exact calibrated calendar dataset structure extracted from image_fcfbb8.png
F1_2026_SCHEDULE = [
    {"round": 1, "race": "Australia", "date_str": "06-08 MAR", "date": datetime(2026, 3, 8)},
    {"round": 2, "race": "China", "date_str": "13-15 MAR", "date": datetime(2026, 3, 15)},
    {"round": 3, "race": "Japan", "date_str": "27-29 MAR", "date": datetime(2026, 3, 29)},
    {"round": 4, "race": "Bahrain", "date_str": "10-12 APR", "date": datetime(2026, 4, 12)},
    {"round": 5, "race": "Saudi Arabia", "date_str": "17-19 APR", "date": datetime(2026, 4, 19)},
    {"round": 6, "race": "Miami", "date_str": "01-03 MAY", "date": datetime(2026, 5, 3)},
    {"round": 7, "race": "Canada", "date_str": "22-24 MAY", "date": datetime(2026, 5, 24)},
    {"round": 8, "race": "Monaco", "date_str": "05-07 JUN", "date": datetime(2026, 6, 7)},
    {"round": 9, "race": "Spain (Barcelona)", "date_str": "12-14 JUN", "date": datetime(2026, 6, 14)},
    {"round": 10, "race": "Austria", "date_str": "26-28 JUN", "date": datetime(2026, 6, 28)},
    {"round": 11, "race": "Great Britain", "date_str": "03-05 JUL", "date": datetime(2026, 7, 5)},
    {"round": 12, "race": "Belgium", "date_str": "17-19 JUL", "date": datetime(2026, 7, 19)},
    {"round": 13, "race": "Hungary", "date_str": "24-26 JUL", "date": datetime(2026, 7, 26)},
    {"round": 14, "race": "Netherlands", "date_str": "21-23 AUG", "date": datetime(2026, 8, 23)},
    {"round": 15, "race": "Italy", "date_str": "04-06 SEP", "date": datetime(2026, 9, 6)},
    {"round": 16, "race": "Spain (Madrid)", "date_str": "11-13 SEP", "date": datetime(2026, 9, 13)},
    {"round": 17, "race": "Azerbaijan", "date_str": "24-26 SEP", "date": datetime(2026, 9, 26)},
    {"round": 18, "race": "Singapore", "date_str": "09-11 OCT", "date": datetime(2026, 10, 11)},
    {"round": 19, "race": "United States", "date_str": "23-25 OCT", "date": datetime(2026, 10, 25)},
    {"round": 20, "race": "Mexico", "date_str": "30 OCT - 01 NOV", "date": datetime(2026, 11, 1)},
    {"round": 21, "race": "Brazil", "date_str": "06-08 NOV", "date": datetime(2026, 11, 8)},
    {"round": 22, "race": "Las Vegas", "date_str": "19-21 NOV", "date": datetime(2026, 11, 21)},
    {"round": 23, "race": "Qatar", "date_str": "27-29 NOV", "date": datetime(2026, 11, 29)},
    {"round": 24, "race": "Abu Dhabi", "date_str": "04-06 DEC", "date": datetime(2026, 12, 6)},
]

# Real-time Auto Detection Engine (Strict upcoming gap mapping logic)
current_date = datetime.now()
next_race_name = "Austria"
next_race_date_str = "26-28 JUN"
default_index = 9

for i, event in enumerate(F1_2026_SCHEDULE):
    if event["date"] >= current_date:
        next_race_name = event["race"]
        next_race_date_str = event["date_str"]
        default_index = i
        break

# Map plain string array for seamless dropdown choice mappings
races_list = [f"Round {e['round']}: {e['race']}" for e in F1_2026_SCHEDULE]

# --- Perfectly Connected Center Layout Columns ---
container_cols = st.columns([1.5, 2.5, 2.5, 1.5])

with container_cols[1]:
    selected_race_box = st.selectbox("Select Grand Prix", races_list, index=default_index)
    race_name = F1_2026_SCHEDULE[races_list.index(selected_race_box)]["race"]

with container_cols[2]:
    st.markdown(f"""
    <div style='background: #14141C; padding: 6px 14px; border-radius: 8px; border-left: 4px solid #FF1801; text-align: left !important; height: 58px; box-shadow: 0 4px 15px rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.02);'>
        <span style='color: #888888; font-size: 0.72em; text-transform: uppercase;'>Upcoming Live Weekend</span><br>
        <strong style='color: #FFFFFF; font-size: 0.95em; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>🎯 {next_race_name}</strong>
        <span style='color: #FF1801; font-size: 0.8em; font-weight: bold;'>📅 {next_race_date_str}</span>
    </div>
    """, unsafe_allow_html=True)

# Generate Button Row
btn_cols = st.columns([2.5, 3, 2.5])
with btn_cols[1]:
    trigger_prediction = st.button("🔮 Generate Grid Prediction", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

def get_driver_image(driver_code):
    local_path = f"drivers_images/{driver_code}.png"
    if os.path.exists(local_path):
        return local_path
    return OFFICIAL_F1_IMAGES.get(driver_code, "https://media.formula1.com/d_driver_fallback_image.png")

if trigger_prediction:
    with st.spinner("Processing prediction..."):
        try:
            import predict_race_v3
            pred_df = predict_race_v3.predict_race(year, race_name, None)
        except Exception as e:
            st.error(f"Failed to execute prediction pipeline: {e}")
            st.stop()

        if pred_df is None or pred_df.empty:
            st.warning("No data returned.")
        else:
            st.markdown("### 🏆 Predicted Podium")
            podium_cols = st.columns(3)
            
            # P2 (Left Card)
            if len(pred_df) > 1:
                p2_row = pred_df.iloc[1]
                p2_img = get_driver_image(p2_row['driver'])
                p2_color = TEAM_COLORS.get(p2_row['team'], "#FFFFFF")
                p2_logo_path = TEAM_LOGOS.get(p2_row['team'], "team_logos/Unknown.png")
                p2_base64 = get_base64_image(p2_logo_path)
                with podium_cols[0]:
                    st.markdown("<div style='border-top: 4px solid #C0C0C0; padding-top: 10px; margin-bottom: 15px;'><span class='pos-badge' style='background:#C0C0C0; color:#111;'>🥈 P2</span></div>", unsafe_allow_html=True)
                    st.image(p2_img, width=170)
                    st.markdown(f"### {p2_row['_name']}")
                    
                    logo_html = f"<img src='{p2_base64}' width='25'/>" if p2_base64 else ""
                    st.markdown(f"<div style='display: flex; align-items: center; justify-content: center; gap: 8px;'>{logo_html}<div style='border-left: 4px solid {p2_color}; padding-left: 8px; color: #AAAAAA; font-weight: 500;'>{p2_row['team']}</div></div>", unsafe_allow_html=True)

            # P1 (Center Card Winner)
            if len(pred_df) > 0:
                p1_row = pred_df.iloc[0]
                p1_img = get_driver_image(p1_row['driver'])
                p1_color = TEAM_COLORS.get(p1_row['team'], "#FFFFFF")
                p1_logo_path = TEAM_LOGOS.get(p1_row['team'], "team_logos/Unknown.png")
                p1_base64 = get_base64_image(p1_logo_path)
                with podium_cols[1]:
                    st.markdown("<div style='border-top: 4px solid #FFD700; padding-top: 10px; margin-bottom: 15px;'><span class='pos-badge' style='background:#FFD700; color:#111;'>🏆 WINNER</span></div>", unsafe_allow_html=True)
                    st.image(p1_img, width=210)
                    st.markdown(f"<h2>{p1_row['_name']}</h2>", unsafe_allow_html=True)
                    
                    logo_html = f"<img src='{p1_base64}' width='30'/>" if p1_base64 else ""
                    st.markdown(f"<div style='display: flex; align-items: center; justify-content: center; gap: 8px;'>{logo_html}<div style='border-left: 4px solid {p1_color}; padding-left: 8px; color: #FFFFFF; font-weight: bold;'>{p1_row['team']}</div></div>", unsafe_allow_html=True)

            # P3 (Right Card)
            if len(pred_df) > 2:
                p3_row = pred_df.iloc[2]
                p3_img = get_driver_image(p3_row['driver'])
                p3_color = TEAM_COLORS.get(p3_row['team'], "#FFFFFF")
                p3_logo_path = TEAM_LOGOS.get(p3_row['team'], "team_logos/Unknown.png")
                p3_base64 = get_base64_image(p3_logo_path)
                with podium_cols[2]:
                    st.markdown("<div style='border-top: 4px solid #CD7F32; padding-top: 10px; margin-bottom: 15px;'><span class='pos-badge' style='background:#CD7F32; color:#111;'>🥉 P3</span></div>", unsafe_allow_html=True)
                    st.image(p3_img, width=170)
                    st.markdown(f"### {p3_row['_name']}")
                    
                    logo_html = f"<img src='{p3_base64}' width='25'/>" if p3_base64 else ""
                    st.markdown(f"<div style='display: flex; align-items: center; justify-content: center; gap: 8px;'>{logo_html}<div style='border-left: 4px solid {p3_color}; padding-left: 8px; color: #AAAAAA; font-weight: 500;'>{p3_row['team']}</div></div>", unsafe_allow_html=True)

            st.markdown("<br><h3 style='margin-top: 25px;'>🏁 Full Predicted Grid Standing</h3>", unsafe_allow_html=True)
            st.markdown("---")
            
            table_container_width = [1, 2, 4, 2]
            h_cols = st.columns(table_container_width)
            h_cols[0].markdown("**Pos**")
            h_cols[1].markdown("**Driver Name**")
            h_cols[2].markdown("**Team Lineup**")
            h_cols[3].markdown("**Starting Grid**")
            st.markdown("---")
            
            for idx, row in pred_df.iterrows():
                pos = f"P{row['predicted_position']}"
                driver_name = row['_name']
                team_name = row['team']
                start_grid = f"Grid: {int(row['grid_position'])}"
                
                team_color = TEAM_COLORS.get(team_name, "#FFFFFF")
                t_logo_path = TEAM_LOGOS.get(team_name, "team_logos/Unknown.png")
                t_base64 = get_base64_image(t_logo_path)
                
                row_cols = st.columns(table_container_width)
                
                row_cols[0].markdown(f"**{pos}**")
                row_cols[1].markdown(driver_name)
                
                logo_html = f"<img src='{t_base64}' width='24'/>" if t_base64 else ""
                team_stripe_html = f"<div style='border-left: 6px solid {team_color}; padding-left: 12px; font-weight: 500; height: 30px; display: flex; align-items: center; gap: 10px; color: #EEEEEE; justify-content: center;'>{logo_html}{team_name}</div>"
                row_cols[2].markdown(team_stripe_html, unsafe_allow_html=True)
                
                row_cols[3].markdown(start_grid)
                
            st.success(f"📊 Prediction output processed cleanly.")

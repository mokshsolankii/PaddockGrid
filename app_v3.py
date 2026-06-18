import streamlit as st
import pandas as pd
import pickle
import os
import base64

# Set page config for a widescreen racing dashboard layout
st.set_page_config(page_title="F1 Race Predictor V3", page_icon="🏎️", layout="wide")

# Custom global UI overrides for an elite F1 Telemetry Dashboard
st.markdown(
    """
    <style>
    /* Global Background and Typography */
    .stApp {
        background-color: #0F0F14 !important;
        color: #F3F4F6 !important;
    }
    h1, h2, h3, h4, p, .stMarkdown {
        text-align: center !important;
        font-family: 'Titillium Web', 'Segoe UI', sans-serif !important;
    }
    
    /* Global Center Alignment for Columns */
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
    "Unknown": "team_logos/unknown.png"
}

# Helper function to convert local image to inline safe Base64 source
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
st.markdown("<h1 style='color: #FF1801; font-family: sans-serif;'>🏎️ Formula 1 Race Outcome Predictor V3</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1em; color: #BBBBBB;'>Powered by CatBoost & Dynamic Rolling Form Analytics</p>", unsafe_allow_html=True)
st.markdown("---")

st.sidebar.header("🔧 Race Configuration")
year = st.sidebar.selectbox("Select Year", [2026, 2025, 2024])

@st.cache_data
def get_available_races():
    try:
        df = pd.read_csv("f1_training_data_v3.csv")
        return sorted(df["race"].unique())
    except Exception:
        return ["Austria", "Monaco", "British", "Belgium", "Bahrain", "Singapore"]

available_races = get_available_races()
race_name = st.sidebar.selectbox("Select Grand Prix", available_races)
round_num = st.sidebar.number_input("Round Number (Optional)", min_value=1, max_value=25, value=8)

def get_driver_image(driver_code):
    local_path = f"drivers_images/{driver_code}.png"
    if os.path.exists(local_path):
        return local_path
    return OFFICIAL_F1_IMAGES.get(driver_code, "https://media.formula1.com/d_driver_fallback_image.png")

if st.sidebar.button("🔮 Generate Grid Prediction", use_container_width=True):
    with st.spinner("Processing prediction..."):
        try:
            import predict_race_v3
            pred_df = predict_race_v3.predict_race(year, race_name, round_num)
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
                p2_logo_path = TEAM_LOGOS.get(p2_row['team'], TEAM_LOGOS["Unknown"])
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
                p1_logo_path = TEAM_LOGOS.get(p1_row['team'], TEAM_LOGOS["Unknown"])
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
                p3_logo_path = TEAM_LOGOS.get(p3_row['team'], TEAM_LOGOS["Unknown"])
                p3_base64 = get_base64_image(p3_logo_path)
                with podium_cols[2]:
                    st.markdown("<div style='border-top: 4px solid #CD7F32; padding-top: 10px; margin-bottom: 15px;'><span class='pos-badge' style='background:#CD7F32; color:#111;'>🥉 P3</span></div>", unsafe_allow_html=True)
                    st.image(p3_img, width=170)
                    st.markdown(f"### {p3_row['_name']}")
                    
                    logo_html = f"<img src='{p3_base64}' width='25'/>" if p3_base64 else ""
                    st.markdown(f"<div style='display: flex; align-items: center; justify-content: center; gap: 8px;'>{logo_html}<div style='border-left: 4px solid {p3_color}; padding-left: 8px; color: #AAAAAA; font-weight: 500;'>{p3_row['team']}</div></div>", unsafe_allow_html=True)

            st.markdown("<br><h3 style='text-align: left !important; margin-top: 25px;'>🏁 Full Predicted Grid Standing</h3>", unsafe_allow_html=True)
            st.markdown("---")
            
            h_cols = st.columns([1, 2, 4, 2])
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
                t_logo_path = TEAM_LOGOS.get(team_name, TEAM_LOGOS["Unknown"])
                t_base64 = get_base64_image(t_logo_path)
                
                row_cols = st.columns([1, 2, 4, 2])
                
                row_cols[0].markdown(f"**{pos}**")
                row_cols[1].markdown(driver_name)
                
                logo_html = f"<img src='{t_base64}' width='24'/>" if t_base64 else ""
                team_stripe_html = f"<div style='border-left: 6px solid {team_color}; padding-left: 12px; font-weight: 500; height: 30px; display: flex; align-items: center; gap: 10px; color: #EEEEEE;'>{logo_html}{team_name}</div>"
                row_cols[2].markdown(team_stripe_html, unsafe_allow_html=True)
                
                row_cols[3].markdown(start_grid)
                
            st.success(f"📊 Prediction output processed cleanly.")
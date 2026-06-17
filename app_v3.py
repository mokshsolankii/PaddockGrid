import streamlit as st
import pandas as pd
import pickle
import os

# Set page config for a widescreen racing dashboard layout
st.set_page_config(page_title="F1 Race Predictor V3", page_icon="🏎️", layout="wide")

# Custom global padding layout overrides to force center-alignment universally
st.markdown(
    """
    <style>
    h1, h2, h3, h4, p, .stMarkdown {
        text-align: center !important;
    }
    div[data-testid="stVerticalBlock"] {
        align-items: center !important;
        text-align: center !important;
    }
    div[data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0 auto !important;
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
    "ALO": "https://media.formula1.com/content/dam/fom-website/drivers/F/FERALO01_Fernando_Alonso/feralo01.png",
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

# Helper function to smart-route image paths
def get_driver_image(driver_code):
    local_path = f"drivers_images/{driver_code}.png"
    # If manually downloaded local file exists, use it first
    if os.path.exists(local_path):
        return local_path
    # Otherwise fallback to official web link or global silhouette avatar
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
                with podium_cols[0]:
                    st.markdown("#### 🥈 2nd Place")
                    st.image(p2_img, width=170)
                    st.markdown(f"### {p2_row['_name']}")
                    st.markdown(f"<div style='display: inline-block; border-left: 4px solid {p2_color}; padding-left: 8px; color: #AAAAAA; font-weight: 500;'>{p2_row['team']}</div>", unsafe_allow_html=True)

            # P1 (Center Card Winner)
            if len(pred_df) > 0:
                p1_row = pred_df.iloc[0]
                p1_img = get_driver_image(p1_row['driver'])
                p1_color = TEAM_COLORS.get(p1_row['team'], "#FFFFFF")
                with podium_cols[1]:
                    st.markdown("<h3 style='color: #FFD700; margin-bottom: 5px;'>🥇 WINNER</h3>", unsafe_allow_html=True)
                    st.image(p1_img, width=210)
                    st.markdown(f"<h2>{p1_row['_name']}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<div style='display: inline-block; border-left: 4px solid {p1_color}; padding-left: 8px; color: #FFFFFF; font-weight: bold;'>{p1_row['team']}</div>", unsafe_allow_html=True)

            # P3 (Right Card)
            if len(pred_df) > 2:
                p3_row = pred_df.iloc[2]
                p3_img = get_driver_image(p3_row['driver'])
                p3_color = TEAM_COLORS.get(p3_row['team'], "#FFFFFF")
                with podium_cols[2]:
                    st.markdown("#### 🥉 3rd Place")
                    st.image(p3_img, width=170)
                    st.markdown(f"### {p3_row['_name']}")
                    st.markdown(f"<div style='display: inline-block; border-left: 4px solid {p3_color}; padding-left: 8px; color: #AAAAAA; font-weight: 500;'>{p3_row['team']}</div>", unsafe_allow_html=True)

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
                row_cols = st.columns([1, 2, 4, 2])
                
                row_cols[0].markdown(f"**{pos}**")
                row_cols[1].markdown(driver_name)
                
                team_stripe_html = f"<div style='border-left: 6px solid {team_color}; padding-left: 12px; font-weight: 500; height: 24px; display: flex; align-items: center; color: #EEEEEE;'>{team_name}</div>"
                row_cols[2].markdown(team_stripe_html, unsafe_allow_html=True)
                
                row_cols[3].markdown(start_grid)
                
            st.success(f"📊 Prediction output processed cleanly.")
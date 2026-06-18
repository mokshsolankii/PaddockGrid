import streamlit as st
import pandas as pd
import pickle
import os
import base64
from datetime import datetime

@st.cache_data(ttl=3600)  # Data stays cached for 1 hour so the app remains blazing fast
def fetch_live_wdc_standings():
    try:
        # Fetching current real-time standings directly from the Live API
        url = "http://ergast.com/api/f1/current/driverStandings.json"
        df_list = pd.read_json(url)
        standings_lists = df_list["MRData"]["StandingsTable"]["StandingsList"][0]["DriverStandings"]
        
        pos_list, driver_list, team_list, points_list = [], [], [], []
        
        for item in standings_lists:
            pos_list.append(int(item["position"]))
            # Formatting Name: GivenName FamilyName
            d_name = f"{item['Driver']['givenName']} {item['Driver']['familyName']}"
            driver_list.append(d_name)
            # Fetching constructor name smoothly
            team_list.append(item["Constructors"][0]["name"])
            points_list.append(float(item["points"]))
            
        return pd.DataFrame({
            "Pos": pos_list,
            "Driver": driver_list,
            "Team": team_list,
            "Points": points_list
        })
    except Exception as e:
        # Fixed strict length array symmetry matching exactly 20 elements
        return pd.DataFrame({
            "Pos": list(range(1, 21)),
            "Driver": [
                "Kimi Antonelli", "Lewis Hamilton", "George Russell", "Charles Leclerc", "Lando Norris",
                "Max Verstappen", "Oscar Piastri", "Carlos Sainz", "Pierre Gasly", "Fernando Alonso",
                "Esteban Ocon", "Alexander Albon", "Lance Stroll", "Yuki Tsunoda", "Oliver Bearman",
                "Nico Hulkenberg", "Liam Lawson", "Gabriel Bortoleto", "Jack Doohan", "Franco Colapinto"
            ],
            "Team": [
                "Mercedes", "Ferrari", "Mercedes", "Ferrari", "McLaren",
                "Red Bull Racing", "McLaren", "Williams", "Alpine", "Aston Martin",
                "Haas", "Williams", "Aston Martin", "Racing Bulls", "Haas",
                "Audi", "Racing Bulls", "Audi", "Alpine", "Red Bull Racing"
            ],
            "Points": [156, 115, 106, 75, 73, 70, 65, 48, 32, 28, 18, 12, 10, 8, 6, 4, 2, 0, 0, 0]
        })

# Set page config for a widescreen racing dashboard layout
st.set_page_config(page_title="PaddockPulse", page_icon="🏎️", layout="wide")

# Custom global UI overrides for an elite F1 Telemetry Dashboard
st.markdown(
    """
    <style>
    /* Hide Sidebar Elements completely to enforce central layout */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    
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
        padding: 20px 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.03) !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.45) !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    [data-testid="stHorizontalBlock"] > div:hover {
        transform: translateY(-5px) !important;
        border-color: rgba(255, 24, 1, 0.2) !important;
    }
    
    /* Pristine Center-Aligned Driver Images */
    div[data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 15px auto !important;
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

    /* Style override for popover telemetry cards to look like native blocks with glow */
    div[data-testid="stPopover"] {
        width: 100% !important;
    }
    div[data-testid="stPopover"] > button {
        background: transparent !important;
        color: #F3F4F6 !important;
        border: 1px solid rgba(255, 255, 255, 0.03) !important;
        border-radius: 16px !important;
        padding: 12px 16px !important;
        width: 100% !important;
        text-align: center !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.45) !important;
        font-size: 1.1em !important;
        font-weight: 500 !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    div[data-testid="stPopover"] > button:hover {
        transform: translateY(-5px) !important;
        border-color: rgba(255, 24, 1, 0.5) !important;
        box-shadow: 0 0 20px rgba(255, 24, 1, 0.2) !important;
    }
    
    /* Inline content text styling inside cards */
    .card-text {
        color: #F3F4F6;
        font-size: 1.1em;
        font-weight: 500;
        margin: 0;
        padding: 10px 0;
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
}

TEAM_COLORS = {
    "Mercedes": "#27F4D2", "Ferrari": "#E8002D", "McLaren": "#FF8000", "Red Bull Racing": "#3671C6",
    "BWT Alpine F1 Team": "#FF87BC", "Visa Cash App Racing Bulls F1 Team": "#66C2FF", "TGR Haas F1 Team": "#B6BABD",
}

# Dynamic Track Shapes Database
TRACK_METRICS = {
    "Australia": {"name": "Albert Park Circuit", "weather": "☀️ Sunny | Track Temp: 34°C"},
    "China": {"name": "Shanghai Circuit", "weather": "☁️ Overcast | Track Temp: 22°C"},
    "Japan": {"name": "Suzuka Racing Course", "weather": "☀️ Clear | Track Temp: 29°C"},
    "Bahrain": {"name": "Bahrain Circuit", "weather": "🌙 Night Race | Track Temp: 27°C"},
    "Saudi Arabia": {"name": "Jeddah Corniche", "weather": "🌙 Night Race | Track Temp: 28°C"},
    "Miami": {"name": "Miami Autodrome", "weather": "🌤️ Humid | Track Temp: 41°C"},
    "Canada": {"name": "Circuit Gilles-Villeneuve", "weather": "🌤️ Breezy | Track Temp: 26°C"},
    "Monaco": {"name": "Circuit de Monaco", "weather": "☀️ Clear | Track Temp: 32°C"},
    "Spain (Barcelona)": {"name": "Circuit de Catalunya", "weather": "☀️ Hot | Track Temp: 39°C"},
    "Austria": {"name": "Red Bull Ring (Spielberg)", "weather": "🌤️ Part Cloud | Track Temp: 28°C"},
    "Great Britain": {"name": "Silverstone Circuit", "weather": "🌧️ Light Drizzle | Track Temp: 19°C"},
    "Belgium": {"name": "Spa-Francorchamps", "weather": "☁️ Cloudy | Track Temp: 18°C"}
}

@st.cache_resource
def load_model_bundle():
    model_path = "f1_model_v3.pkl"
    if not os.path.exists(model_path): return None
    with open(model_path, "rb") as f: return pickle.load(f)

bundle = load_model_bundle()
if bundle is None: st.stop()
model, ALL_FEATURES = bundle["model"], bundle["features"]

# --- Brand New Title Header Branding ---
st.markdown("<h1 style='color: #FF1801; font-family: sans-serif; margin-top: -20px; letter-spacing: 1px;'>🏎️ PaddockPulse V3</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.15em; color: #BBBBBB; font-style: italic;'>Predictive Telemetry & Rolling Analytics • Straight From The Pit Lane</p>", unsafe_allow_html=True)
st.markdown("---")

year = 2026

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
]

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

races_list = [f"Round {e['round']}: {e['race']}" for e in F1_2026_SCHEDULE]

# =====================================================================
# 🏁 ROW 1: 4 COLUMNS
# =====================================================================
row1_cols = st.columns(4)

with row1_cols[0]:
    # Pull dynamic real-time data from cache/API
    live_wdc_df = fetch_live_wdc_standings()
    
    # Safely extract leader info (fallback if empty)
    leader_name = live_wdc_df.iloc[0]["Driver"] if not live_wdc_df.empty else "Kimi Antonelli"
    leader_team = live_wdc_df.iloc[0]["Team"] if not live_wdc_df.empty else "Mercedes"
    
    # Custom HTML styling for layout alignment inside the button card
    wdc_leader_html = f"""
    <div style='display: flex; justify-content: space-between; align-items: center; width: 100%; text-align: left !important; min-height: 58px;'>
        <div style='text-align: left !important;'>
            <span style='color: #FF1801; font-size: 0.72em; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;'>WDC Standings</span>
            <h3 style='margin: 1px 0 !important; color: #FFFFFF; font-size: 1.05em; font-weight: 700; text-align: left !important; white-space: nowrap;'>{leader_name}</h3>
            <span style='color: #888888; font-size: 0.8em; font-weight: 500;'>{leader_team}</span>
        </div>
        <div style='display: flex; align-items: center;'>
            <img src='https://media.formula1.com/content/dam/fom-website/drivers/K/KIMANT01_Kimi_Antonelli/kimant01.png' 
                 style='height: 52px; width: auto; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.5)); margin-left: 4px;' />
        </div>
    </div>
    """
    
    with st.popover(wdc_leader_html, use_container_width=True):
        st.markdown("<h3 style='color:#FF1801; text-align: center;'>🏆 Live Drivers Championship Standings</h3>", unsafe_allow_html=True)
        st.markdown("---")
        st.dataframe(
            live_wdc_df.set_index("Pos"), 
            use_container_width=True,
            column_config={
                "Driver": st.column_config.TextColumn("Driver Profile"),
                "Team": st.column_config.TextColumn("Constructor/Team"),
                "Points": st.column_config.NumberColumn("Total Points", format="%d 🏁")
            }
        )

with row1_cols[1]:
    selected_race_box = st.selectbox("Select Grand Prix", races_list, index=default_index)
    race_name = F1_2026_SCHEDULE[races_list.index(selected_race_box)]["race"]

with row1_cols[2]:
    st.markdown(f"""
    <div style='background: #14141C; padding: 6px 14px; border-radius: 8px; border-left: 4px solid #FF1801; text-align: left !important; height: 58px; box-shadow: 0 4px 15px rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.02); line-height: 1.3;'>
        <span style='color: #888888; font-size: 0.7em; text-transform: uppercase;'>Upcoming Live Weekend</span><br>
        <strong style='color: #FFFFFF; font-size: 0.9em; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>🎯 {next_race_name}</strong>
        <span style='color: #FF1801; font-size: 0.75em; font-weight: bold;'>📅 {next_race_date_str}</span>
    </div>
    """, unsafe_allow_html=True)

with row1_cols[3]:
    with st.popover("Constructor standing"):
        st.markdown("<h4 style='color:#FF1801;'>🏁 Constructors Championship Standings</h4>", unsafe_allow_html=True)
        wcc_data = pd.DataFrame({
            "Pos": [1, 2, 3, 4],
            "Team": ["Mercedes", "Ferrari", "McLaren", "Red Bull Racing"],
            "Points": [262, 190, 141, 89]
        })
        st.table(wcc_data.set_index("Pos"))

st.markdown("<br>", unsafe_allow_html=True)

# =====================================================================
# 🏁 ROW 2: 3 COLUMNS
# =====================================================================
row2_cols = st.columns(3)

with row2_cols[0]:
    track_info = TRACK_METRICS.get(race_name, {"name": "F1 Grand Prix Track", "weather": "Fetching Live Status..."})
    st.markdown(f"""
    <div style='text-align: center; background: #14141C; padding: 8px; border-radius: 8px; height: 58px; border: 1px solid rgba(255,255,255,0.02); box-shadow: 0 4px 15px rgba(0,0,0,0.25);'>
        <div style='font-size: 1.05em; font-weight: 600; color: #FFF; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>🗺️ {track_info['name']}</div>
        <div style='color: #888888; font-size: 0.85em;'>{track_info['weather']}</div>
    </div>
    """, unsafe_allow_html=True)

with row2_cols[1]:
    trigger_prediction = st.button("🔮 Generate Grid Prediction", use_container_width=True)

with row2_cols[2]:
    with st.popover("Last race result"):
        st.markdown("<h4 style='color:#FF1801;'>🏁 AWS Gran Premio de España Result</h4>", unsafe_allow_html=True)
        st.markdown("**1st:** Lewis Hamilton (Ferrari)<br>**2nd:** George Russell (Mercedes)<br>**3rd:** Lando Norris (McLaren)", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

def get_driver_image(driver_code):
    local_path = f"drivers_images/{driver_code}.png"
    if os.path.exists(local_path): return local_path
    return OFFICIAL_F1_IMAGES.get(driver_code, "https://media.formula1.com/d_driver_fallback_image.png")

# Execution Output Block
if trigger_prediction:
    with st.spinner("Processing prediction..."):
        try:
            import predict_race_v3
            pred_df = predict_race_v3.predict_race(2026, race_name, None)
        except Exception as e:
            st.error(f"Failed to execute prediction pipeline: {e}")
            st.stop()

        if pred_df is None or pred_df.empty:
            st.warning("No data returned.")
        else:
            st.markdown("### 🏆 Predicted Podium")
            podium_cols = st.columns(3)
            
            if len(pred_df) > 1:
                p2_row = pred_df.iloc[1]
                with podium_cols[0]:
                    st.markdown("<div><span class='pos-badge' style='background:#C0C0C0; color:#111;'>🥈 P2</span></div>", unsafe_allow_html=True)
                    st.image(get_driver_image(p2_row['driver']), width=170)
                    st.markdown(f"### {p2_row['_name']}")
                    st.markdown(f"<div style='color: #AAAAAA; font-weight: 500;'>{p2_row['team']}</div>", unsafe_allow_html=True)

            if len(pred_df) > 0:
                p1_row = pred_df.iloc[0]
                with podium_cols[1]:
                    st.markdown("<div><span class='pos-badge' style='background:#FFD700; color:#111;'>🏆 WINNER</span></div>", unsafe_allow_html=True)
                    st.image(get_driver_image(p1_row['driver']), width=210)
                    st.markdown(f"<h2>{p1_row['_name']}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<div style='color: #FFFFFF; font-weight: bold;'>{p1_row['team']}</div>", unsafe_allow_html=True)

            if len(pred_df) > 2:
                p3_row = pred_df.iloc[2]
                with podium_cols[2]:
                    st.markdown("<div><span class='pos-badge' style='background:#CD7F32; color:#111;'>🥉 P3</span></div>", unsafe_allow_html=True)
                    st.image(get_driver_image(p3_row['driver']), width=170)
                    st.markdown(f"### {p3_row['_name']}")
                    st.markdown(f"<div style='color: #AAAAAA; font-weight: 500;'>{p3_row['team']}</div>", unsafe_allow_html=True)

            st.markdown("<br><h3 style='margin-top: 25px;'>🏁 Full Predicted Grid Standing</h3>", unsafe_allow_html=True)
            st.markdown("---")
            
            table_container_width = [1, 2, 4, 2]
            for idx, row in pred_df.iterrows():
                row_cols = st.columns(table_container_width)
                row_cols[0].markdown(f"**P{row['predicted_position']}**")
                row_cols[1].markdown(row['_name'])
                row_cols[2].markdown(f"<div style='border-left: 6px solid {TEAM_COLORS.get(row['team'], '#FFFFFF')}; padding-left: 12px;'>{row['team']}</div>", unsafe_allow_html=True)
                row_cols[3].markdown(f"Grid: {int(row['grid_position'])}")
                
            st.success(f"📊 Prediction output processed cleanly.")

import streamlit as st
import pandas as pd
import pickle
import os
import base64
import requests
from datetime import datetime

# ==================== 1. HELPER FUNCTIONS & MAPPINGS ====================

@st.cache_data(ttl=3600)
def fetch_live_wdc_standings():
    try:
        url = "http://ergast.com/api/f1/current/driverStandings.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            standings_lists = data["MRData"]["StandingsTable"]["StandingsList"][0]["DriverStandings"]
            pos_list, driver_list, team_list, points_list = [], [], [], []
            for item in standings_lists:
                pos_list.append(int(item["position"]))
                d_name = f"{item['Driver']['givenName']} {item['Driver']['familyName']}"
                driver_list.append(d_name)
                team_list.append(item["Constructors"][0]["name"])
                points_list.append(float(item["points"]))
            return pd.DataFrame({"Pos": pos_list, "Driver": driver_list, "Team": team_list, "Points": points_list})
    except Exception:
        pass
    try:
        scrape_url = "https://www.formula1.com/en/results.html/2026/drivers.html"
        tables = pd.read_html(scrape_url)
        f1_table = tables[0].dropna(subset=['Pos'])
        return pd.DataFrame({
            "Pos": f1_table['Pos'].astype(int).tolist(),
            "Driver": f1_table['Driver'].apply(lambda x: " ".join(str(x).split()[:-1])).tolist(),
            "Team": f1_table['Car'].tolist(),
            "Points": f1_table['PTS'].astype(float).tolist()
        })
    except Exception:
        return pd.DataFrame({
            "Pos": list(range(1, 23)),
            "Driver": [
                "Kimi Antonelli", "Lewis Hamilton", "George Russell", "Charles Leclerc", "Lando Norris",
                "Oscar Piastri", "Max Verstappen", "Pierre Gasly", "Isack Hadjar", "Liam Lawson",
                "Oliver Bearman", "Franco Colapinto", "Arvid Lindblad", "Carlos Sainz Jr.", "Alex Albon",
                "Esteban Ocon", "Gabriel Bortoleto", "Fernando Alonso", "Nico Hulkenberg", "Valtteri Bottas",
                "Sergio Perez", "Lance Stroll"
            ],
            "Team": [
                "Mercedes", "Ferrari", "Mercedes", "Ferrari", "McLaren",
                "McLaren", "Red Bull Racing", "Alpine", "Red Bull Racing", "Racing Bulls",
                "Haas", "Alpine", "Racing Bulls", "Williams", "Williams",
                "Haas", "Audi", "Aston Martin", "Audi", "Cadillac",
                "Cadillac", "Aston Martin"
            ],
            "Points": [156, 115, 106, 75, 73, 68, 55, 41, 34, 28, 18, 16, 13, 6, 5, 3, 2, 1, 0, 0, 0, 0]
        })

OFFICIAL_F1_IMAGES = {
    "RUS": "https://media.formula1.com/content/dam/fom-website/drivers/G/GEORUS01_George_Russell/georus01.png",
    "HAM": "https://media.formula1.com/content/dam/fom-website/drivers/L/LEWHAM01_Lewis_Hamilton/lewham01.png",
    "NOR": "https://media.formula1.com/content/dam/fom-website/drivers/L/LANNOR01_Lando_Norris/lannor01.png",
    "PIA": "https://media.formula1.com/content/dam/fom-website/drivers/O/OSCPIA01_Oscar_Piastri/oscpia01.png",
    "LEC": "https://media.formula1.com/content/dam/fom-website/drivers/C/CHALEC01_Charles_Leclerc/chalec01.png",
    "VER": "https://media.formula1.com/content/dam/fom-website/drivers/M/MAXVER01_Max_Verstappen/maxver01.png",
    "GAS": "https://media.formula1.com/content/dam/fom-website/drivers/P/PIEGAS01_Pierre_Gasly/piegas01.png",
    "ANT": "https://media.formula1.com/content/dam/fom-website/drivers/K/KIMANT01_Kimi_Antonelli/kimant01.png"
}

TEAM_COLORS = {
    "Mercedes": "#27F4D2", "Mercedes-AMG Petronas F1 Team": "#27F4D2",
    "Ferrari": "#E8002D", "Scuderia Ferrari HP": "#E8002D",
    "McLaren": "#FF8000", "McLaren F1 Team": "#FF8000",
    "Red Bull Racing": "#3671C6", "Oracle Red Bull Racing": "#3671C6",
    "Alpine": "#FF87BC", "BWT Alpine F1 Team": "#FF87BC",
    "Racing Bulls": "#66C2FF", "Visa Cash App RB F1 Team": "#66C2FF", "Visa Cash App Racing Bulls F1 Team": "#66C2FF",
    "Haas": "#B6BABD", "MoneyGram Haas F1 Team": "#B6BABD", "TGR Haas F1 Team": "#B6BABD",
    "Cadillac": "#FFFFFF", "Cadillac Racing": "#FFFFFF",
    "Audi": "#F51A4A", "Kick Sauber": "#F51A4A", "Stake F1 Team Kick Sauber": "#F51A4A",
    "Aston Martin": "#229971", "Aston Martin Aramco F1 Team": "#229971",
    "Williams": "#64C4FF", "Williams Racing": "#64C4FF", "Atlassian Williams F1 Team": "#64C4FF"
}

TEAM_LOGOS_MAPPING = {
    "Mercedes": "team_logos/mercedes.png", "Mercedes-AMG Petronas F1 Team": "team_logos/mercedes.png",
    "Ferrari": "team_logos/ferrari.png", "Scuderia Ferrari HP": "team_logos/ferrari.png",
    "McLaren": "team_logos/mclaren.png", "McLaren F1 Team": "team_logos/mclaren.png",
    "Red Bull Racing": "team_logos/redblue.png" if os.path.exists("team_logos/redblue.png") else "team_logos/redbull.png",
    "Oracle Red Bull Racing": "team_logos/redbull.png",
    "Alpine": "team_logos/alpine.png", "BWT Alpine F1 Team": "team_logos/alpine.png",
    "Racing Bulls": "team_logos/rb.png", "Visa Cash App RB F1 Team": "team_logos/rb.png", "Visa Cash App Racing Bulls F1 Team": "team_logos/rb.png",
    "Haas": "team_logos/haas.png", "MoneyGram Haas F1 Team": "team_logos/haas.png", "TGR Haas F1 Team": "team_logos/haas.png",
    "Cadillac": "team_logos/cadillac.png", "Cadillac Racing": "team_logos/cadillac.png",
    "Audi": "team_logos/audi.png", "Kick Sauber": "team_logos/audi.png",
    "Aston Martin": "team_logos/astonmartin.png", "Aston Martin Aramco F1 Team": "team_logos/astonmartin.png",
    "Williams": "team_logos/williams.png", "Williams Racing": "team_logos/williams.png", "Atlassian Williams F1 Team": "team_logos/williams.png"
}

# ==================== SVG ICON HELPERS (replaces all emoji usage) ====================

def svg_sun():
    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FDB833" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;flex-shrink:0;"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'

def svg_cloud():
    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;flex-shrink:0;"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>'

def svg_rain():
    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#60A5FA" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;flex-shrink:0;"><line x1="16" y1="13" x2="16" y2="21"/><line x1="8" y1="13" x2="8" y2="21"/><line x1="12" y1="15" x2="12" y2="23"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/></svg>'

def svg_wind():
    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#A78BFA" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;flex-shrink:0;"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>'

def svg_moon():
    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C4B5FD" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;flex-shrink:0;"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'

def svg_partly_cloudy():
    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;flex-shrink:0;"><circle cx="10" cy="8" r="4" stroke="#FDB833" fill="none"/><path d="M17 13h-1.26A6 6 0 1 0 6 20h11a4 4 0 0 0 0-8z" stroke="#9CA3AF" fill="none"/></svg>'

def svg_map_pin():
    return '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#64C4FF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:5px;flex-shrink:0;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>'

def svg_trophy():
    return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFD700" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px;flex-shrink:0;"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 9c0 5.25 6 8 6 8s6-2.75 6-8"/><line x1="12" y1="17" x2="12" y2="22"/><line x1="8" y1="22" x2="16" y2="22"/><path d="M4 9H2a2 2 0 0 0 0 4h2"/><path d="M20 9h2a2 2 0 0 1 0 4h-2"/></svg>'

def svg_flag():
    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#F3F4F6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px;flex-shrink:0;"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>'

def svg_chart():
    return '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#27F4D2" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px;flex-shrink:0;"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'

def svg_bolt():
    return '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#27F4D2" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:6px;flex-shrink:0;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'

def svg_list():
    return '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#B6BABD" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:5px;flex-shrink:0;"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>'

def svg_calendar():
    return '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#FF1801" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;flex-shrink:0;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>'

# Weather entries: icon fn + hex-colored desc strings (no emojis anywhere)
TRACK_METRICS = {
    "Australia":       {"name": "Albert Park Circuit",                       "icon_fn": svg_sun,          "cond": "Sunny",          "cond_color": "#FDB833", "temp": "34", "temp_color": "#F97316"},
    "China":           {"name": "Shanghai Circuit",                           "icon_fn": svg_cloud,        "cond": "Overcast",       "cond_color": "#9CA3AF", "temp": "22", "temp_color": "#FBBF24"},
    "Japan":           {"name": "Suzuka Racing Course",                       "icon_fn": svg_sun,          "cond": "Clear",          "cond_color": "#FDB833", "temp": "29", "temp_color": "#F97316"},
    "Bahrain":         {"name": "Bahrain Circuit",                            "icon_fn": svg_moon,         "cond": "Night Race",     "cond_color": "#C4B5FD", "temp": "27", "temp_color": "#FBBF24"},
    "Saudi Arabia":    {"name": "Jeddah Corniche",                            "icon_fn": svg_moon,         "cond": "Night Race",     "cond_color": "#C4B5FD", "temp": "28", "temp_color": "#FBBF24"},
    "Miami":           {"name": "Miami Autodrome",                            "icon_fn": svg_partly_cloudy,"cond": "Humid",          "cond_color": "#FBBF24", "temp": "41", "temp_color": "#EF4444"},
    "Canada":          {"name": "Circuit Gilles-Villeneuve",                  "icon_fn": svg_partly_cloudy,"cond": "Breezy",         "cond_color": "#FBBF24", "temp": "26", "temp_color": "#FBBF24"},
    "Monaco":          {"name": "Circuit de Monaco",                          "icon_fn": svg_sun,          "cond": "Clear",          "cond_color": "#FDB833", "temp": "32", "temp_color": "#F97316"},
    "Spain (Barcelona)":{"name": "Circuit de Catalunya",                      "icon_fn": svg_sun,          "cond": "Hot",            "cond_color": "#FDB833", "temp": "39", "temp_color": "#EF4444"},
    "Austria":         {"name": "Red Bull Ring (Spielberg)",                  "icon_fn": svg_partly_cloudy,"cond": "Part Cloud",     "cond_color": "#FBBF24", "temp": "28", "temp_color": "#FBBF24"},
    "Great Britain":   {"name": "Silverstone Circuit",                        "icon_fn": svg_rain,         "cond": "Light Drizzle",  "cond_color": "#60A5FA", "temp": "19", "temp_color": "#34D399"},
    "Belgium":         {"name": "Spa-Francorchamps",                          "icon_fn": svg_cloud,        "cond": "Cloudy",         "cond_color": "#9CA3AF", "temp": "18", "temp_color": "#34D399"},
    "Netherlands":     {"name": "Circuit Zandvoort",                          "icon_fn": svg_wind,         "cond": "Windy",          "cond_color": "#A78BFA", "temp": "21", "temp_color": "#34D399"},
    "Italy":           {"name": "Autodromo Nazionale Monza",                  "icon_fn": svg_sun,          "cond": "Very Hot",       "cond_color": "#FDB833", "temp": "42", "temp_color": "#EF4444"},
    "Azerbaijan":      {"name": "Baku City Circuit",                          "icon_fn": svg_partly_cloudy,"cond": "Clear",          "cond_color": "#FBBF24", "temp": "30", "temp_color": "#F97316"},
    "Singapore":       {"name": "Marina Bay Street Circuit",                  "icon_fn": svg_rain,         "cond": "Humid & Wet",    "cond_color": "#60A5FA", "temp": "29", "temp_color": "#FBBF24"},
    "United States":   {"name": "Circuit of the Americas",                    "icon_fn": svg_sun,          "cond": "Sunny",          "cond_color": "#FDB833", "temp": "37", "temp_color": "#F97316"},
    "Mexico":          {"name": "Autodromo Hermanos Rodriguez",               "icon_fn": svg_partly_cloudy,"cond": "Thin Air",       "cond_color": "#FBBF24", "temp": "33", "temp_color": "#F97316"},
    "Brazil":          {"name": "Autodromo Jose Carlos Pace (Interlagos)",    "icon_fn": svg_rain,         "cond": "Unpredictable",  "cond_color": "#60A5FA", "temp": "25", "temp_color": "#FBBF24"},
    "Las Vegas":       {"name": "Las Vegas Strip Circuit",                    "icon_fn": svg_moon,         "cond": "Cold Night",     "cond_color": "#C4B5FD", "temp": "14", "temp_color": "#60A5FA"},
    "Qatar":           {"name": "Lusail International Circuit",               "icon_fn": svg_moon,         "cond": "Windy Night",    "cond_color": "#C4B5FD", "temp": "31", "temp_color": "#F97316"},
    "Abu Dhabi":       {"name": "Yas Marina Circuit",                         "icon_fn": svg_moon,         "cond": "Twilight Race",  "cond_color": "#C4B5FD", "temp": "28", "temp_color": "#FBBF24"},
    "Hungary":         {"name": "Hungaroring (Budapest)",                     "icon_fn": svg_sun,          "cond": "Scorching",      "cond_color": "#FDB833", "temp": "43", "temp_color": "#EF4444"},
    "Spain (Madrid)":  {"name": "Madrid Street Circuit",                      "icon_fn": svg_partly_cloudy,"cond": "Pleasant",       "cond_color": "#FBBF24", "temp": "28", "temp_color": "#FBBF24"},
}

def render_track_weather(race_name):
    info = TRACK_METRICS.get(race_name, {
        "name": "F1 Grand Prix Track",
        "icon_fn": svg_partly_cloudy,
        "cond": "Fetching...",
        "cond_color": "#9CA3AF",
        "temp": "--",
        "temp_color": "#9CA3AF"
    })
    icon = info["icon_fn"]()
    return f'{svg_map_pin()}{info["name"]} &nbsp;&bull;&nbsp; {icon}<span style="color:{info["cond_color"]};">{info["cond"]}</span> <span style="color:#4B5563;">|</span> <span style="color:{info["temp_color"]};">{info["temp"]}&#176;C</span>'


def get_driver_image(driver_code):
    local_path = f"drivers_images/{driver_code}.png"
    if os.path.exists(local_path):
        try:
            with open(local_path, "rb") as img_file:
                b64_string = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{b64_string}"
        except Exception:
            pass
    return OFFICIAL_F1_IMAGES.get(driver_code, "https://media.formula1.com/d_driver_fallback_image.png")

def get_base64_logo_html(team_name, border_color, centered=False):
    target_path = TEAM_LOGOS_MAPPING.get(team_name, "")
    if not os.path.exists(target_path):
        clean_key = team_name.split()[0].lower()
        if "williams" in team_name.lower(): clean_key = "williams"
        elif "haas" in team_name.lower(): clean_key = "haas"
        elif "alpine" in team_name.lower(): clean_key = "alpine"
        elif "racing" in team_name.lower() and "bulls" in team_name.lower(): clean_key = "rb"
        if os.path.exists("team_logos"):
            for filename in os.listdir("team_logos"):
                if clean_key in filename.lower() and filename.endswith(".png"):
                    target_path = f"team_logos/{filename}"
                    break
    if os.path.exists(target_path):
        with open(target_path, "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode()
        logo_height = "38px" if "mclaren" in team_name.lower() else "20px"
        if centered:
            return f"""<div style='display: inline-flex; align-items: center; justify-content: center; text-align: center !important; width: 100%; height: 38px;'><img src='data:image/png;base64,{b64_string}' style='height: {logo_height}; width: auto; margin-right: 8px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));' /> <span style='font-size: 1em; font-weight: 500; color: #F3F4F6;'>{team_name}</span></div>"""
        else:
            return f"""<div style='border-left: 6px solid {border_color}; padding-left: 10px; display: inline-flex; align-items: center; justify-content: flex-start; text-align: left !important; width: 100%; height: 38px;'><img src='data:image/png;base64,{b64_string}' style='height: {logo_height}; width: auto; margin-right: 12px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));' /> <span style='font-size: 1em; font-weight: 500; color: #F3F4F6;'>{team_name}</span></div>"""
    align_style = "text-align: center !important;" if centered else f"border-left: 6px solid {border_color}; padding-left: 10px; text-align: left !important;"
    return f"<div style='{align_style}'>{team_name}</div>"

# ==================== 2. APP PAGE CONFIGURATION ====================

st.set_page_config(page_title="PaddockGrid", page_icon="🏎️", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    .stApp { background-color: #0F0F14 !important; color: #F3F4F6 !important; }
    h1, h2, h3, h4, p, .stMarkdown {
        text-align: center !important;
        font-family: 'Titillium Web', 'Segoe UI', sans-serif !important;
    }
    [data-testid="stHorizontalBlock"] { gap: 16px !important; }

    .paddock-box {
        background: #181820 !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        min-height: 115px !important; max-height: 115px !important; box-sizing: border-box;
    }
    .paddock-box:hover {
        transform: translateY(-2px) !important;
        border-color: rgba(255, 24, 1, 0.25) !important;
        background: #1c1c26 !important;
        box-shadow: 0 0 20px rgba(255, 24, 1, 0.35) !important;
    }

    div.prediction-container div[data-testid="stButton"] button {
        background-color: transparent !important;
        color: #27F4D2 !important;
        border: 1px solid rgba(39, 244, 210, 0.4) !important;
        font-weight: bold !important; height: 50px !important;
        transition: all 0.3s ease !important;
    }
    div.prediction-container div[data-testid="stButton"] button:hover {
        background-color: #27F4D2 !important; color: #111116 !important;
        box-shadow: 0 0 15px rgba(39, 244, 210, 0.4) !important;
    }

    div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stSelectbox"] {
        background: #181820 !important; border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 10px !important; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35) !important;
        display: flex !important; flex-direction: column !important; justify-content: flex-end !important;
        min-height: 115px !important; max-height: 115px !important;
        padding: 12px 16px 12px 16px !important; margin-top: 0px !important;
        box-sizing: border-box !important; position: relative !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stSelectbox"]::before {
        content: "SELECT GRAND PRIX" !important; position: absolute !important;
        top: 22px !important; left: 0 !important; width: 100% !important;
        text-align: center !important; color: #888888 !important;
        font-size: 0.72rem !important; font-weight: 600 !important;
        letter-spacing: 0.8px !important;
        font-family: 'Titillium Web', 'Segoe UI', sans-serif !important;
    }
    div[data-testid="stColumn"]:nth-of-type(2) label[data-testid="stWidgetLabel"] {
        display: none !important; height: 0px !important; margin: 0px !important; padding: 0px !important;
    }
    div[data-testid="stColumn"]:nth-of-type(2) div[role="combobox"] {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 6px !important; color: #F3F4F6 !important;
        height: 40px !important; margin-top: auto !important;
    }
    div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stSelectbox"]:hover {
        transform: translateY(-2px) !important; border-color: rgba(255, 24, 1, 0.4) !important;
        background: #1c1c26 !important; box-shadow: 0 0 20px rgba(255, 24, 1, 0.35) !important;
    }

    .interactive-wrapper { position: relative; width: 100%; }
    .popover-anchor div[data-testid="stPopover"] {
        position: absolute; top: 0; left: 0;
        width: 100% !important; height: 95px !important; z-index: 10; opacity: 0 !important;
    }
    .popover-anchor div[data-testid="stPopover"] > button {
        width: 100% !important; height: 95px !important;
        border: none !important; background: transparent !important; cursor: pointer !important;
    }

    .pos-badge {
        background: #FF1801; color: white; padding: 4px 14px;
        border-radius: 20px; font-size: 0.85em; font-weight: bold;
        text-transform: uppercase; letter-spacing: 1px;
    }
    .grid-row-container {
        background: #14141c; border-radius: 6px; padding: 10px 15px;
        margin-bottom: 6px; border-left: 4px solid #333; display: flex; align-items: center;
    }

    /* WDC card */
    .wdc-wrapper-box {
        position: relative; width: 100%; height: 115px;
        display: flex; align-items: flex-end; transform: translateY(-15px) !important;
    }
    .wdc-contender-card {
        background: #181820; border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 10px; padding: 12px 16px 12px 90px;
        display: flex; flex-direction: column; justify-content: center;
        width: 100%; height: 115px !important; box-sizing: border-box;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .wdc-3d-avatar {
        position: absolute; left: 8px; bottom: 0px;
        width: 80px; height: 110px; object-fit: contain; z-index: 10;
        filter: drop-shadow(0 8px 12px rgba(0,0,0,0.5));
        transition: transform 0.3s ease, filter 0.3s ease;
    }
    .wdc-wrapper-box:hover .wdc-contender-card {
        border-color: #FF1801 !important;
        box-shadow: 0 0 20px rgba(255, 24, 1, 0.35) !important;
        background: #1c1c26 !important;
    }
    .wdc-wrapper-box:hover .wdc-3d-avatar {
        transform: translateY(-4px) scale(1.03);
        filter: drop-shadow(0 12px 16px rgba(255, 24, 1, 0.25));
    }

    /* WCC card */
    .wcc-wrapper-box { position: relative !important; width: 100%; height: 115px; display: flex; align-items: flex-end; }
    .wcc-contender-card {
        background: #181820 !important; border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 10px !important; padding: 12px 16px !important;
        display: flex !important; flex-direction: column !important;
        justify-content: center !important; align-items: center !important;
        text-align: center !important; width: 100%; height: 115px !important;
        box-sizing: border-box; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        margin-bottom: 12px !important;
    }
    .wcc-wrapper-box:hover .wcc-contender-card {
        transform: translateY(-4px) !important; border-color: rgba(255, 24, 1, 0.4) !important;
        background: #1c1c26 !important; box-shadow: 0 0 20px rgba(255, 24, 1, 0.35) !important;
    }
    .wcc-wrapper-box:hover img { transform: scale(1.08); }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_resource
def load_model_bundle():
    model_path = "f1_model_v3.pkl"
    if not os.path.exists(model_path): return None
    with open(model_path, "rb") as f: return pickle.load(f)

bundle = load_model_bundle()
if bundle is None: st.stop()
model, ALL_FEATURES = bundle["model"], bundle["features"]

st.markdown("<h1 style='color: #FF1801; font-weight: bold; margin-top: -10px; margin-bottom: 2px;'>PaddockGrid</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.0em; color: #888888; margin-bottom: 25px;'>Telemetry Analytics &nbsp;&#8725;&#8725;&nbsp; Straight from the pitlane, onto the grid</p>", unsafe_allow_html=True)

F1_2026_SCHEDULE = [
    {"round": 1,  "race": "Australia",      "date_str": "06-08 MAR",        "date": datetime(2026, 3, 8)},
    {"round": 2,  "race": "China",           "date_str": "13-15 MAR",        "date": datetime(2026, 3, 15)},
    {"round": 3,  "race": "Japan",           "date_str": "27-29 MAR",        "date": datetime(2026, 3, 29)},
    {"round": 4,  "race": "Bahrain",         "date_str": "10-12 APR",        "date": datetime(2026, 4, 12)},
    {"round": 5,  "race": "Saudi Arabia",    "date_str": "17-19 APR",        "date": datetime(2026, 4, 19)},
    {"round": 6,  "race": "Miami",           "date_str": "01-03 MAY",        "date": datetime(2026, 5, 3)},
    {"round": 7,  "race": "Canada",          "date_str": "22-24 MAY",        "date": datetime(2026, 5, 24)},
    {"round": 8,  "race": "Monaco",          "date_str": "05-07 JUN",        "date": datetime(2026, 6, 7)},
    {"round": 9,  "race": "Spain (Barcelona)","date_str": "12-14 JUN",       "date": datetime(2026, 6, 14)},
    {"round": 10, "race": "Austria",         "date_str": "26-28 JUN",        "date": datetime(2026, 6, 28)},
    {"round": 11, "race": "Great Britain",   "date_str": "03-05 JUL",        "date": datetime(2026, 7, 5)},
    {"round": 12, "race": "Belgium",         "date_str": "17-19 JUL",        "date": datetime(2026, 7, 19)},
    {"round": 13, "race": "Hungary",         "date_str": "24-26 JUL",        "date": datetime(2026, 7, 26)},
    {"round": 14, "race": "Netherlands",     "date_str": "21-23 AUG",        "date": datetime(2026, 8, 23)},
    {"round": 15, "race": "Italy",           "date_str": "04-06 SEP",        "date": datetime(2026, 9, 6)},
    {"round": 16, "race": "Spain (Madrid)",  "date_str": "11-13 SEP",        "date": datetime(2026, 9, 13)},
    {"round": 17, "race": "Azerbaijan",      "date_str": "24-26 SEP",        "date": datetime(2026, 9, 26)},
    {"round": 18, "race": "Singapore",       "date_str": "09-11 OCT",        "date": datetime(2026, 10, 11)},
    {"round": 19, "race": "United States",   "date_str": "23-25 OCT",        "date": datetime(2026, 10, 25)},
    {"round": 20, "race": "Mexico",          "date_str": "30 OCT - 01 NOV",  "date": datetime(2026, 11, 1)},
    {"round": 21, "race": "Brazil",          "date_str": "06-08 NOV",        "date": datetime(2026, 11, 8)},
    {"round": 22, "race": "Las Vegas",       "date_str": "19-21 NOV",        "date": datetime(2026, 11, 21)},
    {"round": 23, "race": "Qatar",           "date_str": "27-29 NOV",        "date": datetime(2026, 11, 29)},
    {"round": 24, "race": "Abu Dhabi",       "date_str": "04-06 DEC",        "date": datetime(2026, 12, 6)},
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

race_name = next_race_name
races_list = [f"Round {e['round']}: {e['race']}" for e in F1_2026_SCHEDULE]

# ==================== ROW 1 CONSOLE INTERFACES ====================
row1_cols = st.columns(4)

with row1_cols[0]:
    live_wdc_df = fetch_live_wdc_standings()
    if not live_wdc_df.empty:
        leader_name = live_wdc_df.iloc[0]["Driver"]
        leader_team = live_wdc_df.iloc[0]["Team"]
    else:
        leader_name = "Kimi Antonelli"
        leader_team = "Mercedes"

    accent_color = TEAM_COLORS.get(leader_team, "#27F4D2")
    try:
        raw_lastname = leader_name.split()[-1]
        driver_code = "SAI" if "sainz" in leader_name.lower() else raw_lastname[:3].upper()
    except:
        driver_code = "ANT"

    driver_b64_stream = get_driver_image(driver_code)
    st.markdown(f"""
    <div class="wdc-wrapper-box">
        <img class="wdc-3d-avatar" src="{driver_b64_stream}" />
        <div class="wdc-contender-card">
            <div style="color: #888888; font-size: 0.72em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; line-height: 1.2;">WDC CONTENDER</div>
            <div style="color: #FFFFFF; font-size: 1.25em; font-weight: bold; margin: 3px 0; line-height: 1.2;">{leader_name}</div>
            <div style="border-left: 3px solid {accent_color}; padding-left: 8px; font-size: 0.85em; color: #BBBBBB; font-weight: 500; margin-top: 3px; line-height: 1.2;">{leader_team}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with row1_cols[1]:
    selected_option = st.selectbox(
        "Select Grand Prix Hidden Base Label",
        options=races_list,
        index=default_index,
        key="dashboard_gp_selector_v5_perfected"
    )
    race_name = selected_option.split(": ")[-1]

with row1_cols[2]:
    st.markdown(f"""
    <div class="paddock-box" style="border-left: 4px solid #FF1801; align-items: flex-start; text-align: left !important; line-height: 1.35;">
        <span style='color: #888888; font-size: 0.7em; text-transform: uppercase; letter-spacing: 0.5px;'>Upcoming Live Weekend</span>
        <strong style='color: #FFFFFF; font-size: 1.0em; margin-top: 2px;'>{next_race_name}</strong>
        <span style='color: #FF1801; font-size: 0.8em; font-weight: bold;'>{svg_calendar()}{next_race_date_str}</span>
    </div>
    """, unsafe_allow_html=True)

with row1_cols[3]:
    wcc_leader_team = "Mercedes"
    wcc_accent_color = TEAM_COLORS.get(wcc_leader_team, "#27F4D2")
    logo_path = "team_logos/mercedes.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            b64_string = base64.b64encode(img_file.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64_string}" style="height: 32px; width: auto; margin-right: 10px; transition: transform 0.3s ease; filter: drop-shadow(0 2px 6px rgba(0,0,0,0.4));" />'
    else:
        logo_html = f'<img src="https://media.formula1.com/content/dam/fom-website/teams/2026/mercedes.png" style="height: 32px; width: auto; margin-right: 10px; transition: transform 0.3s ease;" />'

    st.markdown(f"""
    <div class="wcc-wrapper-box">
        <div class="wcc-contender-card" style="border-left: 5px solid {wcc_accent_color};">
            <div style="color: #888888; font-size: 0.72em; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;">WCC CONTENDER</div>
            <div style="display: inline-flex; align-items: center; justify-content: center; margin-bottom: 4px; width: 100%;">
                {logo_html}
                <span style="color: #FFFFFF; font-size: 1.25em; font-weight: bold;">{wcc_leader_team}</span>
            </div>
            <div style="font-size: 0.85em; color: #BBBBBB; font-weight: 500;">Current Championship Leader</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

        wcc_data = pd.DataFrame({"Pos": [1, 2, 3, 4, 5], "Team": ["Mercedes", "Ferrari", "McLaren", "Red Bull Racing", "Cadillac"], "Points": [262, 190, 141, 89, 0]})
        st.table(wcc_data.set_index("Pos"))

# ==================== ROW 2 CONSOLE INTERFACES ====================
row2_cols = st.columns(3)

with row2_cols[0]:
    weather_html = render_track_weather(race_name)
    st.markdown(f"""
    <div class="paddock-box" style="border-left: 4px solid #64C4FF; align-items: flex-start; text-align: left !important; min-height: 85px; max-height: 85px; gap: 4px;">
        <span style='font-size: 1.05em; font-weight: 600; color: #FFF;'>Circuit Details</span>
        <span style='font-size: 0.82em; color: #9CA3AF; display:flex; align-items:center; flex-wrap:wrap; gap:2px;'>{weather_html}</span>
    </div>
    """, unsafe_allow_html=True)

with row2_cols[1]:
    st.markdown('<div class="prediction-container paddock-box" style="border-left: 4px solid #27F4D2; align-items: stretch; padding: 12px 14px; min-height: 85px; max-height: 85px;">', unsafe_allow_html=True)
    trigger_prediction = st.button("Generate Grid Prediction", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with row2_cols[2]:
    st.markdown(f"""
    <div class="interactive-wrapper popover-anchor">
        <div class="paddock-box" style="border-left: 4px solid #B6BABD; align-items: center; text-align: center !important; min-height: 85px; max-height: 85px;">
            <span style='color: #FFFFFF; font-size: 1.15em; font-weight: 500;'>{svg_list()}Last Race Result</span>
            <span style='color: #666666; font-size: 0.8em; margin-top: 2px;'>Click to open race summary</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    with st.popover("Results Window"):
        st.markdown(f"<h4 style='color:#FF1801;'>{svg_flag()}AWS Gran Premio de Espana Result</h4>", unsafe_allow_html=True)
        st.markdown("**1st:** Lewis Hamilton (Ferrari)<br>**2nd:** George Russell (Mercedes)<br>**3rd:** Lando Norris (McLaren)", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== PREDICTED PODIUM ENGINE VIEW ====================
if trigger_prediction:
    with st.spinner("Processing prediction..."):
        bundle_path = "f1_model_v3.pkl"
        if not os.path.exists(bundle_path):
            st.error("Model file bundle not found.")
            st.stop()
        try:
            import predict_race_v3
            pred_df = predict_race_v3.predict_race(2026, race_name, None)
        except Exception as e:
            st.error(f"Failed to execute prediction pipeline: {e}")
            st.stop()

        if pred_df is None or pred_df.empty:
            st.warning("No data returned.")
        else:
            st.markdown(f"<h2 style='margin: 25px 0 15px 0; font-weight: 600;'>{svg_trophy()}Predicted Podium</h2>", unsafe_allow_html=True)
            podium_cols = st.columns(3)

            if len(pred_df) > 1:
                p2_row = pred_df.iloc[1]
                p2_color = TEAM_COLORS.get(p2_row['team'], '#FFFFFF')
                p2_logo_centered = get_base64_logo_html(p2_row['team'], p2_color, centered=True)
                with podium_cols[0]:
                    st.markdown(f"""
                    <div style="background: #181820; border-radius: 12px; border-top: 4px solid {p2_color}; padding: 25px 15px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
                        <div style="margin-bottom: 15px;"><span class='pos-badge' style='background:#C0C0C0; color:#111;'>P2</span></div>
                        <img src="{get_driver_image(p2_row['driver'])}" style="width: 150px; height: auto; aspect-ratio: 1/1; object-fit: contain; margin-bottom: 12px;" />
                        <h3 style="margin: 5px 0 2px 0; font-size: 1.4em; color: #FFF; font-weight: 500;">{p2_row['_name']}</h3>
                        <div style="width: 100%; margin-top: 8px;">{p2_logo_centered}</div>
                    </div>
                    """, unsafe_allow_html=True)

            if len(pred_df) > 0:
                p1_row = pred_df.iloc[0]
                p1_color = TEAM_COLORS.get(p1_row['team'], '#FFFFFF')
                p1_logo_centered = get_base64_logo_html(p1_row['team'], p1_color, centered=True)
                with podium_cols[1]:
                    st.markdown(f"""
                    <div style="background: #181820; border-radius: 12px; border-top: 4px solid {p1_color}; padding: 30px 15px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 12px 30px rgba(0,0,0,0.45); border-left: 1px solid rgba(255,215,0,0.05); border-right: 1px solid rgba(255,215,0,0.05);">
                        <div style="margin-bottom: 15px;"><span class='pos-badge' style='background:#FFD700; color:#111; box-shadow: 0 0 10px rgba(255,215,0,0.25);'>WINNER</span></div>
                        <img src="{get_driver_image(p1_row['driver'])}" style="width: 175px; height: auto; aspect-ratio: 1/1; object-fit: contain; margin-bottom: 12px;" />
                        <h2 style="margin: 5px 0 2px 0; font-size: 1.7em; color: #FFF; font-weight: bold; letter-spacing: 0.5px;">{p1_row['_name']}</h2>
                        <div style="width: 100%; margin-top: 8px;">{p1_logo_centered}</div>
                    </div>
                    """, unsafe_allow_html=True)

            if len(pred_df) > 2:
                p3_row = pred_df.iloc[2]
                p3_color = TEAM_COLORS.get(p3_row['team'], '#FFFFFF')
                p3_logo_centered = get_base64_logo_html(p3_row['team'], p3_color, centered=True)
                with podium_cols[2]:
                    st.markdown(f"""
                    <div style="background: #181820; border-radius: 12px; border-top: 4px solid {p3_color}; padding: 25px 15px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
                        <div style="margin-bottom: 15px;"><span class='pos-badge' style='background:#CD7F32; color:#111;'>P3</span></div>
                        <img src="{get_driver_image(p3_row['driver'])}" style="width: 150px; height: auto; aspect-ratio: 1/1; object-fit: contain; margin-bottom: 12px;" />
                        <h3 style="margin: 5px 0 2px 0; font-size: 1.4em; color: #FFF; font-weight: 500;">{p3_row['_name']}</h3>
                        <div style="width: 100%; margin-top: 8px;">{p3_logo_centered}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown(f"<br><h3 style='margin-top: 35px; font-weight:600;'>{svg_flag()}Full Predicted Grid Standing</h3>", unsafe_allow_html=True)
            st.markdown("---")

            for idx, row in pred_df.iterrows():
                row_cols = st.columns([1, 2, 4, 2])
                row_cols[0].markdown(f"**P{row['predicted_position']}**")
                row_cols[1].markdown(row['_name'])
                border_color = TEAM_COLORS.get(row['team'], '#FFFFFF')
                logo_html_block = get_base64_logo_html(row['team'], border_color, centered=False)
                row_cols[2].markdown(logo_html_block, unsafe_allow_html=True)
                row_cols[3].markdown(f"Grid: {int(row['grid_position'])}")

            st.success(f"{svg_chart()} Prediction output processed cleanly.")

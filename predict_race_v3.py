"""
predict_race_v3.py — F1 Race Outcome Predictor V3
==================================================
Predicts finishing positions for:
  - Completed races  : uses real FastF1 qualifying data
  - Upcoming races   : uses current standings + circuit defaults
                       (no qualifying data available yet)

Usage:
  python predict_race_v3.py
  Then enter year and race name when prompted.
"""

import fastf1
import pandas as pd
import numpy as np
import pickle
import requests
import os
from datetime import date as _date
import time
# --- Import the centralized feature engine ---
from features_v3 import compute_v3_features

os.makedirs("f1_cache", exist_ok=True)
fastf1.Cache.enable_cache("f1_cache")

# ── Load model ─────────────────────────────────────────────────────────────────
with open("f1_model_v3.pkl", "rb") as f:
    bundle = pickle.load(f)

model        = bundle["model"]
ALL_FEATURES = bundle["features"]
CAT_FEATURES = bundle["cat_features"]
cat_idx      = bundle["cat_idx"]

print(f"\n  ✓ Model loaded  (V3 MAE: {bundle['mae']} positions)")

# ── 2026 verified standings (update each race weekend) ────────────────────────
DRIVER_POINTS_2026 = {
    "ANT": 156, "HAM": 115, "RUS": 106, "LEC":  75,
    "NOR":  73, "PIA":  58, "VER":  55, "GAS":  41,
    "HAD":  34, "LAW":  28, "BEA":  18, "COL":  16,
    "LIN":  13, "SAI":   6, "ALB":   5, "OCO":   3,
    "BOR":   2, "ALO":   1, "HUL":   0, "PER":   0,
    "BOT":   0, "STR":   0,
}
CONSTRUCTOR_POINTS_2026 = {
    "Mercedes": 262, "Ferrari": 190, "McLaren": 131,
    "Red Bull Racing": 89, "BWT Alpine F1 Team": 57,
    "Visa Cash App Racing Bulls F1 Team": 41,
    "TGR Haas F1 Team": 21, "Atlassian Williams F1 Team": 11,
    "Audi Revolut F1 Team": 2, "Aston Martin Aramco F1 Team": 1,
    "Cadillac F1 Team": 0,
}

# ── 2026 driver roster (full grid) ────────────────────────────────────────────
DRIVERS_2026 = {
    "ANT": {"name": "Kimi Antonelli",    "team": "Mercedes"},
    "RUS": {"name": "George Russell",    "team": "Mercedes"},
    "HAM": {"name": "Lewis Hamilton",    "team": "Ferrari"},
    "LEC": {"name": "Charles Leclerc",   "team": "Ferrari"},
    "NOR": {"name": "Lando Norris",      "team": "McLaren"},
    "PIA": {"name": "Oscar Piastri",     "team": "McLaren"},
    "VER": {"name": "Max Verstappen",    "team": "Red Bull Racing"},
    "HAD": {"name": "Isack Hadjar",      "team": "Red Bull Racing"},
    "GAS": {"name": "Pierre Gasly",      "team": "BWT Alpine F1 Team"},
    "COL": {"name": "Franco Colapinto",  "team": "BWT Alpine F1 Team"},
    "LAW": {"name": "Liam Lawson",       "team": "Visa Cash App Racing Bulls F1 Team"},
    "LIN": {"name": "Arvid Lindblad",    "team": "Visa Cash App Racing Bulls F1 Team"},
    "BEA": {"name": "Oliver Bearman",    "team": "TGR Haas F1 Team"},
    "OCO": {"name": "Esteban Ocon",      "team": "TGR Haas F1 Team"},
    "SAI": {"name": "Carlos Sainz",      "team": "Atlassian Williams F1 Team"},
    "ALB": {"name": "Alex Albon",        "team": "Atlassian Williams F1 Team"},
    "HUL": {"name": "Nico Hulkenberg",   "team": "Audi Revolut F1 Team"},
    "BOR": {"name": "Gabriel Bortoleto", "team": "Audi Revolut F1 Team"},
    "ALO": {"name": "Fernando Alonso",   "team": "Aston Martin Aramco F1 Team"},
    "STR": {"name": "Lance Stroll",      "team": "Aston Martin Aramco F1 Team"},
    "PER": {"name": "Sergio Perez",      "team": "Cadillac F1 Team"},
    "BOT": {"name": "Valtteri Bottas",   "team": "Cadillac F1 Team"},
}

CIRCUIT_INFO = {
    "Monaco":              {"type": 1, "lat": 43.7347, "lon":   7.4206},
    "Spain":               {"type": 0, "lat": 41.5700, "lon":   2.2611},
    "Barcelona-Catalunya": {"type": 0, "lat": 41.5700, "lon":   2.2611},
    "Madrid":              {"type": 1, "lat": 40.4168, "lon":  -3.7038},
    "British":             {"type": 0, "lat": 52.0786, "lon":  -1.0169},
    "Austria":             {"type": 0, "lat": 47.2197, "lon":  14.7647},
    "Belgium":             {"type": 2, "lat": 50.4372, "lon":   5.9714},
    "Hungary":             {"type": 0, "lat": 47.5789, "lon":  19.2486},
    "Netherlands":         {"type": 0, "lat": 52.3888, "lon":   4.5409},
    "Italian":             {"type": 0, "lat": 45.6156, "lon":   9.2811},
    "Bahrain":             {"type": 0, "lat": 26.0325, "lon":  50.5106},
    "Saudi Arabia":        {"type": 1, "lat": 21.6319, "lon":  39.1044},
    "Azerbaijan":          {"type": 1, "lat": 40.3725, "lon":  49.8533},
    "Japan":               {"type": 0, "lat": 34.8431, "lon": 136.5407},
    "China":               {"type": 0, "lat": 31.3389, "lon": 121.2197},
    "Singapore":           {"type": 1, "lat":  1.2914, "lon": 103.8640},
    "Qatar":               {"type": 0, "lat": 25.4900, "lon":  51.4542},
    "Abu Dhabi":           {"type": 0, "lat": 24.4672, "lon":  54.6031},
    "Australia":           {"type": 1, "lat":-37.8497, "lon": 144.9680},
    "Miami":               {"type": 1, "lat": 25.9581, "lon": -80.2389},
    "Canada":              {"type": 1, "lat": 45.5000, "lon": -73.5228},
    "United States":       {"type": 1, "lat": 30.1328, "lon": -97.6411},
    "Mexico City":         {"type": 0, "lat": 19.4042, "lon": -99.0907},
    "São Paulo":           {"type": 0, "lat":-23.7036, "lon": -46.6997},
    "Las Vegas":           {"type": 1, "lat": 36.1147, "lon":-115.1728},
}

TYRE_ENCODE = {"SOFT": 0, "MEDIUM": 1, "HARD": 2, "INTERMEDIATE": 3, "WET": 4}


def get_weather(lat, lon, date_str):
    try:
        is_past = _date.fromisoformat(date_str) < _date.today()
        base    = "archive-api.open-meteo.com/v1/archive" if is_past else "api.open-meteo.com/v1/forecast"
        url     = (f"https://{base}?latitude={lat}&longitude={lon}"
                   f"&start_date={date_str}&end_date={date_str}"
                   f"&daily=temperature_2m_max,precipitation_sum&timezone=auto")
        d     = requests.get(url, timeout=10).json().get("daily", {})
        temp  = (d.get("temperature_2m_max", [None])[0]) or 25.0
        rain  = (d.get("precipitation_sum",  [None])[0]) or 0.0
        return temp, rain, temp + (15 if rain < 1 else 5)
    except Exception:
        return 25.0, 0.0, 40.0


def get_standings(year, round_number):
    if year >= 2026:
        return DRIVER_POINTS_2026, CONSTRUCTOR_POINTS_2026
    driver_pts, constructor_pts = {}, {}
    prev = max(1, round_number - 1)
    try:
        sl = requests.get(
            f"https://api.jolpi.ca/ergast/f1/{year}/{prev}/driverStandings.json",
            timeout=10).json()["MRData"]["StandingsTable"]["StandingsLists"]
        if sl:
            for s in sl[0]["DriverStandings"]:
                code = s["Driver"].get("code", s["Driver"]["driverId"][:3].upper())
                driver_pts[code] = float(s["points"])
    except Exception:
        pass
    try:
        sl = requests.get(
            f"https://api.jolpi.ca/ergast/f1/{year}/{prev}/constructorStandings.json",
            timeout=10).json()["MRData"]["StandingsTable"]["StandingsLists"]
        if sl:
            for s in sl[0]["ConstructorStandings"]:
                constructor_pts[s["Constructor"]["name"]] = float(s["points"])
    except Exception:
        pass
    return driver_pts, constructor_pts


def get_form_from_csv(driver, team, race_name, year, round_num):
    """Pull rolling form stats from the training CSV."""
    try:
        df = pd.read_csv("f1_training_data_v3.csv")
        # Races before this one
        prior = df[(df["year"] < year) | ((df["year"] == year) & (df["round"] < round_num))]
        drv_form  = prior[prior["driver"] == driver]["finish_position"].tail(3).mean()
        team_form = prior[prior["team"]   == team  ]["finish_position"].tail(3).mean()
        track_h   = prior[(prior["driver"] == driver) & (prior["race"] == race_name)]["finish_position"].mean()
        median_fp = df["finish_position"].median()
        return (
            float(drv_form)  if not pd.isna(drv_form)  else median_fp,
            float(team_form) if not pd.isna(team_form) else median_fp,
            float(track_h)   if not pd.isna(track_h)   else median_fp,
        )
    except Exception:
        return 10.0, 10.0, 10.0


def predict_race(year, race_name, round_num=None):
    circuit = CIRCUIT_INFO.get(race_name, {"type": 0, "lat": 25.0, "lon": 55.0})
    if round_num is None:
        round_num = 10  # fallback

    # ── Try loading FastF1 qualifying ──────────────────────────────────────────
    has_quali = False
    q_best, q_grid, q_tyre = {}, {}, {}
    print(f"\n  Trying FastF1 qualifying for {year} {race_name}...")
    try:
        quali = fastf1.get_session(year, race_name, "Q")
        quali.load(telemetry=False, weather=False, messages=False)
        race_s = fastf1.get_session(year, race_name, "R")
        race_s.load(telemetry=False, weather=False, messages=False)

        for driver in quali.laps["Driver"].unique():
            fastest = quali.laps.pick_drivers(driver).pick_fastest()
            if fastest is not None and not fastest.empty:
                lt = fastest["LapTime"]
                if pd.notna(lt):
                    q_best[driver] = lt.total_seconds()

        for _, row in race_s.results.iterrows():
            code = row.get("Abbreviation", "")
            gp   = row.get("GridPosition", None)
            if code and pd.notna(gp):
                q_grid[code] = int(gp)

        lap1 = race_s.laps[race_s.laps["LapNumber"] == 1]
        for _, row in lap1.iterrows():
            drv = row.get("Driver", "")
            cmp = row.get("Compound", "MEDIUM")
            if drv and pd.notna(cmp):
                q_tyre[drv] = TYRE_ENCODE.get(str(cmp).upper(), 1)

        race_date = str(race_s.date.date())
        has_quali = True
        print(f"  ✓ Real qualifying data: {len(q_best)} drivers")
    except Exception as e:
        print(f"  ! No FastF1 data ({e})")
        print(f"  → Switching to standings-only prediction for upcoming race")
        race_date = str(_date.today())

    # ── Standings + weather ────────────────────────────────────────────────────
    driver_pts, constructor_pts = get_standings(year, round_num)
    air_temp, rainfall, track_temp = get_weather(circuit["lat"], circuit["lon"], race_date)

    # ── Build prediction rows ──────────────────────────────────────────────────
    if has_quali and q_best:
        predict_codes = list(q_best.keys())
    elif year == 2026:
        predict_codes = list(DRIVERS_2026.keys())
    else:
        print("  ✗ Cannot predict: no qualifying data and not a 2026 race.")
        return None

    pole_time = min(q_best.values()) if q_best else None
    median_q  = np.median(list(q_best.values())) if q_best else 90.0

    rows = []
    for code in predict_codes:
        if year == 2026 and code in DRIVERS_2026:
            team = DRIVERS_2026[code]["team"]
            name = DRIVERS_2026[code]["name"]
        else:
            team = "Unknown"
            name = code

        q_time   = q_best.get(code, median_q)
        pole_gap = round(q_time - pole_time, 3) if pole_time else 0.0
        print_code = "ANT" if code == "KIM" else code # Handle FastF1 abbreviation nuances if any
        d_pts    = driver_pts.get(code, 0.0)
        c_pts    = constructor_pts.get(team, 0.0)
        grid     = q_grid.get(code, list(predict_codes).index(code) + 1)
        tyre     = q_tyre.get(code, 1)

        drv_form, team_form, track_hist = get_form_from_csv(code, team, race_name, year, round_num)

        row = {
            "year":               year,
            "race":               race_name,
            "round":              round_num,
            "driver":             code,
            "team":               team,
            "quali_time_s":       round(q_time, 3),
            "grid_position":      grid,
            "driver_points":      d_pts,
            "constructor_points": c_pts,
            "start_tyre":         tyre,
            "circuit_type":       circuit["type"],
            "air_temp_c":         air_temp,
            "rainfall_mm":        rainfall,
            "track_temp_c":       track_temp,
            "pole_gap_s":         pole_gap,
            "driver_form_last3":  drv_form,
            "team_form_last3":    team_form,
            "driver_track_hist":  track_hist,
            "finish_position":    grid, # Temporary placeholder to feed features utility safely
            "_name":              name,
        }
        rows.append(row)

    # ── Process the New Priority Features Live ────────────────────────────────
    df_pred = pd.DataFrame(rows)
    
    print("  → Dynamic calculations for ranks and rolling performance...")
    df_pred = compute_v3_features(df_pred)

    # ── Predict ────────────────────────────────────────────────────────────────
    X_pred  = df_pred[ALL_FEATURES]
    scores  = model.predict(X_pred)
    df_pred["predicted_score"] = scores

    # Rank by score (lower = better finishing position)
    df_pred = df_pred.sort_values("predicted_score").reset_index(drop=True)
    df_pred["predicted_position"] = range(1, len(df_pred) + 1)

    return df_pred


# ── CLI ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "═"*56)
    print("  F1 Race Outcome Predictor V3")
    print("═"*56)
    year      = int(input("\n  Enter year (e.g. 2026): ").strip())
    race_name = input("  Enter race name (e.g. Austria): ").strip()
    round_num = input("  Enter round number (e.g. 8) [optional, press Enter to skip]: ").strip()
    round_num = int(round_num) if round_num else None

    result = predict_race(year, race_name, round_num)
    if result is None:
        print("  Could not generate prediction.")
    else:
        print(f"\n  {'═'*56}")
        print(f"  PREDICTED RESULT — {year} {race_name} Grand Prix")
        print(f"  {'═'*56}")
        print(f"  {'Pos':<5} {'Driver':<22} {'Team':<35} {'Score':>7}")
        print(f"  {'─'*72}")
        for _, row in result.iterrows():
            pos  = int(row["predicted_position"])
            name = row["_name"]
            team = row["team"]
            sc   = row["predicted_score"]
            medal = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else f"P{pos} "
            print(f"  {medal:<5} {name:<22} {team:<35} {sc:>7.2f}")
        print(f"  {'═'*56}\n")

        result.to_csv(f"prediction_{year}_{race_name.replace(' ','_')}.csv", index=False)
        print(f"  Saved to prediction_{year}_{race_name.replace(' ','_')}.csv")
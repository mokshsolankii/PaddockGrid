"""
fetch_data_v3.py — F1 Race Outcome Predictor V3
================================================
Rate-limit safe version:
  - Skips races already in f1_training_data_v3.csv (resume support)
  - Adds 3s delay between sessions to respect 500 calls/hr limit
  - New features: pole_gap_s, driver_form_last3, team_form_last3, driver_track_hist
"""

import fastf1
import pandas as pd
import numpy as np
import requests
import os
import time
from datetime import date as _date
from collections import defaultdict

os.makedirs("f1_cache", exist_ok=True)
fastf1.Cache.enable_cache("f1_cache")

def engineer_priority_v3_features(df):
    # Sort chronologically to ensure rolling windows behave correctly
    df = df.sort_values(by=['year', 'round', 'finish_position']).reset_index(drop=True)
    
    print("Engineering championship ranks...")
    # Calculate Driver and Constructor Championship Ranks for each race weekend
    df['driver_championship_rank'] = df.groupby(['year', 'round'])['driver_points'].rank(ascending=False, method='min')
    df['constructor_championship_rank'] = df.groupby(['year', 'round'])['constructor_points'].rank(ascending=False, method='min')
    
    print("Engineering rolling finishing form (last 5 races)...")
    # Driver rolling average finish (shifted by 1 to prevent data leakage)
    df['driver_avg_finish_last5'] = df.groupby('driver')['finish_position'].transform(
        lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
    )
    
    # Team rolling average finish (shifted by 1 to prevent data leakage)
    df['team_avg_finish_last5'] = df.groupby('team')['finish_position'].transform(
        lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
    )
    
    # Handle initial races where historical rolling data isn't full yet
    # Fallback to their grid position if no previous races exist in dataset
    df['driver_avg_finish_last5'] = df['driver_avg_finish_last5'].fillna(df['grid_position'])
    df['team_avg_finish_last5'] = df['team_avg_finish_last5'].fillna(df['grid_position'])
    
    return df

# Application example:
# df = pd.read_csv("f1_training_data_v3.csv")
# df = engineer_priority_v3_features(df)
# df.to_csv("f1_training_data_v3.csv", index=False)

# ── 2026 verified standings after Round 7 (Barcelona, 15 Jun 2026) ────────────
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

CIRCUIT_INFO = {
    "Monaco":              {"type": 1, "lat": 43.7347, "lon":   7.4206},
    "Spain":               {"type": 0, "lat": 41.5700, "lon":   2.2611},
    "Barcelona-Catalunya": {"type": 0, "lat": 41.5700, "lon":   2.2611},
    "Madrid":              {"type": 1, "lat": 40.4168, "lon":  -3.7038},
    "British":             {"type": 0, "lat": 52.0786, "lon":  -1.0169},
    "Austria":             {"type": 0, "lat": 47.2197, "lon":  14.7647},
    "French":              {"type": 0, "lat": 43.2506, "lon":   5.7917},
    "Belgium":             {"type": 2, "lat": 50.4372, "lon":   5.9714},
    "Hungary":             {"type": 0, "lat": 47.5789, "lon":  19.2486},
    "Netherlands":         {"type": 0, "lat": 52.3888, "lon":   4.5409},
    "Italian":             {"type": 0, "lat": 45.6156, "lon":   9.2811},
    "Emilia Romagna":      {"type": 0, "lat": 44.3439, "lon":  11.7167},
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
    "Mexico":              {"type": 0, "lat": 19.4042, "lon": -99.0907},
    "São Paulo":           {"type": 0, "lat":-23.7036, "lon": -46.6997},
    "Brazil":              {"type": 0, "lat":-23.7036, "lon": -46.6997},
    "Las Vegas":           {"type": 1, "lat": 36.1147, "lon":-115.1728},
}

TYRE_ENCODE = {"SOFT": 0, "MEDIUM": 1, "HARD": 2, "INTERMEDIATE": 3, "WET": 4}


def get_race_weather(lat, lon, date_str):
    try:
        is_past = _date.fromisoformat(date_str) < _date.today()
        base = "archive-api.open-meteo.com/v1/archive" if is_past else "api.open-meteo.com/v1/forecast"
        url  = (f"https://{base}?latitude={lat}&longitude={lon}"
                f"&start_date={date_str}&end_date={date_str}"
                f"&daily=temperature_2m_max,precipitation_sum&timezone=auto")
        d     = requests.get(url, timeout=10).json().get("daily", {})
        temp  = (d.get("temperature_2m_max", [None])[0]) or 25.0
        rain  = (d.get("precipitation_sum",  [None])[0]) or 0.0
        track = temp + 15 if rain < 1 else temp + 5
        print(f"    ✓ Weather: {temp}°C | {rain}mm rain | {track}°C track")
        return {"air_temp_c": temp, "rainfall_mm": rain, "track_temp_c": track}
    except Exception as e:
        print(f"    ✗ Weather ({e}) — defaults")
        return {"air_temp_c": 25.0, "rainfall_mm": 0.0, "track_temp_c": 40.0}


def get_standings_at_race(year, round_number):
    driver_pts, constructor_pts = {}, {}
    if round_number <= 1:
        return driver_pts, constructor_pts
    prev = round_number - 1
    try:
        sl = requests.get(
            f"https://api.jolpi.ca/ergast/f1/{year}/{prev}/driverStandings.json",
            timeout=10).json()["MRData"]["StandingsTable"]["StandingsLists"]
        if sl:
            for s in sl[0]["DriverStandings"]:
                code = s["Driver"].get("code", s["Driver"]["driverId"][:3].upper())
                driver_pts[code] = float(s["points"])
    except Exception as e:
        print(f"    ✗ Driver standings: {e}")
    try:
        sl = requests.get(
            f"https://api.jolpi.ca/ergast/f1/{year}/{prev}/constructorStandings.json",
            timeout=10).json()["MRData"]["StandingsTable"]["StandingsLists"]
        if sl:
            for s in sl[0]["ConstructorStandings"]:
                constructor_pts[s["Constructor"]["name"]] = float(s["points"])
    except Exception as e:
        print(f"    ✗ Constructor standings: {e}")
    return driver_pts, constructor_pts


# ── Rolling form trackers ──────────────────────────────────────────────────────
driver_recent   = defaultdict(list)
team_recent     = defaultdict(list)
driver_at_track = defaultdict(list)

def get_form(history, n=3):
    recent = history[-n:]
    return round(float(np.mean(recent)), 3) if recent else float("nan")

def update_form(rows_this_race):
    for r in rows_this_race:
        driver_recent[r["driver"]].append(r["finish_position"])
        team_recent[r["team"]].append(r["finish_position"])
        driver_at_track[(r["driver"], r["race"])].append(r["finish_position"])


# ── Per-race fetch ─────────────────────────────────────────────────────────────
def fetch_race(year, race_name, round_number):
    print(f"\n{'─'*56}")
    print(f"  [{year}] Round {round_number:02d} — {race_name}")
    print(f"{'─'*56}")
    rows = []

    try:
        # ── Polite delay: 3s between each session load ─────────────────────
        # FastF1 counts ~6 API calls per session.load() for cached misses.
        # 3s gap keeps us well under 500/hr even for uncached races.
        quali = fastf1.get_session(year, race_name, "Q")
        quali.load(telemetry=False, weather=False, messages=False)
        time.sleep(3)

        race  = fastf1.get_session(year, race_name, "R")
        race.load(telemetry=False, weather=False, messages=False)
        time.sleep(3)

        print(f"  ✓ Sessions loaded")
    except Exception as e:
        print(f"  ✗ Session load failed: {e}")
        return []

    try:
        race_date = str(race.date.date())
    except Exception:
        race_date = f"{year}-06-01"

    circuit = CIRCUIT_INFO.get(race_name, {"type": 0, "lat": 25.0, "lon": 55.0})

    print(f"  Fetching weather ({race_date})...")
    weather = get_race_weather(circuit["lat"], circuit["lon"], race_date)
    time.sleep(1)

    if year >= 2026:
        driver_pts_map      = DRIVER_POINTS_2026
        constructor_pts_map = CONSTRUCTOR_POINTS_2026
    else:
        print(f"  Fetching standings (after round {round_number-1})...")
        driver_pts_map, constructor_pts_map = get_standings_at_race(year, round_number)
        time.sleep(1)

    # Qualifying best lap per driver
    q_best = {}
    try:
        for driver in quali.laps["Driver"].unique():
            fastest = quali.laps.pick_drivers(driver).pick_fastest()
            if fastest is not None and not fastest.empty:
                lt = fastest["LapTime"]
                if pd.notna(lt):
                    q_best[driver] = lt.total_seconds()
        print(f"  ✓ Qualifying: {len(q_best)} drivers")
    except Exception as e:
        print(f"  ✗ Qualifying failed: {e}")
        return []

    pole_time = min(q_best.values()) if q_best else None

    grid_pos, start_tyre, finish_pos, team_map = {}, {}, {}, {}
    try:
        for _, row in race.results.iterrows():
            code = row.get("Abbreviation", "")
            gp   = row.get("GridPosition", None)
            if code and pd.notna(gp):
                grid_pos[code] = int(gp)
    except Exception as e:
        print(f"  ! Grid warning: {e}")
    try:
        lap1 = race.laps[race.laps["LapNumber"] == 1]
        for _, row in lap1.iterrows():
            drv = row.get("Driver", "")
            cmp = row.get("Compound", "MEDIUM")
            if drv and pd.notna(cmp):
                start_tyre[drv] = TYRE_ENCODE.get(str(cmp).upper(), 1)
    except Exception as e:
        print(f"  ! Tyre warning: {e}")
    try:
        for _, row in race.results.iterrows():
            code = row.get("Abbreviation", "")
            pos  = row.get("Position", None)
            team = row.get("TeamName", "")
            if code and pd.notna(pos):
                finish_pos[code] = int(float(pos))
            if code and team:
                team_map[code] = str(team)
    except Exception as e:
        print(f"  ✗ Race results failed: {e}")
        return []

    for driver, q_time in q_best.items():
        if driver not in finish_pos:
            continue
        team      = team_map.get(driver, "Unknown")
        pole_gap  = round(q_time - pole_time, 3) if pole_time else 0.0
        form_drv  = get_form(driver_recent[driver])
        form_team = get_form(team_recent[team])
        track_h   = get_form(driver_at_track[(driver, race_name)])

        rows.append({
            "year":               year,
            "race":               race_name,
            "round":              round_number,
            "driver":             driver,
            "team":               team,
            "finish_position":    finish_pos[driver],
            "quali_time_s":       round(q_time, 3),
            "grid_position":      grid_pos.get(driver, 10),
            "driver_points":      driver_pts_map.get(driver, 0.0),
            "constructor_points": constructor_pts_map.get(team, 0.0),
            "start_tyre":         start_tyre.get(driver, 1),
            "circuit_type":       circuit["type"],
            "air_temp_c":         weather["air_temp_c"],
            "rainfall_mm":        weather["rainfall_mm"],
            "track_temp_c":       weather["track_temp_c"],
            "pole_gap_s":         pole_gap,
            "driver_form_last3":  form_drv,
            "team_form_last3":    form_team,
            "driver_track_hist":  track_h,
        })

    update_form(rows)
    print(f"  ✓ {len(rows)} rows collected")
    return rows


RACES = [
    # 2022
    (2022, "Bahrain",         1), (2022, "Saudi Arabia",   2),
    (2022, "Australia",       3), (2022, "Emilia Romagna", 4),
    (2022, "Miami",           5), (2022, "Spain",          6),
    (2022, "Monaco",          7), (2022, "Canada",         8),
    (2022, "British",         9), (2022, "Austria",       10),
    (2022, "French",         11), (2022, "Hungary",       12),
    (2022, "Belgium",        13), (2022, "Netherlands",   14),
    (2022, "Italian",        15), (2022, "Singapore",     16),
    (2022, "Japan",          17), (2022, "United States", 18),
    (2022, "Mexico City",    19), (2022, "São Paulo",     20),
    (2022, "Abu Dhabi",      21),
    # 2023
    (2023, "Bahrain",         1), (2023, "Saudi Arabia",   2),
    (2023, "Australia",       3), (2023, "Azerbaijan",     4),
    (2023, "Miami",           5), (2023, "Monaco",         6),
    (2023, "Spain",           7), (2023, "Canada",         8),
    (2023, "British",         9), (2023, "Austria",       10),
    (2023, "Hungary",        11), (2023, "Belgium",       12),
    (2023, "Netherlands",    13), (2023, "Italian",       14),
    (2023, "Singapore",      15), (2023, "Japan",         16),
    (2023, "Qatar",          17), (2023, "United States", 18),
    (2023, "Mexico City",    19), (2023, "São Paulo",     20),
    (2023, "Las Vegas",      21), (2023, "Abu Dhabi",     22),
    # 2024
    (2024, "Bahrain",         1), (2024, "Saudi Arabia",   2),
    (2024, "Australia",       3), (2024, "Japan",          4),
    (2024, "China",           5), (2024, "Miami",          6),
    (2024, "Emilia Romagna",  7), (2024, "Monaco",         8),
    (2024, "Canada",          9), (2024, "Spain",         10),
    (2024, "Austria",        11), (2024, "British",       12),
    (2024, "Hungary",        13), (2024, "Belgium",       14),
    (2024, "Netherlands",    15), (2024, "Italian",       16),
    (2024, "Azerbaijan",     17), (2024, "Singapore",     18),
    (2024, "United States",  19), (2024, "Mexico City",   20),
    (2024, "São Paulo",      21), (2024, "Las Vegas",     22),
    (2024, "Qatar",          23), (2024, "Abu Dhabi",     24),
    # 2025
    (2025, "Australia",       1), (2025, "China",          2),
    (2025, "Japan",           3), (2025, "Bahrain",        4),
    (2025, "Saudi Arabia",    5), (2025, "Miami",          6),
    (2025, "Emilia Romagna",  7), (2025, "Monaco",         8),
    (2025, "Spain",           9), (2025, "Canada",        10),
    (2025, "Austria",        11), (2025, "British",       12),
    (2025, "Belgium",        13), (2025, "Hungary",       14),
    (2025, "Netherlands",    15), (2025, "Italian",       16),
    (2025, "Azerbaijan",     17), (2025, "Singapore",     18),
    (2025, "United States",  19), (2025, "Mexico City",   20),
    (2025, "São Paulo",      21), (2025, "Las Vegas",     22),
    (2025, "Qatar",          23), (2025, "Abu Dhabi",     24),
    # 2026 — completed only
    (2026, "Australia",           1),
    (2026, "China",               2),
    (2026, "Japan",               3),
    (2026, "Miami",               4),
    (2026, "Canada",              5),
    (2026, "Monaco",              6),
    (2026, "Barcelona-Catalunya", 7),
]


if __name__ == "__main__":
    # ── Resume: load already-fetched races ─────────────────────────────────────
    CSV_OUT = "f1_training_data_v3.csv"
    existing_rows = []
    already_done  = set()

    if os.path.exists(CSV_OUT):
        existing_df = pd.read_csv(CSV_OUT)
        existing_rows = existing_df.to_dict("records")
        already_done  = set(zip(existing_df["year"], existing_df["race"]))

        # Rebuild form trackers from existing data so rolling stats stay correct
        for rec in sorted(existing_rows, key=lambda r: (r["year"], r["round"])):
            driver_recent[rec["driver"]].append(rec["finish_position"])
            team_recent[rec["team"]].append(rec["finish_position"])
            driver_at_track[(rec["driver"], rec["race"])].append(rec["finish_position"])

        print(f"\n  ✓ Resuming — {len(already_done)} races already in CSV, skipping them")

    all_rows = list(existing_rows)
    failed   = []

    remaining = [(y, r, n) for y, r, n in RACES if (y, r) not in already_done]

    print(f"\n{'═'*56}")
    print(f"  F1 Predictor V3 — Data Fetch (Resume-Safe)")
    print(f"  {len(remaining)} races to fetch  |  {len(already_done)} already done")
    print(f"  Rate-limit delay: 3s between session loads")
    print(f"{'═'*56}")

    for i, (year, race_name, round_num) in enumerate(remaining, 1):
        print(f"\n[{i}/{len(remaining)}]", end="")
        try:
            rows = fetch_race(year, race_name, round_num)
            if rows:
                all_rows.extend(rows)
            else:
                failed.append(f"{year} {race_name}")
        except Exception as e:
            print(f"  ✗ Unexpected: {e}")
            failed.append(f"{year} {race_name}")

        # Save after every race — so progress is never lost if interrupted
        df_so_far = pd.DataFrame(all_rows)
        df_so_far.to_csv(CSV_OUT, index=False)

    # Final fill NaN form values with median
    df = pd.read_csv(CSV_OUT)
    for col in ["driver_form_last3", "team_form_last3", "driver_track_hist"]:
        median_val = df[col].median()
        filled = df[col].isna().sum()
        df[col] = df[col].fillna(median_val)
        if filled:
            print(f"  Filled {filled} NaN in '{col}' with median {median_val:.2f}")
    df.to_csv(CSV_OUT, index=False)

    print(f"\n{'═'*56}")
    print(f"  ✓ Saved: {CSV_OUT}")
    print(f"  ✓ Rows:       {len(df)}")
    print(f"  ✓ Races done: {df[['year','race']].drop_duplicates().shape[0]}")
    if failed:
        print(f"\n  Skipped ({len(failed)}):")
        for f in failed:
            print(f"    - {f}")
    print(f"\n  Next → python train_v3.py")
    print(f"{'═'*56}\n")

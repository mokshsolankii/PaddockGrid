import fastf1
import pandas as pd
import requests
import os
import time
from datetime import date as _date

# ── Cache setup ────────────────────────────────────────────────────────────────
os.makedirs("f1_cache", exist_ok=True)
fastf1.Cache.enable_cache("f1_cache")

# ── Circuit metadata ───────────────────────────────────────────────────────────
# type: 0=permanent, 1=street, 2=hybrid
CIRCUIT_INFO = {
    # Europe
    "Monaco":              {"type": 1, "lat": 43.73,  "lon": 7.42},
    "Barcelona-Catalunya": {"type": 0, "lat": 41.57,  "lon": 2.26},
    "Spain":               {"type": 0, "lat": 41.57,  "lon": 2.26},   # old name
    "Madrid":              {"type": 1, "lat": 40.41,  "lon": -3.70},  # new Madring street circuit
    "British":             {"type": 0, "lat": 52.07,  "lon": -1.02},
    "Austria":             {"type": 0, "lat": 47.22,  "lon": 14.76},
    "Belgium":             {"type": 0, "lat": 50.44,  "lon": 5.97},
    "Hungary":             {"type": 0, "lat": 47.58,  "lon": 19.25},
    "Netherlands":         {"type": 0, "lat": 52.39,  "lon": 4.54},
    "Italian":             {"type": 0, "lat": 45.62,  "lon": 9.29},
    "Emilia Romagna":      {"type": 0, "lat": 44.34,  "lon": 11.71},  # 2022-2025 only
    # Middle East / Asia
    "Bahrain":             {"type": 0, "lat": 26.03,  "lon": 50.51},
    "Saudi Arabia":        {"type": 1, "lat": 21.63,  "lon": 39.10},
    "Japan":               {"type": 0, "lat": 34.84,  "lon": 136.54},
    "China":               {"type": 0, "lat": 31.34,  "lon": 121.22},
    "Azerbaijan":          {"type": 1, "lat": 40.37,  "lon": 49.85},
    "Singapore":           {"type": 1, "lat": 1.29,   "lon": 103.86},
    "Qatar":               {"type": 0, "lat": 25.49,  "lon": 51.45},
    "Abu Dhabi":           {"type": 0, "lat": 24.47,  "lon": 54.60},
    # Americas
    "Australia":           {"type": 1, "lat": -37.84, "lon": 144.97},
    "Miami":               {"type": 1, "lat": 25.96,  "lon": -80.24},
    "Canada":              {"type": 1, "lat": 45.50,  "lon": -73.52},
    "United States":       {"type": 1, "lat": 30.13,  "lon": -97.63},
    "Mexico City":         {"type": 0, "lat": 19.40,  "lon": -99.09},
    "São Paulo":           {"type": 0, "lat": -23.70, "lon": -46.70},
    "Las Vegas":           {"type": 1, "lat": 36.11,  "lon": -115.17},
    "Mexico":              {"type": 0, "lat": 19.40,  "lon": -99.09},
    "Brazil":              {"type": 0, "lat": -23.70, "lon": -46.70},
}

# Tyre compound encoding
TYRE_ENCODE = {"SOFT": 0, "MEDIUM": 1, "HARD": 2, "INTERMEDIATE": 3, "WET": 4}

# ── Helper: standings from jolpi.ca (Ergast mirror) ───────────────────────────
def get_standings_at_race(year, round_number):
    driver_pts = {}
    constructor_pts = {}
    if round_number <= 1:
        return driver_pts, constructor_pts
    prev = round_number - 1
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/{prev}/driverStandings.json"
        r = requests.get(url, timeout=10)
        sl = r.json()["MRData"]["StandingsTable"]["StandingsLists"]
        if sl:
            for s in sl[0]["DriverStandings"]:
                code = s["Driver"].get("code", s["Driver"]["driverId"][:3].upper())
                driver_pts[code] = float(s["points"])
    except Exception as e:
        print(f"    Driver standings failed: {e}")
    try:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/{prev}/constructorStandings.json"
        r = requests.get(url, timeout=10)
        sl = r.json()["MRData"]["StandingsTable"]["StandingsLists"]
        if sl:
            for s in sl[0]["ConstructorStandings"]:
                constructor_pts[s["Constructor"]["name"]] = float(s["points"])
    except Exception as e:
        print(f"    Constructor standings failed: {e}")
    return driver_pts, constructor_pts


# ── Main fetch per race ────────────────────────────────────────────────────────
def fetch_race(year, race_name, round_number):
    print(f"\n{'─'*52}")
    print(f"  {year} | Round {round_number} | {race_name}")
    print(f"{'─'*52}")
    rows = []

    try:
        quali = fastf1.get_session(year, race_name, "Q")
        quali.load(telemetry=False, weather=False, messages=False)
        race  = fastf1.get_session(year, race_name, "R")
        race.load(telemetry=False, weather=False, messages=False)
        print(f"  ✓ FastF1 sessions loaded")
    except Exception as e:
        print(f"SESSION FAILED: {year} {race_name}")
        print(repr(e))
        return []

    race_date = str(race.date.date()) if hasattr(race, "date") and race.date else f"{year}-01-01"
    circuit   = CIRCUIT_INFO.get(race_name, {"type": 0, "lat": 25.0, "lon": 55.0})

    print(f"  Fetching weather for {race_date}...")
    weather = get_race_weather(circuit["lat"], circuit["lon"], race_date)
    time.sleep(0.3)

    print(f"  Fetching standings at round {round_number}...")
    driver_pts_map, constructor_pts_map = get_standings_at_race(
    year,
    round_number
    )
    time.sleep(0.3)
    # Qualifying — best lap + avg throttle
    q_best     = {}
    try:
        for driver in quali.laps["Driver"].unique():
            d_laps = quali.laps.pick_drivers(driver).pick_fastest()
            if d_laps is not None and not d_laps.empty:
                lt = d_laps["LapTime"]
                if pd.notna(lt):
                    q_best[driver] = lt.total_seconds()
        print(f"  ✓ Qualifying: {len(q_best)} drivers")
    except Exception as e:
        print(f"  ✗ Qualifying failed: {e}")
        return []
    pole_time = min(q_best.values()) if q_best else None

    # Grid positions
    grid_pos = {}
    try:
        for _, row in race.results.iterrows():
            code = row.get("Abbreviation", "")
            gp   = row.get("GridPosition", None)
            if code and pd.notna(gp):
                grid_pos[code] = int(gp)
    except Exception as e:
        print(f"  Warning grid pos: {e}")

    # Starting tyre
    start_tyre = {}
    try:
        lap1 = race.laps[race.laps["LapNumber"] == 1]
        for _, row in lap1.iterrows():
            drv = row.get("Driver", "")
            cmp = row.get("Compound", "MEDIUM")
            if drv and pd.notna(cmp):
                start_tyre[drv] = TYRE_ENCODE.get(str(cmp).upper(), 1)
    except Exception as e:
        print(f"  Warning tyre: {e}")

    # Race results
    finish_pos = {}
    team_map   = {}
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

    # Assemble
    for driver, q_time in q_best.items():
        if driver not in finish_pos:
            continue
        team = team_map.get(driver, "Unknown")

        lookup_team = TEAM_MAPPING.get(
           team,
           team
)

d_pts = driver_pts_map.get(driver, 0.0)

c_pts = constructor_pts_map.get(
    lookup_team,
    0.0
)
rows.append({
    "year": year,
    "race": race_name,
    "round": round_number,

    "driver": driver,
    "team": team,

    "quali_time_s": round(q_time, 3),

    "pole_gap_s": round(
        q_time - pole_time,
        3
    ) if pole_time else 0,

    "finish_position": finish_pos[driver],

    "grid_position": grid_pos.get(driver, 10),

    "driver_points": d_pts,
    "constructor_points": c_pts,

    "start_tyre": start_tyre.get(driver, 1),

    "circuit_type": circuit["type"]
})

print(f"  ✓ {len(rows)} rows collected")


# ── Race list — CORRECTED & COMPLETE ──────────────────────────────────────────
# Format: (year, fastf1_race_name, ergast_round_number)
RACES = [
    # ── 2022 (22 races) ────────────────────────────────────────────────────────
    (2022, "Bahrain",        1), (2022, "Saudi Arabia",  2),
    (2022, "Australia",      3), (2022, "Emilia Romagna",4),
    (2022, "Miami",          5), (2022, "Spain",         6),
    (2022, "Monaco",         7), (2022, "Canada",        8),
    (2022, "British",        9), (2022, "Austria",      10),
    (2022, "French",        11), (2022, "Hungary",      12),
    (2022, "Belgium",       13), (2022, "Netherlands",  14),
    (2022, "Italian",       15), (2022, "Singapore",    16),
    (2022, "Japan",         17), (2022, "United States",18),
    (2022, "Mexico City",   19), (2022, "São Paulo",    20),
    (2022, "Abu Dhabi",     21),

    # ── 2023 (23 races) ────────────────────────────────────────────────────────
    (2023, "Bahrain",        1), (2023, "Saudi Arabia",  2),
    (2023, "Australia",      3), (2023, "Azerbaijan",    4),
    (2023, "Miami",          5), (2023, "Monaco",        6),
    (2023, "Spain",          7), (2023, "Canada",        8),
    (2023, "British",        9), (2023, "Austria",      10),
    (2023, "Hungary",       11), (2023, "Belgium",      12),
    (2023, "Netherlands",   13), (2023, "Italian",      14),
    (2023, "Singapore",     15), (2023, "Japan",        16),
    (2023, "Qatar",         17), (2023, "United States",18),
    (2023, "Mexico City",   19), (2023, "São Paulo",    20),
    (2023, "Las Vegas",     21), (2023, "Abu Dhabi",    22),

    # ── 2024 (24 races) ────────────────────────────────────────────────────────
    (2024, "Bahrain",        1), (2024, "Saudi Arabia",  2),
    (2024, "Australia",      3), (2024, "Japan",         4),
    (2024, "China",          5), (2024, "Miami",         6),
    (2024, "Emilia Romagna", 7), (2024, "Monaco",        8),
    (2024, "Canada",         9), (2024, "Spain",        10),
    (2024, "Austria",       11), (2024, "British",      12),
    (2024, "Hungary",       13), (2024, "Belgium",      14),
    (2024, "Netherlands",   15), (2024, "Italian",      16),
    (2024, "Azerbaijan",    17), (2024, "Singapore",    18),
    (2024, "United States", 19), (2024, "Mexico City",  20),
    (2024, "São Paulo",     21), (2024, "Las Vegas",    22),
    (2024, "Qatar",         23), (2024, "Abu Dhabi",    24),

    # ── 2025 (24 races) ────────────────────────────────────────────────────────
    (2025, "Australia",      1), (2025, "China",         2),
    (2025, "Japan",          3), (2025, "Bahrain",       4),
    (2025, "Saudi Arabia",   5), (2025, "Miami",         6),
    (2025, "Emilia Romagna", 7), (2025, "Monaco",        8),
    (2025, "Spain",          9), (2025, "Canada",       10),
    (2025, "Austria",       11), (2025, "British",      12),
    (2025, "Belgium",       13), (2025, "Hungary",      14),
    (2025, "Netherlands",   15), (2025, "Italian",      16),
    (2025, "Azerbaijan",    17), (2025, "Singapore",    18),
    (2025, "United States", 19), (2025, "Mexico City",  20),
    (2025, "São Paulo",     21), (2025, "Las Vegas",    22),
    (2025, "Qatar",         23), (2025, "Abu Dhabi",    24),
]


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    all_rows = []
    failed   = []

    print(f"\n{'═'*52}")
    print(f"  F1 Race Predictor V2 — Data Fetch")
    print(f"  {len(RACES)} races to process (2022–2026)")
    print(f"{'═'*52}")

    for i, (year, race_name, round_num) in enumerate(RACES, 1):
        print(f"\n[{i}/{len(RACES)}]", end="")
        try:
            rows = fetch_race(year, race_name, round_num)
            if rows:
                all_rows.extend(rows)
            else:
                failed.append(f"{year} {race_name}")
        except Exception as e:
           print(f"FAILED: {year} {race_name}")
           print(f"ERROR: {repr(e)}")
        time.sleep(1)

    df = pd.DataFrame(all_rows)
    df.to_csv("f1_training_data_v2.csv", index=False)

    print(f"\n{'═'*52}")
    print(f"  ✓ Saved: f1_training_data_v2.csv")
    print(f"  ✓ Total rows:  {len(df)}")
    print(f"  ✓ Races done:  {df[['year','race']].drop_duplicates().shape[0]}")
    print(f"  ✓ Columns:     {list(df.columns)}")
    if failed:
        print(f"\n  Skipped ({len(failed)}):")
        for f in failed:
            print(f"    - {f}")
    print(f"\n  Next: python train_v2.py")
    print(f"{'═'*52}\n")

print("\nRows per race:")

print(
    df.groupby(
        ["year", "race"]
    )
    .size()
    .sort_values()
    .head(20)
)

print("\nFailed races:")

for f in failed:
    print(f)

    df = pd.DataFrame(all_rows)

    print("\nDATASET SUMMARY")
print("Rows:", len(df))

if len(df) > 0:
    print(
        df.groupby(["year","race"])
          .size()
          .describe()
    )
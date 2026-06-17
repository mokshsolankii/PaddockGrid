"""
train_v3.py — F1 Race Outcome Predictor V3 (improved)
======================================================
Key changes vs first version:
  - Rolling cross-validation by year (more realistic evaluation)
  - CatBoost tuned for F1 data patterns
  - Saves full feature importance breakdown
  - MAE evaluated per-year so you see where model struggles
"""

import pandas as pd
import numpy as np
import pickle
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

print("\n" + "═"*56)
print("  F1 Predictor V3 — Training (Improved)")
print("═"*56)

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

df = pd.read_csv("f1_training_data_v3.csv")
print(f"  Dataset : {df.shape[0]} rows × {df.shape[1]} cols")
print(f"  Years   : {sorted(df['year'].unique())}")

# ── Features ───────────────────────────────────────────────────────────────────
CAT_FEATURES = ["driver", "team", "race"]
NUM_FEATURES = [
    "year", "round",
    "quali_time_s", "grid_position", "pole_gap_s",
    "driver_points", "constructor_points",
    "start_tyre", "circuit_type",
    "air_temp_c", "rainfall_mm", "track_temp_c",
    "driver_form_last3", "team_form_last3", "driver_track_hist",
    # --- New Priority Features Added Below ---
    "driver_championship_rank", "constructor_championship_rank",
    "driver_avg_finish_last5", "team_avg_finish_last5"
]
ALL_FEATURES = NUM_FEATURES + CAT_FEATURES
TARGET = "finish_position"

X = df[ALL_FEATURES]
y = df[TARGET]
cat_idx = [ALL_FEATURES.index(c) for c in CAT_FEATURES]

# ── Evaluation: rolling year cross-validation ──────────────────────────────────
# Train on all years up to N, test on year N+1
# This mimics real-world usage — you never have future data
print(f"\n  Rolling year cross-validation:")
print(f"  {'Train years':<30} {'Test year':<12} {'MAE':>6} {'Top3':>7} {'Top10':>7}")
print(f"  {'─'*65}")

yearly_maes = []
for test_year in [2023, 2024, 2025, 2026]:
    train_mask = df["year"] < test_year
    test_mask  = df["year"] == test_year
    if test_mask.sum() == 0:
        continue

    X_tr, X_te = X[train_mask], X[test_mask]
    y_tr, y_te = y[train_mask], y[test_mask]

    m = CatBoostRegressor(
        iterations=800, learning_rate=0.05, depth=7,
        loss_function="MAE", eval_metric="MAE",
        cat_features=cat_idx, random_seed=42, verbose=0,
    )
    m.fit(Pool(X_tr, y_tr, cat_features=cat_idx))
    preds     = np.clip(np.round(m.predict(X_te)), 1, 20).astype(int)
    actual    = y_te.values
    mae       = mean_absolute_error(actual, preds)
    top3_acc  = np.mean((preds <= 3)  == (actual <= 3))
    top10_acc = np.mean((preds <= 10) == (actual <= 10))
    yearly_maes.append(mae)

    train_yrs = sorted(df[train_mask]["year"].unique())
    print(f"  {str(train_yrs):<30} {test_year:<12} {mae:>6.3f} {top3_acc*100:>6.1f}% {top10_acc*100:>6.1f}%")

print(f"  {'─'*65}")
print(f"  Average MAE across years: {np.mean(yearly_maes):.3f}")

# ── Final model: train on ALL data ────────────────────────────────────────────
# For production prediction we use everything available
print(f"\n  Training final model on all {len(df)} rows...")

# Hold out last 20% of races (by round) for final MAE report
cutoff = df["round"].quantile(0.80)
train_mask = df["round"] <= cutoff
X_train, X_test = X[train_mask], X[~train_mask]
y_train, y_test = y[train_mask], y[~train_mask]

model = CatBoostRegressor(
    iterations=1200,
    learning_rate=0.04,
    depth=8,
    loss_function="MAE",
    eval_metric="MAE",
    cat_features=cat_idx,
    early_stopping_rounds=60,
    l2_leaf_reg=3,
    random_seed=42,
    verbose=100,
)

model.fit(
    Pool(X_train, y_train, cat_features=cat_idx),
    eval_set=Pool(X_test, y_test, cat_features=cat_idx),
)

preds     = model.predict(X_test)
preds_int = np.clip(np.round(preds), 1, 20).astype(int)
actual    = y_test.values

mae       = mean_absolute_error(actual, preds)
top3_acc  = np.mean((preds_int <= 3)  == (actual <= 3))
top10_acc = np.mean((preds_int <= 10) == (actual <= 10))

print(f"\n  ── Final model results ──")
print(f"  MAE        : {mae:.3f} positions")
print(f"  Top-3  acc : {top3_acc*100:.1f}%")
print(f"  Top-10 acc : {top10_acc*100:.1f}%")

# MAE per year breakdown
print(f"\n  MAE breakdown by year (test set):")
test_df = df[~train_mask].copy()
test_df["pred"] = preds_int
for yr in sorted(test_df["year"].unique()):
    yr_df  = test_df[test_df["year"] == yr]
    yr_mae = mean_absolute_error(yr_df["finish_position"], yr_df["pred"])
    races  = yr_df["race"].nunique()
    print(f"    {yr} ({races:2d} races): MAE {yr_mae:.3f}")

# ── Feature importances ────────────────────────────────────────────────────────
importances = model.get_feature_importance()
feat_imp    = sorted(zip(ALL_FEATURES, importances), key=lambda x: -x[1])
print(f"\n  Feature importances:")
for feat, imp in feat_imp:
    bar = "█" * int(imp / 1.5)
    print(f"    {feat:<25} {imp:>6.2f}%  {bar}")

# ── Save ───────────────────────────────────────────────────────────────────────
with open("f1_model_v3.pkl", "wb") as f:
    pickle.dump({
        "model":        model,
        "features":     ALL_FEATURES,
        "cat_features": CAT_FEATURES,
        "num_features": NUM_FEATURES,
        "cat_idx":      cat_idx,
        "mae":          round(mae, 3),
        "top3_acc":     round(top3_acc, 3),
        "top10_acc":    round(top10_acc, 3),
    }, f)

print(f"\n  ✓ Saved: f1_model_v3.pkl")
print(f"  Next  → python predict_race_v3.py")
print("═"*56 + "\n")

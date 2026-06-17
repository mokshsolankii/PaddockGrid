import pandas as pd
import numpy as np

def compute_v3_features(df):
    """
    Engineers high-priority features including championship ranks and 
    shifted rolling averages to prevent data leakage.
    """
    # 1. Ensure data is sorted chronologically for correct rolling execution
    df = df.sort_values(by=['year', 'round', 'finish_position']).reset_index(drop=True)
    
    print("-> Engineering championship ranks...")
    # Calculate ranks based on points accumulated up to that weekend
    df['driver_championship_rank'] = df.groupby(['year', 'round'])['driver_points'].rank(ascending=False, method='min')
    df['constructor_championship_rank'] = df.groupby(['year', 'round'])['constructor_points'].rank(ascending=False, method='min')
    
    print("-> Engineering rolling finishing form (last 5 races)...")
    # Shift by 1 is CRITICAL to prevent the model from knowing the future result during training
    df['driver_avg_finish_last5'] = df.groupby('driver')['finish_position'].transform(
        lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
    )
    
    df['team_avg_finish_last5'] = df.groupby('team')['finish_position'].transform(
        lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
    )
    
    # 3. Fallback logic for early-season or new entries with no historical window
    df['driver_avg_finish_last5'] = df['driver_avg_finish_last5'].fillna(df['grid_position'])
    df['team_avg_finish_last5'] = df['team_avg_finish_last5'].fillna(df['grid_position'])
    
    return df

if __name__ == "__main__":
    # Test script and update existing dataset
    try:
        data_path = "f1_training_data_v3.csv"
        dataset = pd.read_csv(data_path)
        print(f"Input dataset shape: {dataset.shape}")
        
        updated_dataset = compute_v3_features(dataset)
        updated_dataset.to_csv(data_path, index=False)
        print(f"✓ Successfully updated {data_path} with 4 new priority features!")
        print(f"New dataset shape: {updated_dataset.shape}")
    except FileNotFoundError:
        print(f"Error: Could not find {data_path}. Make sure it is in this directory.")
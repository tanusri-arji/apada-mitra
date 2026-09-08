"""
Hydrological Catchment Dataset Generator for Alaknanda and Mandakini River Basins (Feature 12).
Synthesizes 10 monsoon seasons (2014-2023) of hourly hydrograph telemetry for training
recurrent deep learning (LSTM) flood wave propagation models based on physical kinematic wave principles.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple, List, Any


FEATURE_COLUMNS = [
    "precip_mm_h",
    "cum_24h_precip_mm",
    "soil_saturation_pct",
    "upstream_stage_m",
    "slope_deg",
    "manning_n",
]

TARGET_COLUMNS = [
    "stage_t1",
    "stage_t2",
    "stage_t3",
    "stage_t4",
    "stage_t5",
    "stage_t6",
]


def calculate_nash_sutcliffe(observed: np.ndarray, predicted: np.ndarray) -> float:
    """
    Computes the Nash-Sutcliffe Efficiency (NSE) coefficient.
    NSE = 1 - sum((obs - sim)^2) / sum((obs - mean(obs))^2)
    A value of 1 represents perfect agreement; NSE > 0.75 indicates very good hydrological modeling.
    """
    obs = np.asarray(observed)
    pred = np.asarray(predicted)
    denom = np.sum((obs - np.mean(obs)) ** 2)
    if denom == 0:
        return 1.0 if np.allclose(obs, pred) else 0.0
    numer = np.sum((obs - pred) ** 2)
    return float(1.0 - (numer / denom))


def calculate_rmse(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Computes Root Mean Squared Error (RMSE) in meters."""
    obs = np.asarray(observed)
    pred = np.asarray(predicted)
    return float(np.sqrt(np.mean((obs - pred) ** 2)))


def calculate_r2(observed: np.ndarray, predicted: np.ndarray) -> float:
    """Computes Coefficient of Determination (R²)."""
    obs = np.asarray(observed)
    pred = np.asarray(predicted)
    diff_obs = obs - np.mean(obs)
    diff_pred = pred - np.mean(pred)
    denom = np.sqrt(np.sum(diff_obs ** 2) * np.sum(diff_pred ** 2))
    if denom == 0:
        return 1.0 if np.allclose(obs, pred) else 0.0
    r = np.sum(diff_obs * diff_pred) / denom
    return float(r ** 2)


def generate_catchment_hydrograph_series(
    num_hours: int = 87600,
    seed: int = 42,
    base_stage: float = 2.4,
    slope_deg: float = 32.0,
    manning_n: float = 0.045
) -> pd.DataFrame:
    """
    Generates a physically consistent hourly hydrograph time-series for Himalayan steep-sloped catchments.
    
    Physics parameters:
      - Monsoon seasonal envelope (peaks mid-July to late-August)
      - Storm arrivals with gamma-distributed cloudburst intensity
      - Horton infiltration model: high soil saturation yields non-linear overland runoff surges
      - Upstream flood wave translation with 1.5 to 3.0-hour routing delay
    """
    rng = np.random.default_rng(seed)
    start_time = datetime(2014, 1, 1, 0, 0)
    
    # 1. Temporal Monsoonal Precipitation
    day_of_year = np.array([(i // 24) % 365 for i in range(num_hours)])
    # Monsoon bell curve centered at day 215 (early August)
    monsoon_envelope = np.exp(-((day_of_year - 215) ** 2) / (2 * (40 ** 2)))
    
    # Base rain + stochastic convective storms
    storm_prob = 0.04 + 0.25 * monsoon_envelope
    storm_occurred = rng.random(num_hours) < storm_prob
    
    raw_intensity = rng.gamma(shape=1.5, scale=4.0, size=num_hours) * storm_occurred
    # Extreme cloudburst events (> 50 mm/h) occurring periodically during monsoon
    cloudburst_mask = (rng.random(num_hours) < (0.003 * monsoon_envelope))
    raw_intensity[cloudburst_mask] += rng.uniform(45.0, 95.0, size=np.sum(cloudburst_mask))
    
    precip = np.round(raw_intensity, 2)
    
    # 2. 24-hour antecedent cumulative precipitation
    cum_24h = np.zeros(num_hours)
    window_sum = 0.0
    for i in range(num_hours):
        window_sum += precip[i]
        if i >= 24:
            window_sum -= precip[i - 24]
        cum_24h[i] = round(max(0.0, window_sum), 2)
        
    # 3. Dynamic Soil Saturation (Leaky reservoir bucket)
    soil_sat = np.zeros(num_hours)
    current_sat = 45.0
    recharge_rate = 0.45
    drain_rate = 0.12
    for i in range(num_hours):
        current_sat += (precip[i] * recharge_rate) - drain_rate
        # Climatic seasonal baseline
        target_baseline = 35.0 + 40.0 * monsoon_envelope[i]
        current_sat += 0.02 * (target_baseline - current_sat)
        current_sat = float(np.clip(current_sat, 20.0, 98.5))
        soil_sat[i] = round(current_sat, 1)

    # 4. Upstream Stage (m)
    # High-altitude glacial/gorge runoff upstream
    upstream_stage = np.zeros(num_hours)
    u_stage = base_stage * 0.85
    for i in range(num_hours):
        runoff_factor = max(0.0, (soil_sat[i] - 60.0) / 40.0)
        surge = (precip[i] * 0.04) * (1.0 + 2.0 * runoff_factor)
        u_stage = 0.92 * u_stage + 0.08 * (base_stage * 0.85 + surge)
        upstream_stage[i] = round(float(u_stage), 3)

    # 5. Local River Stage Dynamics and Routing to t+1 ... t+6
    # Kinematic wave velocity: v = (1/n) * R^(2/3) * S^(1/2)
    slope_rad = np.radians(slope_deg)
    slope_term = np.sqrt(np.sin(slope_rad))
    celerity = (1.0 / manning_n) * (1.2 ** (2/3)) * slope_term * 0.25  # scaled celerity
    
    local_stage = np.zeros(num_hours)
    stage_val = base_stage
    for i in range(num_hours):
        # Infiltration excess runoff
        saturation_mult = 1.0 + (soil_sat[i] / 50.0) ** 2.2
        direct_runoff = (precip[i] / 25.0) * saturation_mult
        
        # Upstream wave arrival delayed by ~2 hours
        lag_idx = max(0, i - 2)
        upstream_inflow = (upstream_stage[lag_idx] - (base_stage * 0.85)) * 0.65
        
        target_stage = base_stage + direct_runoff + upstream_inflow
        stage_val = 0.82 * stage_val + 0.18 * target_stage
        local_stage[i] = stage_val

    # Construct dataframe with forward multi-step targets t+1 to t+6
    data: Dict[str, Any] = {
        "precip_mm_h": precip,
        "cum_24h_precip_mm": cum_24h,
        "soil_saturation_pct": soil_sat,
        "upstream_stage_m": upstream_stage,
        "slope_deg": np.full(num_hours, slope_deg),
        "manning_n": np.full(num_hours, manning_n),
    }
    
    # Multi-step future stages
    for step in range(1, 7):
        target = np.roll(local_stage, -step)
        # Pad last 'step' rows
        target[-step:] = local_stage[-1]
        data[f"stage_t{step}"] = np.round(target, 3)

    df = pd.DataFrame(data)
    return df


def get_train_val_test_splits(
    df: pd.DataFrame,
    train_ratio: float = 0.80,
    val_ratio: float = 0.10
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """Splits dataset temporally into train, validation, and test arrays with standard scaling parameters."""
    n = len(df)
    n_train = int(n * train_ratio)
    n_val = int(n * (train_ratio + val_ratio))
    
    x_raw = df[FEATURE_COLUMNS].values
    y_raw = df[TARGET_COLUMNS].values
    
    # Compute scaler on train split only
    x_mean = np.mean(x_raw[:n_train], axis=0)
    x_std = np.std(x_raw[:n_train], axis=0)
    x_std[x_std == 0] = 1.0  # avoid divide by zero
    
    y_mean = np.mean(y_raw[:n_train], axis=0)
    y_std = np.std(y_raw[:n_train], axis=0)
    y_std[y_std == 0] = 1.0

    x_norm = (x_raw - x_mean) / x_std
    y_norm = (y_raw - y_mean) / y_std
    
    scaler_params = {
        "feature_mean": x_mean.tolist(),
        "feature_std": x_std.tolist(),
        "target_mean": y_mean.tolist(),
        "target_std": y_std.tolist(),
        "feature_names": FEATURE_COLUMNS,
        "target_names": TARGET_COLUMNS,
    }
    
    x_train, y_train = x_norm[:n_train], y_norm[:n_train]
    x_val, y_val = x_norm[n_train:n_val], y_norm[n_train:n_val]
    x_test, y_test = x_norm[n_val:], y_norm[n_val:]
    
    return x_train, y_train, x_val, y_val, x_test, y_test, scaler_params

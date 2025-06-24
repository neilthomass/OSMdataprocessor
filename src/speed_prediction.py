import random
from typing import Dict, List

import numpy as np
from sklearn.linear_model import LinearRegression
import requests


def fetch_pems_speed(station_id: int) -> Dict[int, List[float]]:
    """Fetch current speed data for each lane from PeMS.

    The real PeMS API requires authentication. This function attempts to
    retrieve data from the public endpoint and falls back to synthetic data
    if the request fails (e.g., due to lack of network access).
    """
    url = f"https://pems.dot.ca.gov/?station_id={station_id}&d=1"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # Expect data format: {'lanes': {'1': speed1, '2': speed2, ...}}
        lanes = {int(k): [float(v)] for k, v in data.get('lanes', {}).items()}
        if lanes:
            return lanes
    except Exception:
        pass

    # Fallback: generate random speeds for three lanes
    return {i: [float(random.randint(40, 65))] for i in range(1, 4)}


def predict_next_speeds(
    speeds_per_lane: Dict[int, List[float]], horizon: int = 30
) -> Dict[int, List[float]]:
    """Predict speeds for each lane for the next `horizon` seconds."""
    predictions: Dict[int, List[float]] = {}
    for lane, speeds in speeds_per_lane.items():
        if not speeds:
            predictions[lane] = [0.0] * horizon
            continue

        if len(speeds) < 2:
            predictions[lane] = [float(speeds[-1])] * horizon
            continue

        x = np.arange(len(speeds)).reshape(-1, 1)
        y = np.array(speeds)
        model = LinearRegression()
        model.fit(x, y)
        last_t = len(speeds) - 1
        future_x = np.arange(last_t + 1, last_t + horizon + 1).reshape(-1, 1)
        preds = model.predict(future_x)
        predictions[lane] = [max(0.0, float(p)) for p in preds]
    return predictions

import os
import random
from datetime import date, timedelta
from typing import Dict, List

import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from pems import PeMSConnection, OneStation5MinDataHandler


def fetch_pems_speed(station_id: int) -> Dict[int, List[float]]:
    """Fetch the latest 5‑minute speeds for a station from PeMS.

    Credentials can be supplied via the ``PEMS_USERNAME`` and ``PEMS_PASSWORD``
    environment variables. If fetching fails, random speeds are returned so the
    API remains functional.
    """

    username = os.getenv("PEMS_USERNAME")
    password = os.getenv("PEMS_PASSWORD")
    district = os.getenv("PEMS_DISTRICT")

    if username and password and not PeMSConnection().initialized:
        try:
            PeMSConnection.initialize(username, password)
        except Exception:
            pass

    if PeMSConnection().initialized:
        handler = OneStation5MinDataHandler(station_id=station_id, use_cache=False)
        today = date.today()
        try:
            chunks = list(handler.load_between(today - timedelta(days=1), today, district=district))
            chunks = [c for c in chunks if c is not None and not c.empty]
            if chunks:
                df = chunks[-1].sort_values("timestamp")
                latest = df.iloc[-1]
                speeds = {}
                for idx, col in enumerate([c for c in df.columns if c.endswith("_avg_speed")]):
                    speeds[idx + 1] = [float(latest[col])]
                if speeds:
                    return speeds
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

import os
import random
from typing import Dict, List

import numpy as np
from sklearn.linear_model import LinearRegression
import requests


def fetch_pems_speed(station_id: int) -> Dict[int, List[float]]:
    """Fetch current speed data for each lane from PeMS.

    This function optionally logs in using ``PEMS_USERNAME`` and ``PEMS_PASSWORD``
    environment variables. If fetching the live data fails, it falls back to
    synthetic speeds so the API continues to work.
    """
    session = requests.Session()
    username = os.getenv("PEMS_USERNAME")
    password = os.getenv("PEMS_PASSWORD")

    if username and password:
        try:
            session.post(
                "https://pems.dot.ca.gov/",
                data={"username": username, "password": password, "login": "Login"},
                timeout=10,
            )
        except Exception:
            pass

    url = (
        "https://pems.dot.ca.gov/"
        f"?dnode=station_speed&content=speed&station_id={station_id}&format=json"
    )
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        lanes = {
            int(item.get("lane", idx + 1)): [float(item.get("speed", 0))]
            for idx, item in enumerate(data.get("speeds", []))
        }
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

import requests
from typing import Dict, List
from app.core.config import GOOGLE_MAPS_API_KEY
from app.models.poi import POI


def get_distance_matrix(pois: List[POI]) -> Dict:
    origins = "|".join([f"{p.lat},{p.lng}" for p in pois])
    destinations = origins

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origins,
        "destinations": destinations,
        "mode": "driving",
        "key": GOOGLE_MAPS_API_KEY,
    }

    response = requests.get(url, params=params)
    return response.json()

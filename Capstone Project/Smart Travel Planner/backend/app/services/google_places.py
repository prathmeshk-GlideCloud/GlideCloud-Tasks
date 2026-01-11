import requests
from typing import List
from app.core.config import GOOGLE_MAPS_API_KEY, PLACES_RADIUS_METERS, MIN_RATING
from app.models.poi import POI


def fetch_pois(city: str) -> List[POI]:
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"top attractions in {city}",
        "radius": PLACES_RADIUS_METERS,
        "key": GOOGLE_MAPS_API_KEY,
    }

    response = requests.get(url, params=params)
    data = response.json()

    pois = []
    for place in data.get("results", []):
        if "geometry" not in place:
            continue
        if place.get("rating", 0) < MIN_RATING:
            continue

        poi = POI(
            place_id=place["place_id"],
            name=place["name"],
            category=place["types"][0] if place.get("types") else "unknown",
            rating=place.get("rating"),
            lat=place["geometry"]["location"]["lat"],
            lng=place["geometry"]["location"]["lng"],
        )
        pois.append(poi)

    return pois

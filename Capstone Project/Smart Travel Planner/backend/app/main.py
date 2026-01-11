from fastapi import FastAPI
from app.services.google_places import fetch_pois
from app.services.distance_matrix import get_distance_matrix

app = FastAPI(title="Smart Travel Planner - Day 2")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/pois")
def get_pois(city: str):
    return fetch_pois(city)

@app.post("/distance-matrix")
def distance_matrix(city: str):
    pois = fetch_pois(city)
    return get_distance_matrix(pois)

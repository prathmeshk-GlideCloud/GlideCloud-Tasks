from app.services.google_places import fetch_pois
from app.services.distance_matrix import get_distance_matrix

def test_distance_matrix():
    pois = fetch_pois("Pune")[:3]
    matrix = get_distance_matrix(pois)
    assert "rows" in matrix

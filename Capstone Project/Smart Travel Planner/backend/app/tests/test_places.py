from app.services.google_places import fetch_pois

def test_fetch_pois():
    pois = fetch_pois("Pune")
    assert len(pois) > 0

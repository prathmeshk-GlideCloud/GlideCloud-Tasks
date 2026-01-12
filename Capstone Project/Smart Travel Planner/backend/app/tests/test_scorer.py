from app.planning.scorer import score_plan
from app.models.day_plan import DayPlan
from app.models.poi import POI

def test_score_positive():
    poi = POI(place_id="1", name="A", category="museum", rating=4.5, lat=0, lng=0)
    day = DayPlan(day=1, pois=[poi], total_distance=5, total_travel_time=30)

    score = score_plan([day], {"museum": 0.6})
    assert score > 0

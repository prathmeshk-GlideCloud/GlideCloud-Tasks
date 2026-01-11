from app.planning.constraints import apply_hard_constraints
from app.models.poi import POI

def test_budget_constraint():
    pois = [
        POI(place_id="1", name="A", category="c", rating=4.0, lat=0, lng=0)
        for _ in range(10)
    ]
    result = apply_hard_constraints(pois, budget=500, must_visit=[])
    assert result.is_feasible is False

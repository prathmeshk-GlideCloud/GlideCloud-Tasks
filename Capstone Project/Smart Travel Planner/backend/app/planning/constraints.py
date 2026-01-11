from typing import List
from app.models.poi import POI
from app.models.constraint_result import ConstraintResult

def apply_hard_constraints(
    pois: List[POI],
    budget: float,
    must_visit: List[str]
) -> ConstraintResult:
    
    reasons = []

    # Budget check
    estimated_cost = len(pois) * 200  # simple assumption
    if estimated_cost > budget:
        reasons.append("Estimated cost exceeds budget")

    # Must-visit check
    poi_names = {p.name for p in pois}
    for place in must_visit:
        if place not in poi_names:
            reasons.append(f"Must-visit place missing: {place}")

    return ConstraintResult(
        is_feasible=len(reasons) == 0,
        reasons=reasons
    )

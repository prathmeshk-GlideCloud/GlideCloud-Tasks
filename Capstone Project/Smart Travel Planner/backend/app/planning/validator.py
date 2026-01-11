from app.models.itinerary import Itinerary
from app.models.constraint_result import ConstraintResult

def validate_itinerary(itinerary: Itinerary) -> ConstraintResult:
    reasons = []

    if itinerary.total_cost <= 0:
        reasons.append("Invalid total cost")

    for plan in itinerary.plans:
        if len(plan.pois) == 0:
            reasons.append(f"Day {plan.day} has no POIs")

    return ConstraintResult(
        is_feasible=len(reasons) == 0,
        reasons=reasons
    )

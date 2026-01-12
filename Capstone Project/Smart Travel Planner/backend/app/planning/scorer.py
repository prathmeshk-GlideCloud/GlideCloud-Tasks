from typing import List, Dict
from app.models.day_plan import DayPlan

def score_plan(
    plans: List[DayPlan],
    interest_weights: Dict[str, float]
) -> float:
    """
    Returns a numeric score for an itinerary.
    Higher is better.
    """

    interest_score = 0.0
    distance_penalty = 0.0
    diversity_score = 0.0

    seen_categories = set()

    for day in plans:
        distance_penalty += day.total_distance

        for poi in day.pois:
            # Interest match
            interest_score += interest_weights.get(poi.category, 0.1)

            # Diversity
            if poi.category not in seen_categories:
                diversity_score += 1
                seen_categories.add(poi.category)

    # Normalize & combine
    final_score = (
        0.5 * interest_score
        - 0.3 * distance_penalty
        + 0.2 * diversity_score
    )

    return round(final_score, 2)

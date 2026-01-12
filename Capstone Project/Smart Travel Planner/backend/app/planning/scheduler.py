from typing import List
from app.models.poi import POI
from app.models.day_plan import DayPlan

def allocate_days(
    pois: List[POI],
    days: int,
    daily_limit: int = 8  # max POIs per day
) -> List[DayPlan]:

    plans = []
    chunk_size = max(1, len(pois) // days)

    for day in range(days):
        start = day * chunk_size
        end = start + chunk_size

        day_pois = pois[start:end]

        plans.append(
            DayPlan(
                day=day + 1,
                pois=day_pois,
                total_travel_time=60 * len(day_pois),
                total_distance=10 * len(day_pois)
            )
        )

    return plans

def generate_candidate_plans(
    pois: List,
    days: int,
    variants: int = 3
):
    plans = []

    for i in range(variants):
        rotated = pois[i:] + pois[:i]
        plans.append(allocate_days(rotated, days))

    return plans

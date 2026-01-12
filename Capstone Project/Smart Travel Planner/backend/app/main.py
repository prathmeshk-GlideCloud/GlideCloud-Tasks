from fastapi import FastAPI
from typing import List, Dict

from app.services.google_places import fetch_pois

from app.planning.constraints import apply_hard_constraints
from app.planning.scheduler import (
    allocate_days,
    generate_candidate_plans
)
from app.planning.validator import validate_itinerary
from app.planning.scorer import score_plan

from app.models.itinerary import Itinerary

# -------------------------------------------------
# FastAPI App
# -------------------------------------------------
app = FastAPI(title="Smart Travel Planner")

# -------------------------------------------------
# Health Check
# -------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------------------------------
# Generate Itinerary (Day 4)
# -------------------------------------------------
@app.post("/generate-itinerary")
def generate_itinerary(
    city: str,
    days: int,
    budget: float,
    must_visit: List[str] = [],
    interests: Dict[str, float] = {
        "museum": 0.6,
        "tourist_attraction": 0.4,
        "park": 0.3
    }
):
    """
    Day 4 responsibilities:
    1. Fetch POIs
    2. Enforce hard constraints (feasibility)
    3. Generate multiple candidate plans
    4. Score plans using soft constraints
    5. Select best plan deterministically
    """

    # -----------------------------
    # Step 1: Fetch POIs
    # -----------------------------
    pois = fetch_pois(city)

    if not pois:
        return {
            "is_feasible": False,
            "reasons": ["No POIs found for given city"]
        }

    # -----------------------------
    # Step 2: Hard Constraint Check
    # -----------------------------
    constraint_result = apply_hard_constraints(
        pois=pois,
        budget=budget,
        must_visit=must_visit
    )

    if not constraint_result.is_feasible:
        return constraint_result

    # -----------------------------
    # Step 3: Generate Candidate Plans
    # -----------------------------
    candidate_plans = generate_candidate_plans(
        pois=pois,
        days=days,
        variants=3
    )

    if not candidate_plans:
        return {
            "is_feasible": False,
            "reasons": ["No feasible plans could be generated"]
        }

    # -----------------------------
    # Step 4: Score & Rank Plans
    # -----------------------------
    scored_plans = []

    for plans in candidate_plans:
        score = score_plan(
            plans=plans,
            interest_weights=interests
        )
        scored_plans.append((score, plans))

    best_score, best_plans = max(scored_plans, key=lambda x: x[0])

    # -----------------------------
    # Step 5: Build Itinerary
    # -----------------------------
    itinerary = Itinerary(
        city=city,
        days=days,
        plans=best_plans,
        total_cost=len(pois) * 200
    )

    # -----------------------------
    # Step 6: Final Validation
    # -----------------------------
    validation_result = validate_itinerary(itinerary)

    if not validation_result.is_feasible:
        return validation_result

    # -----------------------------
    # Day 4 Response (NO EXPLANATION YET)
    # -----------------------------
    return {
        "is_feasible": True,
        "score": best_score,
        "days": days,
        "total_cost": itinerary.total_cost,
        "plan_summary": [
            {
                "day": plan.day,
                "num_pois": len(plan.pois),
                "total_distance": plan.total_distance,
                "total_travel_time": plan.total_travel_time
            }
            for plan in best_plans
        ]
    }

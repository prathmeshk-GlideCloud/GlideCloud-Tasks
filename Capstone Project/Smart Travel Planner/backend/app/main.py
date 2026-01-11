from fastapi import FastAPI
from typing import List

from app.services.google_places import fetch_pois
from app.planning.constraints import apply_hard_constraints
from app.planning.scheduler import allocate_days
from app.planning.validator import validate_itinerary
from app.models.itinerary import Itinerary

# ✅ DEFINE APP FIRST
app = FastAPI(title="Smart Travel Planner")

# -----------------------------
# Health Check
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -----------------------------
# Generate Itinerary (Day 3)
# -----------------------------
@app.post("/generate-itinerary")
def generate_itinerary(
    city: str,
    days: int,
    budget: float,
    must_visit: List[str] = []
):
    pois = fetch_pois(city)

    # Step 1: Hard constraints
    constraint_result = apply_hard_constraints(
        pois=pois,
        budget=budget,
        must_visit=must_visit
    )

    if not constraint_result.is_feasible:
        return constraint_result

    # Step 2: Schedule days
    day_plans = allocate_days(pois, days)

    itinerary = Itinerary(
        city=city,
        days=days,
        plans=day_plans,
        total_cost=len(pois) * 200
    )

    # Step 3: Final validation
    return validate_itinerary(itinerary)

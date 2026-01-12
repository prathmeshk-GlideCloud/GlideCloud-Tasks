from fastapi import FastAPI
from typing import List, Dict

from app.services.google_places import fetch_pois

from app.planning.constraints import apply_hard_constraints
from app.planning.scheduler import generate_candidate_plans
from app.planning.scorer import score_plan
from app.planning.validator import validate_itinerary

from app.models.itinerary import Itinerary
from app.models.constraint_result import ConstraintResult

from app.api.explain import router as explain_router


# -------------------------------------------------
# FastAPI App
# -------------------------------------------------
app = FastAPI(title="Smart Travel Planner")

# RAG explanation endpoint
app.include_router(explain_router)


# -------------------------------------------------
# Health Check
# -------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------------------------------
# Generate Itinerary (Day 6 – Final)
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
    Deterministic planning pipeline:
    1. Fetch POIs
    2. Enforce hard constraints
    3. Generate candidate plans
    4. Score with soft constraints
    5. Select best plan
    6. Validate
    """

    # -----------------------------
    # Step 1: Fetch POIs
    # -----------------------------
    pois = fetch_pois(city)

    if not pois:
        return {
            "is_feasible": False,
            "constraints": {
                "is_feasible": False,
                "reasons": ["No POIs found for given city"]
            }
        }

    # -----------------------------
    # Step 2: Hard Constraints
    # -----------------------------
    constraint_result: ConstraintResult = apply_hard_constraints(
        pois=pois,
        budget=budget,
        must_visit=must_visit
    )

    if not constraint_result.is_feasible:
        return {
            "is_feasible": False,
            "constraints": constraint_result.dict()
        }

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
            "constraints": {
                "is_feasible": False,
                "reasons": ["No feasible candidate plans generated"]
            }
        }

    # -----------------------------
    # Step 4: Score & Rank Plans
    # -----------------------------
    scored_plans = []

    for plan in candidate_plans:
        score = score_plan(
            plans=plan,
            interest_weights=interests
        )
        scored_plans.append((score, plan))

    best_score, best_plan = max(scored_plans, key=lambda x: x[0])

    # -----------------------------
    # Step 5: Build Itinerary
    # -----------------------------
    itinerary = Itinerary(
        city=city,
        days=days,
        plans=best_plan,
        total_cost=len(pois) * 200
    )

    # -----------------------------
    # Step 6: Final Validation
    # -----------------------------
    validation_result = validate_itinerary(itinerary)

    if not validation_result.is_feasible:
        return {
            "is_feasible": False,
            "constraints": validation_result.dict()
        }

    # -----------------------------
    # FINAL RESPONSE (USED BY STREAMLIT + RAG)
    # -----------------------------
    return {
        "is_feasible": True,
        "score": best_score,
        "itinerary": itinerary.dict(),
        "constraints": constraint_result.dict()
    }

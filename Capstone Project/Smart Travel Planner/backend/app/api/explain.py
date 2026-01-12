from fastapi import APIRouter
from app.rag.retriever import retrieve_context
from app.rag.explainer import generate_explanation

router = APIRouter()

@router.post("/explain-itinerary")
def explain_itinerary(payload: dict):
    itinerary = payload["itinerary"]
    constraints = payload["constraints"]

    pois = []
    for day in itinerary["plans"]:
        pois.extend(day["pois"])

    context = retrieve_context(pois)

    explanation = generate_explanation(
        itinerary_summary=str(itinerary),
        retrieved_context=context,
        constraints_summary=str(constraints)
    )

    return {"explanation": explanation}

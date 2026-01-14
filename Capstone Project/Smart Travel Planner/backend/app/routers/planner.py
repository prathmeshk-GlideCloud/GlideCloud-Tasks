"""
Travel Planner API Endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.models.user_input import ItineraryRequest
from app.models.itinerary import ItineraryResponse
from app.services.itinerary_builder import ItineraryBuilder

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize itinerary builder
itinerary_builder = ItineraryBuilder()


@router.post("/generate", response_model=Dict[str, Any])
async def generate_itinerary(request: ItineraryRequest):
    """
    Generate a complete travel itinerary
    
    This is the main endpoint that orchestrates:
    - Google Maps place search
    - RAG wisdom retrieval
    - Constraint-based scheduling
    - Multi-day itinerary generation
    """
    try:
        logger.info(f"Received itinerary request for {request.preferences.destination}")
        
        # Build itinerary
        result = itinerary_builder.build_itinerary(
            preferences=request.preferences,
            optimization_mode=request.optimize_for
        )
        
        # Check result status
        if result.get('status') == 'error':
            raise HTTPException(
                status_code=400,
                detail=result.get('message', 'Failed to generate itinerary')
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/example")
async def get_example_request():
    """
    Get an example request for testing
    """
    from datetime import date, timedelta
    
    return {
        "preferences": {
            "destination": "Paris, France",
            "start_date": str(date.today() + timedelta(days=7)),
            "end_date": str(date.today() + timedelta(days=10)),
            "budget_range": "medium",
            "interests": ["culture", "food"],
            "must_visit": ["Eiffel Tower"],
            "dietary_restrictions": [],
            "max_daily_distance": 50.0,
            "pace": "moderate"
        },
        "optimize_for": "time"
    }
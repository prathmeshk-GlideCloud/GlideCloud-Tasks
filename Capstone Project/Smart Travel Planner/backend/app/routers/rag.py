"""
Enhanced RAG API endpoints with intelligent tips
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from app.services.rag_service import IntelligentRAGService
from app.models.user_input import BudgetRange, PacePreference

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize intelligent RAG service
rag_service = IntelligentRAGService()


class IntelligentTipsRequest(BaseModel):
    """Request for intelligent, context-aware tips"""
    place_name: str = Field(..., description="Name of the place")
    category: str = Field(..., description="Category (museum, temple, park, etc.)")
    visit_time: str = Field(..., description="Visit time in HH:MM format")
    duration_hours: float = Field(..., description="Planned duration in hours")
    city: str = Field(default="Pune", description="City name")
    budget_range: str = Field(default="mid-range", description="Budget category")
    pace: str = Field(default="moderate", description="Travel pace")
    user_interests: Optional[List[str]] = Field(default=None, description="User interests")


class TipsResponse(BaseModel):
    """Response with intelligent tips"""
    place_name: str
    tips: List[str]
    tip_type: str
    confidence: str
    source: str


@router.post("/intelligent-tips", response_model=TipsResponse)
async def get_intelligent_tips(request: IntelligentTipsRequest):
    """
    Get intelligent, context-aware tips for a specific place
    
    This endpoint generates tips based on:
    - Place-specific knowledge (if available)
    - Time of visit
    - User preferences (budget, pace)
    - Category-specific best practices
    """
    try:
        tips_data = rag_service.get_intelligent_tips(
            place_name=request.place_name,
            category=request.category,
            visit_time=request.visit_time,
            duration_hours=request.duration_hours,
            city=request.city,
            budget_range=request.budget_range,
            pace=request.pace,
            user_interests=request.user_interests
        )
        
        return TipsResponse(**tips_data)
    
    except Exception as e:
        logger.error(f"Error getting intelligent tips: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-tips")
async def get_batch_tips(
    activities: List[Dict[str, Any]],
    city: str = "Pune",
    budget_range: str = "mid-range",
    pace: str = "moderate"
):
    """
    Get intelligent tips for multiple activities in batch
    
    Used by the itinerary generator to enrich all activities at once
    """
    try:
        enriched_activities = []
        
        for activity in activities:
            tips_data = rag_service.get_intelligent_tips(
                place_name=activity.get('activity_name', 'Unknown'),
                category=activity.get('category', 'attraction'),
                visit_time=activity.get('start_time', '09:00'),
                duration_hours=activity.get('duration_hours', 1.5),
                city=city,
                budget_range=budget_range,
                pace=pace
            )
            
            # Merge tips into activity
            activity_copy = activity.copy()
            activity_copy['insider_tips'] = tips_data['tips']
            activity_copy['tip_confidence'] = tips_data['confidence']
            enriched_activities.append(activity_copy)
        
        return {
            "activities": enriched_activities,
            "count": len(enriched_activities)
        }
    
    except Exception as e:
        logger.error(f"Error in batch tips: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-place-knowledge")
async def add_place_knowledge(place_data: Dict[str, Any]):
    """
    Add new place-specific knowledge to the system
    
    Example request body:
    {
        "name": "Sinhagad Fort",
        "best_time": "Early morning (6-9 AM) for sunrise",
        "duration_tip": "Allow 2-3 hours including trek",
        "tips": [
            "Can trek up (1.5 hours) or drive/take shared jeep",
            "Wear good trekking shoes",
            "Famous for kanda bhaji and mastani at top"
        ],
        "insider": [
            "Start trek at 6 AM to avoid heat",
            "Try the famous Sinhagad kanda bhaji"
        ],
        "avoid": "Midday heat in summer, weekends get very crowded",
        "nearby": "Within 30 km of Pune city"
    }
    """
    try:
        success = rag_service.add_place_knowledge(place_data)
        
        if success:
            return {
                "status": "success",
                "message": f"Added knowledge for {place_data.get('name', 'unknown place')}"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add place knowledge")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding place knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_rag_stats():
    """
    Get RAG knowledge base statistics
    """
    try:
        stats = rag_service.get_collection_stats()
        return stats
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Legacy endpoints for backward compatibility
@router.post("/tips/activity")
async def get_activity_tips(activity_type: str, n_results: int = 3):
    """Legacy endpoint - redirects to intelligent tips"""
    return {
        "message": "This endpoint is deprecated. Use /intelligent-tips for better results",
        "activity_type": activity_type
    }
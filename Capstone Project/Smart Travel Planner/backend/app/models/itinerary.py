"""
Models for itinerary output
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import time, date
from .place import Location


class RAGInsight(BaseModel):
    """RAG-generated insights for an activity"""
    
    tip: Optional[str] = None
    best_time: Optional[str] = None
    insider_tip: Optional[str] = None
    budget_tip: Optional[str] = None
    crowd_level: Optional[str] = None
    wait_time: Optional[str] = None


class Activity(BaseModel):
    """Single activity in itinerary"""
    
    sequence: int
    activity_name: str
    place_id: Optional[str] = None
    category: str
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    duration_hours: float
    location: Location
    address: Optional[str] = None
    cost: float
    rating: Optional[float] = None
    
    travel_from_previous: Dict[str, Any] = {
        "distance_km": 0,
        "duration_minutes": 0,
        "mode": "start"
    }
    
    rag_insights: Optional[RAGInsight] = None
    must_visit: bool = False
    dietary_match: Optional[List[str]] = []


class DaySchedule(BaseModel):
    """Schedule for a single day"""
    
    date: date
    activities: List[Activity]
    summary: Dict[str, Any]


class ConstraintValidation(BaseModel):
    """Constraint satisfaction details"""
    
    all_satisfied: bool
    details: Dict[str, Any]


class ItineraryResponse(BaseModel):
    """Complete itinerary response"""
    
    status: str  # "success" or "failed"
    message: Optional[str] = None
    
    itinerary: Optional[Dict[str, DaySchedule]] = None
    
    overall_summary: Optional[Dict[str, Any]] = None
    constraint_validation: Optional[ConstraintValidation] = None
    optimization_metrics: Optional[Dict[str, float]] = None
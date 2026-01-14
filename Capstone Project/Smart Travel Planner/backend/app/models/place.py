"""
Models for places and locations
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class Location(BaseModel):
    """Geographic location"""
    lat: float
    lng: float


class OpeningHours(BaseModel):
    """Opening hours information"""
    open_now: bool
    periods: Optional[List[Dict[str, Any]]] = None
    weekday_text: Optional[List[str]] = None


class Place(BaseModel):
    """Google Maps place"""
    
    place_id: str
    name: str
    formatted_address: Optional[str] = None
    location: Location
    rating: Optional[float] = 0.0
    user_ratings_total: Optional[int] = 0
    types: List[str] = []
    price_level: Optional[int] = 2  # 0-4 scale
    opening_hours: Optional[OpeningHours] = None
    photos: Optional[List[Dict[str, Any]]] = []
    website: Optional[str] = None


class TravelInfo(BaseModel):
    """Travel information between two points"""
    
    origin: Location
    destination: Location
    distance_meters: int
    distance_text: str
    duration_seconds: int
    duration_text: str
    mode: str = "driving"  # driving, walking, transit, bicycling
    
    @property
    def distance_km(self) -> float:
        """Distance in kilometers"""
        return self.distance_meters / 1000
    
    @property
    def duration_minutes(self) -> float:
        """Duration in minutes"""
        return self.duration_seconds / 60
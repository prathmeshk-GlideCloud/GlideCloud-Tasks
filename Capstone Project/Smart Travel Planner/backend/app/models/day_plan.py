from pydantic import BaseModel
from typing import List
from app.models.poi import POI

class DayPlan(BaseModel):
    day: int
    pois: List[POI]
    total_travel_time: int  # minutes
    total_distance: float   # km

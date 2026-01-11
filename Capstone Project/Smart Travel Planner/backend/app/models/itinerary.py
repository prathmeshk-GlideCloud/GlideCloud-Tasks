from pydantic import BaseModel
from typing import List
from app.models.day_plan import DayPlan

class Itinerary(BaseModel):
    city: str
    days: int
    plans: List[DayPlan]
    total_cost: float

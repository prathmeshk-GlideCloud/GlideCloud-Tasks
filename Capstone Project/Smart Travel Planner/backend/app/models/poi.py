from pydantic import BaseModel
from typing import Optional

class POI(BaseModel):
    place_id: str
    name: str
    category: str
    rating: Optional[float]
    lat: float
    lng: float

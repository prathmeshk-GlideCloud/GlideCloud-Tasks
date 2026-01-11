from pydantic import BaseModel
from typing import List

class ConstraintResult(BaseModel):
    is_feasible: bool
    reasons: List[str] = []

"""
Pydantic models for user input validation - PYDANTIC V2 FIXED
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from datetime import date
from enum import Enum


class InterestCategory(str, Enum):
    CULTURE = "culture"
    FOOD = "food"
    ADVENTURE = "adventure"
    NATURE = "nature"
    SHOPPING = "shopping"
    HISTORY = "history"
    NIGHTLIFE = "nightlife"
    RELAXATION = "relaxation"


class DietaryRestriction(str, Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    HALAL = "halal"
    KOSHER = "kosher"
    JAIN = "jain"
    NONE = "none"


class PacePreference(str, Enum):
    RELAXED = "relaxed"
    MODERATE = "moderate"
    PACKED = "packed"


class BudgetRange(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TravelPreferences(BaseModel):
    """User travel preferences with HYBRID budget support"""
    
    destination: str = Field(..., min_length=2)
    start_date: date = Field(...)
    end_date: date = Field(...)
    
    # HYBRID: Support both (make both optional, validate later)
    budget_range: Optional[BudgetRange] = Field(default=None)
    custom_budget: Optional[float] = Field(default=None)
    
    interests: List[InterestCategory] = Field(..., min_length=1)
    must_visit: Optional[List[str]] = Field(default_factory=list)
    dietary_restrictions: Optional[List[DietaryRestriction]] = Field(default_factory=list)
    max_daily_distance: float = Field(default=50.0, gt=0, le=200)
    pace: PacePreference = Field(default=PacePreference.MODERATE)
    accommodation_location: Optional[str] = Field(default=None)
    
    @field_validator('start_date')
    @classmethod
    def start_date_not_past(cls, v):
        """Validate start date is not in the past"""
        if v < date.today():
            raise ValueError('start_date cannot be in the past')
        return v
    
    @field_validator('end_date')
    @classmethod
    def end_date_after_start_date(cls, v, info):
        """Validate end date is after start date"""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
    
    @model_validator(mode='after')
    def validate_budget_fields(self):
        """Ensure either budget_range or custom_budget is provided"""
        if self.budget_range is None and self.custom_budget is None:
            raise ValueError('Either budget_range or custom_budget must be provided')
        
        # If custom_budget provided, validate it
        if self.custom_budget is not None:
            num_days = (self.end_date - self.start_date).days + 1
            per_day = self.custom_budget / num_days
            
            if per_day < 1000:
                raise ValueError(f'Budget too low: ₹{per_day:.0f}/day. Minimum ₹1000/day required')
            if per_day > 50000:
                raise ValueError(f'Budget unrealistic: ₹{per_day:.0f}/day. Maximum ₹50,000/day')
        
        return self
    
    @property
    def num_days(self) -> int:
        """Calculate number of days"""
        return (self.end_date - self.start_date).days + 1
    
    @property
    def total_budget(self) -> float:
        """Get total budget (custom takes precedence)"""
        from app.utils.budget_helper import BudgetHelper
        
        if self.custom_budget:
            return float(self.custom_budget)
        else:
            return BudgetHelper.get_total_budget(self.budget_range, self.num_days)
    
    @property
    def daily_budget(self) -> float:
        """Calculate daily budget"""
        return self.total_budget / self.num_days
    
    @property
    def effective_budget_range(self) -> BudgetRange:
        """Determine effective budget range (for custom budgets)"""
        if self.budget_range:
            return self.budget_range
        
        # Infer from custom budget
        per_day = self.daily_budget
        if per_day < 3500:
            return BudgetRange.LOW
        elif per_day < 8000:
            return BudgetRange.MEDIUM
        else:
            return BudgetRange.HIGH
    
    @property
    def budget_description(self) -> str:
        """Human-readable budget description"""
        if self.custom_budget:
            return f"Custom: ₹{self.total_budget:,.0f} (~₹{self.daily_budget:,.0f}/day)"
        else:
            descriptions = {
                BudgetRange.LOW: f"Budget: ~₹{self.daily_budget:.0f}/day",
                BudgetRange.MEDIUM: f"Comfortable: ~₹{self.daily_budget:.0f}/day",
                BudgetRange.HIGH: f"Premium: ~₹{self.daily_budget:.0f}/day"
            }
            return descriptions.get(self.budget_range, "Unknown")
    
    class Config:
        use_enum_values = False  # Keep enum objects, not just values


class OptimizationMode(str, Enum):
    """Optimization preferences"""
    TIME = "time"
    COST = "cost"
    BALANCED = "balanced"


class ItineraryRequest(BaseModel):
    """Complete itinerary generation request"""
    
    preferences: TravelPreferences
    optimize_for: OptimizationMode = Field(default=OptimizationMode.TIME)
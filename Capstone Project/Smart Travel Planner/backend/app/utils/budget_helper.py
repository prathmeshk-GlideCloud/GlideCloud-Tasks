"""
Budget calculation with SMART, REALISTIC pricing
"""
from app.models.user_input import BudgetRange
import random


class BudgetHelper:
    """Helper with realistic Indian pricing"""
    
    # Realistic price ranges for Indian attractions (in INR)
    INDIAN_PRICING = {
        # Museums & Historical Sites
        'museum': {
            BudgetRange.LOW: (50, 200),      # Government museums
            BudgetRange.MEDIUM: (150, 400),   # Mid-tier museums
            BudgetRange.HIGH: (300, 800)      # Premium/private
        },
        'art_gallery': {
            BudgetRange.LOW: (0, 150),
            BudgetRange.MEDIUM: (100, 300),
            BudgetRange.HIGH: (200, 600)
        },
        
        # Religious Sites
        'church': {
            BudgetRange.LOW: (0, 50),         # Usually free
            BudgetRange.MEDIUM: (0, 100),
            BudgetRange.HIGH: (0, 200)
        },
        'hindu_temple': {
            BudgetRange.LOW: (0, 50),
            BudgetRange.MEDIUM: (0, 100),
            BudgetRange.HIGH: (50, 300)
        },
        'place_of_worship': {
            BudgetRange.LOW: (0, 50),
            BudgetRange.MEDIUM: (0, 100),
            BudgetRange.HIGH: (50, 200)
        },
        
        # Forts & Monuments
        'tourist_attraction': {
            BudgetRange.LOW: (100, 300),
            BudgetRange.MEDIUM: (200, 600),
            BudgetRange.HIGH: (400, 1200)
        },
        
        # Parks & Gardens
        'park': {
            BudgetRange.LOW: (0, 50),         # Most parks free
            BudgetRange.MEDIUM: (20, 100),
            BudgetRange.HIGH: (50, 200)
        },
        
        # Shopping
        'shopping_mall': {
            BudgetRange.LOW: (200, 500),      # Window shopping budget
            BudgetRange.MEDIUM: (500, 1500),
            BudgetRange.HIGH: (1000, 3000)
        },
        
        # Food & Dining
        'restaurant': {
            BudgetRange.LOW: (150, 400),      # Local eateries
            BudgetRange.MEDIUM: (400, 1200),  # Good restaurants
            BudgetRange.HIGH: (1000, 3000)    # Fine dining
        },
        'cafe': {
            BudgetRange.LOW: (100, 250),
            BudgetRange.MEDIUM: (200, 500),
            BudgetRange.HIGH: (400, 800)
        },
        
        # Default fallback
        'default': {
            BudgetRange.LOW: (100, 300),
            BudgetRange.MEDIUM: (250, 600),
            BudgetRange.HIGH: (500, 1200)
        }
    }
    
    # Budget ranges - TOTAL TRIP
    BUDGET_RANGES = {
        BudgetRange.LOW: {
            'min': 10000,
            'max': 30000,
            'average': 20000,
            'per_day_avg': 2500,
            'breakdown': {
                'accommodation': 600,
                'food': 700,
                'activities': 900,
                'transport': 300
            }
        },
        BudgetRange.MEDIUM: {
            'min': 30000,
            'max': 60000,
            'average': 45000,
            'per_day_avg': 6000,
            'breakdown': {
                'accommodation': 2000,
                'food': 1500,
                'activities': 1800,
                'transport': 700
            }
        },
        BudgetRange.HIGH: {
            'min': 60000,
            'max': 150000,
            'average': 100000,
            'per_day_avg': 12000,
            'breakdown': {
                'accommodation': 4500,
                'food': 3000,
                'activities': 3200,
                'transport': 1300
            }
        }
    }
    
    @classmethod
    def estimate_activity_cost(
        cls, 
        price_level: int, 
        budget_range: BudgetRange,
        place_types: list = None,
        place_name: str = None
    ) -> float:
        """
        Smart cost estimation with realistic variance
        
        Args:
            price_level: Google Maps price level (0-4) or None
            budget_range: User's budget category
            place_types: List of place types from Google
            place_name: Name of the place (for special cases)
            
        Returns:
            Realistic cost in INR
        """
        
        # Determine category from place types
        category = cls._get_pricing_category(place_types)
        
        # Get price range for this category + budget
        price_range = cls.INDIAN_PRICING.get(category, cls.INDIAN_PRICING['default'])
        min_price, max_price = price_range.get(budget_range, (100, 500))
        
        # Add realistic variance (not always the same!)
        if price_level is not None:
            # Use Google's price level as a guide
            price_multipliers = {
                0: 0.0,   # Free
                1: 0.3,   # Cheap
                2: 0.6,   # Moderate
                3: 0.85,  # Expensive
                4: 1.0    # Very expensive
            }
            multiplier = price_multipliers.get(price_level, 0.6)
        else:
            # Random realistic variance
            multiplier = random.uniform(0.4, 0.9)
        
        # Calculate cost
        cost_range = max_price - min_price
        estimated_cost = min_price + (cost_range * multiplier)
        
        # Add small random variance (±10%) for realism
        variance = random.uniform(-0.1, 0.1)
        final_cost = estimated_cost * (1 + variance)
        
        # Round to nearest 10
        return round(final_cost / 10) * 10
    
    @classmethod
    def _get_pricing_category(cls, place_types: list) -> str:
        """Determine pricing category from place types"""
        if not place_types:
            return 'default'
        
        # Priority mapping
        type_mapping = {
            'museum': 'museum',
            'art_gallery': 'art_gallery',
            'church': 'church',
            'hindu_temple': 'hindu_temple',
            'place_of_worship': 'place_of_worship',
            'park': 'park',
            'shopping_mall': 'shopping_mall',
            'restaurant': 'restaurant',
            'cafe': 'cafe',
            'tourist_attraction': 'tourist_attraction',
            'point_of_interest': 'tourist_attraction'
        }
        
        for ptype in place_types:
            if ptype in type_mapping:
                return type_mapping[ptype]
        
        return 'default'
    
    @classmethod
    def get_daily_budget(cls, budget_range: BudgetRange) -> float:
        return cls.BUDGET_RANGES[budget_range]['per_day_avg']
    
    @classmethod
    def get_total_budget(cls, budget_range: BudgetRange, num_days: int) -> float:
        return cls.get_daily_budget(budget_range) * num_days
    
    @classmethod
    def get_activity_budget(cls, budget_range: BudgetRange, num_days: int) -> float:
        daily = cls.BUDGET_RANGES[budget_range]['breakdown']['activities']
        return daily * num_days
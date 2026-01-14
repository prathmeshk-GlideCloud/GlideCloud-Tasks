"""
Activity scoring system - FIXED for Hybrid Budget
Scores and ranks activities based on multiple factors
"""
from typing import List, Dict, Any, Union
import logging

from app.models.place import Place
from app.models.user_input import TravelPreferences, BudgetRange, InterestCategory
from app.utils.budget_helper import BudgetHelper

logger = logging.getLogger(__name__)


class ActivityScorer:
    """Scores activities based on preferences and constraints"""
    
    def __init__(self, preferences: Union[TravelPreferences, Dict[str, Any]]):
        """
        Initialize scorer with user preferences
        
        Args:
            preferences: Either TravelPreferences object or dict
        """
        # ✅ Handle both TravelPreferences object and dict
        if isinstance(preferences, TravelPreferences):
            # Using TravelPreferences object (RECOMMENDED)
            self.destination = preferences.destination
            self.interests = [i.value if hasattr(i, 'value') else i for i in preferences.interests]
            self.must_visit = [p.lower() for p in preferences.must_visit]
            self.budget_range = preferences.effective_budget_range  # ✅ Handles custom budget!
            self.num_days = preferences.num_days
            self.dietary_restrictions = preferences.dietary_restrictions
            self.pace = preferences.pace.value if hasattr(preferences.pace, 'value') else preferences.pace
        else:
            # Using dict (fallback for backward compatibility)
            self.destination = preferences.get('destination', '')
            self.interests = preferences.get('interests', [])
            self.must_visit = [p.lower() for p in preferences.get('must_visit', [])]
            
            # ✅ Handle budget properly
            self.budget_range = preferences.get('budget_range')
            custom_budget = preferences.get('custom_budget')
            
            if self.budget_range is None and custom_budget:
                # Infer budget range from custom budget
                num_days = preferences.get('num_days', 5)
                if num_days == 0:
                    num_days = 5
                
                per_day = custom_budget / num_days
                
                if per_day < 3500:
                    self.budget_range = BudgetRange.LOW
                elif per_day < 8000:
                    self.budget_range = BudgetRange.MEDIUM
                else:
                    self.budget_range = BudgetRange.HIGH
            
            # Fallback to medium if still None
            if self.budget_range is None:
                self.budget_range = BudgetRange.MEDIUM
            
            self.num_days = preferences.get('num_days', 5)
            self.dietary_restrictions = preferences.get('dietary_restrictions', [])
            self.pace = preferences.get('pace', 'moderate')
    
    def score_activity(self, place: Place, rag_insights: Dict = None) -> float:
        """
        Calculate comprehensive score for an activity
        
        Args:
            place: Place object from Google Maps
            rag_insights: Optional RAG insights about the place
            
        Returns:
            Score (higher is better)
        """
        score = 0.0
        
        # 1. Rating score (0-100 points)
        if place.rating:
            score += (place.rating / 5.0) * 100
        
        # 2. Interest match score (0-100 points)
        interest_score = self._calculate_interest_match(place)
        score += interest_score
        
        # 3. Budget compatibility (0-50 points)
        budget_score = self._calculate_budget_score(place)
        score += budget_score
        
        # 4. Popularity score (0-30 points)
        if place.user_ratings_total:
            import math
            popularity = min(30, math.log10(place.user_ratings_total + 1) * 10)
            score += popularity
        
        # 5. Must-visit bonus (200 points)
        if self._is_must_visit(place):
            score += 200
        
        # 6. RAG enhancement (0-20 points)
        if rag_insights:
            score += 20
        
        logger.debug(f"Scored {place.name}: {score:.1f} points")
        return score
    
    def _calculate_interest_match(self, place: Place) -> float:
        """Calculate how well place matches user interests"""
        if not self.interests:
            return 50.0
        
        # Map place types to interest categories
        type_interest_mapping = {
            'museum': ['culture', 'history'],
            'art_gallery': ['culture'],
            'restaurant': ['food'],
            'cafe': ['food'],
            'bar': ['nightlife', 'food'],
            'night_club': ['nightlife'],
            'park': ['nature', 'relaxation'],
            'amusement_park': ['adventure'],
            'shopping_mall': ['shopping'],
            'store': ['shopping'],
            'church': ['history', 'culture'],
            'hindu_temple': ['history', 'culture'],
            'place_of_worship': ['history', 'culture'],
            'tourist_attraction': ['culture'],
            'spa': ['relaxation'],
            'natural_feature': ['nature']
        }
        
        # Check matches
        matches = 0
        for place_type in place.types:
            if place_type in type_interest_mapping:
                type_interests = type_interest_mapping[place_type]
                for interest in self.interests:
                    if interest in type_interests:
                        matches += 1
        
        # Score based on matches
        if matches == 0:
            return 20.0
        elif matches == 1:
            return 60.0
        elif matches == 2:
            return 80.0
        else:
            return 100.0
    
    def _calculate_budget_score(self, place: Place) -> float:
        """Score based on budget compatibility"""
        if place.price_level is None:
            return 25.0
        
        # ✅ Use smart pricing with place types
        estimated_cost = BudgetHelper.estimate_activity_cost(
            place.price_level,
            self.budget_range,
            place.types,  # Pass types for better estimation
            place.name
        )
        
        # Check affordability
        daily_budget = BudgetHelper.get_daily_budget(self.budget_range)
        activity_budget = BudgetHelper.get_activity_budget(
            self.budget_range,
            self.num_days
        ) / self.num_days
        
        if estimated_cost == 0:
            return 50.0  # Free is always good
        elif estimated_cost <= activity_budget * 0.5:
            return 50.0  # Great value
        elif estimated_cost <= activity_budget:
            return 40.0  # Good value
        elif estimated_cost <= activity_budget * 1.5:
            return 25.0  # Acceptable
        else:
            return 10.0  # Expensive
    
    def _is_must_visit(self, place: Place) -> bool:
        """Check if place is a must-visit"""
        if not self.must_visit:
            return False
        
        place_name_lower = place.name.lower()
        
        for must_visit in self.must_visit:
            if must_visit in place_name_lower or place_name_lower in must_visit:
                return True
        
        return False
    
    def rank_activities(self, places: List[Place], rag_insights_map: Dict = None) -> List[tuple]:
        """
        Rank all activities by score
        
        Args:
            places: List of Place objects
            rag_insights_map: Optional dict mapping place_id to RAG insights
            
        Returns:
            List of (score, place) tuples, sorted by score descending
        """
        scored = []
        
        for place in places:
            insights = None
            if rag_insights_map and place.place_id in rag_insights_map:
                insights = rag_insights_map[place.place_id]
            
            score = self.score_activity(place, insights)
            scored.append((score, place))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        logger.info(f"Ranked {len(scored)} activities")
        return scored
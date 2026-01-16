"""
Itinerary Builder Service - Enhanced with Intelligent RAG
Orchestrates Google Maps, RAG, and Constraint Solver
"""
from typing import Dict, Any, List
import logging

from app.models.user_input import TravelPreferences, OptimizationMode
from app.models.place import Place
from app.services.google_maps import GoogleMapsService
from app.services.rag_service import IntelligentRAGService  # ← Changed import
from app.services.constraint_solver import ConstraintSolver
from app.core.scoring import ActivityScorer

logger = logging.getLogger(__name__)


class ItineraryBuilder:
    """Main service for building complete itineraries"""
    
    def __init__(self):
        self.gmaps = GoogleMapsService()
        self.rag = IntelligentRAGService()  # ← Now using intelligent RAG
        self.solver = ConstraintSolver(self.gmaps)
        self.place_enrichments = {}
    
    def build_itinerary(
        self,
        preferences: TravelPreferences,
        optimization_mode: OptimizationMode = OptimizationMode.TIME
    ) -> Dict[str, Any]:
        """
        Build complete itinerary from preferences
        
        Args:
            preferences: User travel preferences
            optimization_mode: How to optimize the itinerary
            
        Returns:
            Complete itinerary with all details
        """
        logger.info(f"Building itinerary for {preferences.destination}")

        if preferences.budget_range:
            budget_info = f"Budget Range: {preferences.budget_range.value}"
        else:
            budget_info = f"Custom Budget: ₹{preferences.custom_budget:,.0f}"
        
        logger.info(f"Duration: {preferences.num_days} days, {budget_info}")
        logger.info(f"Total Budget: ₹{preferences.total_budget:,.2f}")
        logger.info(f"Daily Budget: ₹{preferences.daily_budget:,.2f}")
        logger.info(f"Effective Category: {preferences.effective_budget_range.value}")

        self.place_enrichments = {}
        
        try:
            # Step 1: Gather places
            logger.info("Step 1: Gathering places from Google Maps...")
            places = self._gather_places(preferences)
            
            if not places:
                return {
                    'status': 'error',
                    'message': f'No places found for {preferences.destination}. Please check the destination name.',
                    'itinerary': None
                }
            
            logger.info(f"Found {len(places)} candidate places")
            
            # Step 2: Get general tips (optional - can be removed as tips are now context-aware)
            logger.info("Step 2: Getting general travel wisdom...")
            general_tips = self._get_general_tips(preferences)
            
            # Step 3: Score and rank
            logger.info("Step 3: Scoring and ranking activities...")
            scorer = ActivityScorer(preferences)
            scored_activities = scorer.rank_activities(places)
            
            logger.info(f"Top 5 scored activities:")
            for i, (score, place) in enumerate(scored_activities[:5], 1):
                logger.info(f"  {i}. {place.name} - Score: {score:.1f}")
            
            # Step 4: Run constraint solver (NOW INCLUDES INTELLIGENT RAG ENRICHMENT)
            logger.info("Step 4: Building itinerary with intelligent tips...")
            result = self.solver.solve(
                places=places,
                preferences=preferences,
                scored_activities=scored_activities
            )
            
            # ← REMOVED: No need for manual RAG enrichment - solver does it automatically
            # The constraint solver now enriches activities with intelligent tips internally
            
            # Step 5: Add overall tips
            result['travel_tips'] = general_tips
            result['destination'] = preferences.destination
            result['preferences_summary'] = self._create_preferences_summary(preferences)
            
            logger.info(f"✅ Itinerary built successfully with intelligent tips")
            return result
            
        except Exception as e:
            logger.error(f"Error building itinerary: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': f'An error occurred while building the itinerary: {str(e)}',
                'itinerary': None
            }
    
    def _gather_places(self, preferences: TravelPreferences) -> List[Place]:
        """Gather places from Google Maps based on interests"""
        all_places = []
        seen_place_ids = set()
        
        # Search for each interest
        for interest in preferences.interests:
            logger.info(f"Searching for {interest} activities...")
            
            places = self.gmaps.search_places_by_interest(
                interest=interest.value,
                location=preferences.destination,
                radius=10000  # 10km radius
            )
            
            # Limit per interest
            for place in places[:15]:
                if place.place_id not in seen_place_ids:
                    all_places.append(place)
                    seen_place_ids.add(place.place_id)
                    
                    if len(all_places) >= 60:
                        break
            
            if len(all_places) >= 60:
                break
        
        # Must-visit places
        for must_visit in preferences.must_visit:
            logger.info(f"Searching for must-visit: {must_visit}")
            
            places = self.gmaps.search_places(
                query=must_visit,
                location=preferences.destination,
                radius=20000
            )
            
            for place in places[:5]:
                if place.place_id not in seen_place_ids:
                    all_places.append(place)
                    seen_place_ids.add(place.place_id)
        
        logger.info(f"Gathered {len(all_places)} total places")
        return all_places[:80]
    
    def _get_general_tips(self, preferences: TravelPreferences) -> List[Dict]:
        """
        Get general travel tips (now optional - main tips come from intelligent RAG)
        These are high-level tips about budget, pace, etc.
        """
        tips = []
        
        # Budget guidance
        budget_category = self._get_budget_category(preferences.effective_budget_range)
        tips.append({
            'category': 'budget',
            'tip': f'Your {budget_category} budget allows for a comfortable trip with good experiences.'
        })
        
        # Pace guidance
        pace_tips = {
            'relaxed': 'Relaxed pace: 3 activities per day with plenty of time to enjoy each experience.',
            'moderate': 'Moderate pace: 4 activities per day with balanced exploration.',
            'packed': 'Packed pace: 5 activities per day for maximum coverage.'
        }
        tips.append({
            'category': 'pace',
            'tip': pace_tips.get(preferences.pace.value, 'Enjoy your trip at your own pace!')
        })
        
        # General travel tips
        tips.extend([
            {
                'category': 'general',
                'tip': 'Stay hydrated and take breaks between activities.'
            },
            {
                'category': 'safety',
                'tip': 'Keep important documents and valuables secure.'
            },
            {
                'category': 'cultural',
                'tip': 'Learn a few basic phrases in the local language.'
            }
        ])
        
        return tips[:5]
    
    def _get_budget_category(self, budget_range) -> str:
        """Get budget category name"""
        mapping = {
            'budget': 'budget-friendly',
            'medium': 'mid-range',
            'luxury': 'premium'
        }
        return mapping.get(budget_range.value, 'mid-range')
    
    def _create_preferences_summary(self, preferences: TravelPreferences) -> Dict:
        """Create human-readable summary of preferences"""
        return {
            'destination': preferences.destination,
            'dates': f"{preferences.start_date} to {preferences.end_date}",
            'duration': f"{preferences.num_days} days",
            'budget': preferences.budget_description,
            'total_budget': f"₹{preferences.total_budget:.2f}",
            'daily_budget': f"₹{preferences.daily_budget:.2f}",
            'interests': [i.value for i in preferences.interests],
            'must_visit': preferences.must_visit,
            'pace': preferences.pace.value,
            'max_daily_distance': f"{preferences.max_daily_distance} km"
        }
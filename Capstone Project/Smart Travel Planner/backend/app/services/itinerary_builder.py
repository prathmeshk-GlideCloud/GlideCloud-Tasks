"""
Itinerary Builder Service - FIXED for Hybrid Budget
Orchestrates Google Maps, RAG, and Constraint Solver
"""
from typing import Dict, Any, List
import logging

from app.models.user_input import TravelPreferences, OptimizationMode
from app.models.place import Place
from app.services.google_maps import GoogleMapsService
from app.services.rag_service import RAGService
from app.services.constraint_solver import ConstraintSolver
from app.core.scoring import ActivityScorer

logger = logging.getLogger(__name__)


class ItineraryBuilder:
    """Main service for building complete itineraries"""
    
    def __init__(self):
        self.gmaps = GoogleMapsService()
        self.rag = RAGService()
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
            
            # Step 2: Get RAG insights
            logger.info("Step 2: Getting travel wisdom from RAG...")
            general_tips = self._get_general_tips(preferences)
            
            # Step 3: Enrich activities
            logger.info("Step 3: Enriching activities with tips...")
            self._enrich_places_with_rag(places)
            
            # Step 4: Score and rank - PASS PREFERENCES OBJECT
            logger.info("Step 4: Scoring and ranking activities...")
            scorer = ActivityScorer(preferences)  # ✅ Pass object, not dict
            scored_activities = scorer.rank_activities(places)
            
            logger.info(f"Top 5 scored activities:")
            for i, (score, place) in enumerate(scored_activities[:5], 1):
                logger.info(f"  {i}. {place.name} - Score: {score:.1f}")
            
            # Step 5: Run constraint solver
            logger.info("Step 5: Running constraint solver...")
            result = self.solver.solve(
                places=places,
                preferences=preferences,
                scored_activities=scored_activities
            )
            
            # Step 6: Add RAG insights
            if result.get('itinerary'):
                result['itinerary'] = self._add_rag_insights_to_itinerary(
                    result['itinerary'],
                    general_tips
                )
            
            # Step 7: Add overall tips
            result['travel_tips'] = general_tips
            result['destination'] = preferences.destination
            result['preferences_summary'] = self._create_preferences_summary(preferences)
            
            logger.info(f"Itinerary built successfully: {result.get('status')}")
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
        """Get general travel tips from RAG"""
        tips = []
        
        try:
            # ✅ FIX: Use effective_budget_range (handles custom budget)
            budget_range = preferences.effective_budget_range
            budget_wisdom = self.rag.get_budget_wisdom(budget_range)
            if budget_wisdom and budget_wisdom.get('wisdom'):
                tips.append({
                    'category': 'budget',
                    'tip': budget_wisdom.get('wisdom', '')
                })
        except Exception as e:
            logger.warning(f"Could not get budget wisdom: {e}")
        
        try:
            pace_guidance = self.rag.get_pace_guidance(preferences.pace)
            if pace_guidance and pace_guidance.get('guidance'):
                tips.append({
                    'category': 'pacing',
                    'tip': pace_guidance.get('guidance', '')
                })
        except Exception as e:
            logger.warning(f"Could not get pace guidance: {e}")
        
        try:
            categories = ['timing', 'safety', 'cultural']
            general_tips = self.rag.get_general_tips(categories=categories, n_results=5)
            
            for tip_obj in general_tips:
                tips.append({
                    'category': tip_obj.get('metadata', {}).get('category', 'general'),
                    'tip': tip_obj.get('text', '')
                })
        except Exception as e:
            logger.warning(f"Could not get general tips: {e}")
        
        if not tips:
            tips = [
                {'category': 'general', 'tip': 'Plan ahead and book popular attractions in advance.'},
                {'category': 'general', 'tip': 'Stay hydrated and take breaks between activities.'},
                {'category': 'general', 'tip': 'Learn a few basic phrases in the local language.'}
            ]
        
        return tips[:8]
    
    def _enrich_places_with_rag(self, places: List[Place]) -> None:
        """Add RAG insights to places"""
        for place in places:
            try:
                activity_type = self._get_primary_type(place.types)
                enrichment = self.rag.enrich_activity_with_tips(
                    activity_name=place.name,
                    activity_type=activity_type,
                    category=activity_type
                )
                self.place_enrichments[place.place_id] = enrichment
            except Exception as e:
                logger.warning(f"Could not enrich {place.name}: {e}")
                self.place_enrichments[place.place_id] = {
                    'general_tip': None,
                    'timing_tip': None,
                    'best_practices': []
                }
    
    def _get_primary_type(self, types: List[str]) -> str:
        """Get primary type from list of types"""
        priority = [
            'museum', 'restaurant', 'park', 'church', 
            'tourist_attraction', 'shopping_mall', 'cafe'
        ]
        
        for ptype in priority:
            if ptype in types:
                return ptype
        
        return types[0] if types else 'point_of_interest'
    
    def _add_rag_insights_to_itinerary(
        self,
        itinerary: Dict,
        general_tips: List[Dict]
    ) -> Dict:
        """Add RAG insights to each activity in itinerary"""
        
        for day_key, day_data in itinerary.items():
            if not isinstance(day_data, dict) or 'activities' not in day_data:
                continue
            
            for activity in day_data['activities']:
                try:
                    category = activity.get('category', 'attraction')
                    place_id = activity.get('place_id')
                    
                    if place_id and place_id in self.place_enrichments:
                        enrichment = self.place_enrichments[place_id]
                        activity['rag_insights'] = {
                            'general_tip': enrichment.get('general_tip'),
                            'timing_tip': enrichment.get('timing_tip'),
                            'budget_tip': None
                        }
                    else:
                        activity_tips = self.rag.get_tips_for_activity_type(category, n_results=1)
                        
                        if activity_tips:
                            activity['rag_insights'] = {
                                'general_tip': activity_tips[0].get('text', ''),
                                'timing_tip': None,
                                'budget_tip': None
                            }
                        else:
                            activity['rag_insights'] = {
                                'general_tip': 'Enjoy your visit!',
                                'timing_tip': None,
                                'budget_tip': None
                            }
                except Exception as e:
                    logger.warning(f"Could not add RAG insights to activity: {e}")
                    activity['rag_insights'] = {
                        'general_tip': 'Enjoy your visit!',
                        'timing_tip': None,
                        'budget_tip': None
                    }
        
        return itinerary
    
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
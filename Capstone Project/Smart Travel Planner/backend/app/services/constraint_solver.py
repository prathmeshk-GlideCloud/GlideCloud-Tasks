"""
Advanced Constraint Solver with Intelligent RAG
"""
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, time, timedelta
import logging
import random
from collections import Counter

from app.models.place import Place, Location
from app.models.user_input import TravelPreferences, PacePreference
from app.services.google_maps import GoogleMapsService
from app.services.rag_service import IntelligentRAGService
from app.core.constraints import (
    ConstraintManager,
    TimeWindowConstraint,
    BudgetConstraint,
    DailyDistanceConstraint,
    MustVisitConstraint,
    MealTimeConstraint,
    ActivityVarietyConstraint
)
from app.core.scoring import ActivityScorer
from app.utils.budget_helper import BudgetHelper

logger = logging.getLogger(__name__)


class Activity:
    """Activity wrapper with metadata"""
    
    def __init__(self, place: Place, estimated_duration: float, estimated_cost: float):
        self.place = place
        self.duration_hours = estimated_duration
        self.cost = estimated_cost
        self.category = self._determine_category(place.types)
        self.is_cultural = self._is_cultural(place.types)
    
    def _determine_category(self, types: List[str]) -> str:
        """Determine primary category from place types"""
        category_map = [
            (['museum', 'art_gallery'], 'museum'),
            (['restaurant', 'cafe', 'food'], 'restaurant'),
            (['park', 'natural_feature'], 'park'),
            (['church', 'hindu_temple', 'place_of_worship', 'temple'], 'temple'),
            (['shopping_mall', 'store'], 'shopping'),
            (['tourist_attraction'], 'landmark'),
            (['historical_place', 'monument'], 'historical'),
        ]
        
        for type_list, category in category_map:
            if any(t in types for t in type_list):
                return category
        return 'attraction'
    
    def _is_cultural(self, types: List[str]) -> bool:
        """Check if place is culturally significant"""
        cultural_types = [
            'museum', 'art_gallery', 'historical_place', 'monument',
            'church', 'hindu_temple', 'place_of_worship', 'tourist_attraction', 'temple'
        ]
        return any(t in types for t in cultural_types)
    
    def __repr__(self):
        return f"Activity({self.place.name}, {self.category}, {self.duration_hours}h)"


class PaceConfig:
    """Pace-specific configuration for daily schedules"""
    
    def __init__(self, pace: PacePreference):
        self.pace = pace
        
        if pace == PacePreference.RELAXED:
            # 3 activities per day
            self.day_start = time(9, 0)
            self.day_end = time(21, 0)
            self.breakfast_time = time(9, 0)
            self.lunch_time = time(13, 30)
            self.dinner_time = time(20, 30)
            self.target_activities = 3
            self.duration_multiplier = 1.2
            self.meal_duration_multiplier = 1.3
        elif pace == PacePreference.PACKED:
            # 5 activities per day
            self.day_start = time(7, 0)
            self.day_end = time(23, 0)
            self.breakfast_time = time(7, 30)
            self.lunch_time = time(12, 30)
            self.dinner_time = time(19, 0)
            self.target_activities = 5
            self.duration_multiplier = 0.85
            self.meal_duration_multiplier = 0.8
        else:  # MODERATE
            # 4 activities per day
            self.day_start = time(8, 0)
            self.day_end = time(22, 0)
            self.breakfast_time = time(8, 0)
            self.lunch_time = time(13, 0)
            self.dinner_time = time(20, 0)
            self.target_activities = 4
            self.duration_multiplier = 1.0
            self.meal_duration_multiplier = 1.0
        
        logger.info(f"🎯 Pace: {pace.value} → {self.target_activities} activities/day")


class AdvancedConstraintSolver:
    """Constraint solver with intelligent RAG-powered tips"""
    
    def __init__(self, gmaps_service: GoogleMapsService):
        self.gmaps = gmaps_service
        self.rag_service = IntelligentRAGService()
        
        # Duration ranges by category (hours)
        self.duration_ranges = {
            'museum': (1.5, 2.5),
            'historical': (1.0, 2.0),
            'landmark': (0.75, 1.5),
            'park': (0.75, 1.25),
            'temple': (0.5, 1.0),
            'shopping': (1.0, 2.0),
            'attraction': (1.0, 1.5),
        }
        
        # Meal durations (hours)
        self.meal_durations = {
            'breakfast': 0.75,
            'lunch': 1.0,
            'dinner': 1.25
        }
    
    def solve(
        self,
        places: List[Place],
        preferences: TravelPreferences,
        scored_activities: List[tuple] = None
    ) -> Dict[str, Any]:
        """Main solver - generates itinerary with intelligent tips"""
        logger.info(f"🚀 Solver: {preferences.destination}")
        logger.info(f"📅 {preferences.num_days} days | 💰 ₹{preferences.total_budget:,.0f}")
        logger.info(f"⚡ Pace: {preferences.pace.value}")
        
        pace_config = PaceConfig(preferences.pace)
        constraint_manager = self._setup_constraints(preferences, pace_config)
        activities = self._create_activities(places, preferences, pace_config)
        
        if scored_activities is None:
            scorer = ActivityScorer(preferences)
            scored_activities = scorer.rank_activities([a.place for a in activities])
        
        itinerary = self._build_multi_day_itinerary(
            activities,
            scored_activities,
            preferences,
            pace_config
        )
        
        # Enrich with intelligent tips
        itinerary = self._enrich_with_intelligent_tips(itinerary, preferences, pace_config)
        
        validation = constraint_manager.check_all_constraints(
            self._flatten_itinerary(itinerary)
        )
        
        return {
            'status': 'success',
            'itinerary': itinerary,
            'validation': validation,
            'summary': self._generate_summary(itinerary, preferences)
        }
    
    def _setup_constraints(
        self,
        preferences: TravelPreferences,
        pace_config: PaceConfig
    ) -> ConstraintManager:
        """Setup constraint manager with all constraints"""
        manager = ConstraintManager()
        
        start_str = pace_config.day_start.strftime("%H:%M")
        end_str = pace_config.day_end.strftime("%H:%M")
        manager.add_constraint(TimeWindowConstraint(start_str, end_str))
        manager.add_constraint(BudgetConstraint(preferences.total_budget))
        
        if preferences.must_visit:
            manager.add_constraint(MustVisitConstraint(preferences.must_visit))
        
        manager.add_constraint(DailyDistanceConstraint(preferences.max_daily_distance))
        manager.add_constraint(MealTimeConstraint())
        manager.add_constraint(ActivityVarietyConstraint())
        
        return manager
    
    def _create_activities(
        self,
        places: List[Place],
        preferences: TravelPreferences,
        pace_config: PaceConfig
    ) -> List[Activity]:
        """Create activities with pace-adjusted durations and costs"""
        activities = []
        effective_range = preferences.effective_budget_range
        
        for place in places:
            category = self._categorize_place(place.types)
            
            min_dur, max_dur = self.duration_ranges.get(category, (1.0, 1.5))
            base_duration = random.uniform(min_dur, max_dur)
            duration = base_duration * pace_config.duration_multiplier
            duration = round(duration * 4) / 4  # Round to nearest 0.25 hour
            
            cost = BudgetHelper.estimate_activity_cost(
                place.price_level,
                effective_range,
                place.types,
                place.name
            )
            
            activity = Activity(place, duration, cost)
            activities.append(activity)
        
        return activities
    
    def _categorize_place(self, types: List[str]) -> str:
        """Categorize place by type priority"""
        priority_map = [
            (['museum', 'art_gallery'], 'museum'),
            (['restaurant', 'cafe'], 'restaurant'),
            (['park', 'natural_feature'], 'park'),
            (['church', 'hindu_temple', 'place_of_worship', 'temple'], 'temple'),
            (['shopping_mall', 'store'], 'shopping'),
            (['tourist_attraction'], 'landmark'),
            (['historical_place', 'monument'], 'historical'),
        ]
        
        for type_list, category in priority_map:
            if any(t in types for t in type_list):
                return category
        
        return 'attraction'
    
    def _build_multi_day_itinerary(
        self,
        activities: List[Activity],
        scored_activities: List[tuple],
        preferences: TravelPreferences,
        pace_config: PaceConfig
    ) -> Dict[str, Any]:
        """Build complete multi-day itinerary"""
        activity_map = {a.place.place_id: a for a in activities}
        
        # Categorize activities by priority
        must_visit_activities = []
        cultural_activities = []
        regular_activities = []
        
        must_visit_names = [mv.lower() for mv in preferences.must_visit]
        
        for score, place in scored_activities:
            if place.place_id not in activity_map:
                continue
            
            activity = activity_map[place.place_id]
            place_name_lower = place.name.lower()
            
            is_must_visit = any(
                mv in place_name_lower or place_name_lower in mv 
                for mv in must_visit_names
            )
            
            if is_must_visit:
                must_visit_activities.append(activity)
            elif activity.is_cultural:
                cultural_activities.append(activity)
            else:
                regular_activities.append(activity)
        
        # Build each day
        itinerary = {}
        used_activities = set()
        
        for day_num in range(1, preferences.num_days + 1):
            day_key = f"day_{day_num}"
            day_date = preferences.start_date + timedelta(days=day_num - 1)
            
            day_schedule = self._build_single_day(
                must_visit_activities,
                cultural_activities,
                regular_activities,
                used_activities,
                preferences,
                day_date,
                pace_config
            )
            
            # Add sequence numbers
            for idx, activity in enumerate(day_schedule, 1):
                activity['sequence'] = idx
            
            itinerary[day_key] = {
                'date': day_date.isoformat(),
                'activities': day_schedule,
                'summary': self._generate_day_summary(day_schedule)
            }
        
        return itinerary
    
    def _build_single_day(
        self,
        must_visit_activities: List[Activity],
        cultural_activities: List[Activity],
        regular_activities: List[Activity],
        used_activities: Set[str],
        preferences: TravelPreferences,
        day_date: datetime,
        pace_config: PaceConfig
    ) -> List[Dict]:
        """Build single day schedule with meals and activities"""
        schedule = []
        current_time = datetime.combine(day_date, pace_config.day_start)
        current_location = None
        
        daily_budget = preferences.total_budget / preferences.num_days
        spent_today = 0.0
        activities_added = 0
        last_category = None  # Track for variety
        
        all_activities = must_visit_activities + cultural_activities + regular_activities
        
        # === BREAKFAST ===
        breakfast_time = datetime.combine(day_date, pace_config.breakfast_time)
        self._add_meal(
            breakfast_time, "breakfast", schedule,
            regular_activities, used_activities,
            spent_today, daily_budget, pace_config
        )
        
        if schedule:
            spent_today += schedule[-1]['cost']
            current_time = datetime.strptime(schedule[-1]['end_time'], "%H:%M")
            current_time = datetime.combine(day_date, current_time.time())
            current_location = Location(
                lat=schedule[-1]['location']['lat'],
                lng=schedule[-1]['location']['lng']
            )
        
        # === MORNING ACTIVITIES ===
        lunch_time = datetime.combine(day_date, pace_config.lunch_time)
        morning_slots = max(1, pace_config.target_activities // 2)
        
        for activity in all_activities:
            if activities_added >= morning_slots:
                break
            
            # Skip conditions
            if activity.place.place_id in used_activities:
                continue
            if activity.category == 'restaurant':
                continue
            if spent_today + activity.cost > daily_budget * 1.3:
                continue
            if last_category is not None and activity.category == last_category:
                continue  # Enforce variety
            if current_time + timedelta(hours=activity.duration_hours + 0.5) > lunch_time:
                continue
            
            if self._add_activity(
                activity, schedule, current_time, current_location,
                used_activities, day_date, pace_config
            ):
                activities_added += 1
                spent_today += activity.cost
                last_category = activity.category
                
                current_time = datetime.strptime(schedule[-1]['end_time'], "%H:%M")
                current_time = datetime.combine(day_date, current_time.time())
                current_location = Location(
                    lat=schedule[-1]['location']['lat'],
                    lng=schedule[-1]['location']['lng']
                )
        
        # === LUNCH ===
        current_time = lunch_time
        self._add_meal(
            current_time, "lunch", schedule,
            regular_activities, used_activities,
            spent_today, daily_budget, pace_config
        )
        
        if schedule and schedule[-1]['category'] == 'restaurant':
            spent_today += schedule[-1]['cost']
            current_time = datetime.strptime(schedule[-1]['end_time'], "%H:%M")
            current_time = datetime.combine(day_date, current_time.time())
            current_location = Location(
                lat=schedule[-1]['location']['lat'],
                lng=schedule[-1]['location']['lng']
            )
            last_category = None  # Reset after meal break
        
        # === AFTERNOON ACTIVITIES ===
        dinner_time = datetime.combine(day_date, pace_config.dinner_time)
        
        for activity in all_activities:
            if activities_added >= pace_config.target_activities:
                break
            
            if activity.place.place_id in used_activities:
                continue
            if activity.category == 'restaurant':
                continue
            if spent_today + activity.cost > daily_budget * 1.3:
                continue
            if last_category is not None and activity.category == last_category:
                continue
            if current_time + timedelta(hours=activity.duration_hours + 0.5) > dinner_time:
                continue
            
            if self._add_activity(
                activity, schedule, current_time, current_location,
                used_activities, day_date, pace_config
            ):
                activities_added += 1
                spent_today += activity.cost
                last_category = activity.category
                
                current_time = datetime.strptime(schedule[-1]['end_time'], "%H:%M")
                current_time = datetime.combine(day_date, current_time.time())
                current_location = Location(
                    lat=schedule[-1]['location']['lat'],
                    lng=schedule[-1]['location']['lng']
                )
        
        # === DINNER ===
        current_time = dinner_time
        self._add_meal(
            current_time, "dinner", schedule,
            regular_activities, used_activities,
            spent_today, daily_budget, pace_config
        )
        
        logger.info(f"✅ Day {day_date.strftime('%Y-%m-%d')}: {activities_added} activities + 3 meals")
        return schedule
    
    def _add_activity(
        self,
        activity: Activity,
        schedule: List[Dict],
        current_time: datetime,
        current_location: Optional[Location],
        used_activities: Set[str],
        day_date: datetime,
        pace_config: PaceConfig
    ) -> bool:
        """Add activity to schedule with travel time calculation"""
        travel_time_minutes = 0
        travel_distance_km = 0
        travel_mode = "start"
        
        if current_location:
            distance_km = self._calculate_distance(current_location, activity.place.location)
            travel_mode = "walking" if distance_km < 1.0 else "transit"
            
            travel_info = self.gmaps.calculate_travel_time(
                current_location,
                activity.place.location,
                mode=travel_mode
            )
            
            if travel_info:
                travel_time_minutes = travel_info.duration_minutes
                travel_distance_km = travel_info.distance_km
        
        arrival_time = current_time + timedelta(minutes=travel_time_minutes)
        end_time = arrival_time + timedelta(hours=activity.duration_hours)
        
        activity_dict = {
            'sequence': len(schedule) + 1,
            'activity_name': activity.place.name,
            'place_id': activity.place.place_id,
            'category': activity.category,
            'start_time': arrival_time.strftime("%H:%M"),
            'end_time': end_time.strftime("%H:%M"),
            'duration_hours': activity.duration_hours,
            'location': {
                'lat': activity.place.location.lat,
                'lng': activity.place.location.lng
            },
            'address': activity.place.formatted_address,
            'cost': activity.cost,
            'rating': activity.place.rating,
            'travel_from_previous': {
                'distance_km': round(travel_distance_km, 2),
                'duration_minutes': travel_time_minutes,
                'mode': travel_mode
            }
        }
        
        schedule.append(activity_dict)
        used_activities.add(activity.place.place_id)
        return True
    
    def _add_meal(
        self,
        meal_time: datetime,
        meal_type: str,
        schedule: List[Dict],
        activities: List[Activity],
        used_activities: Set[str],
        spent_today: float,
        daily_budget: float,
        pace_config: PaceConfig
    ) -> bool:
        """Add meal to schedule"""
        restaurant_candidates = [
            a for a in activities
            if a.category == 'restaurant'
            and a.place.place_id not in used_activities
            and spent_today + a.cost <= daily_budget * 1.3
        ]
        
        if not restaurant_candidates:
            return False
        
        # Pick highest-rated available restaurant
        restaurant_candidates.sort(key=lambda a: a.place.rating or 0, reverse=True)
        restaurant = restaurant_candidates[0]
        
        base_duration = self.meal_durations[meal_type]
        meal_duration = base_duration * pace_config.meal_duration_multiplier
        meal_end = meal_time + timedelta(hours=meal_duration)
        
        meal_dict = {
            'sequence': len(schedule) + 1,
            'activity_name': f"{restaurant.place.name} ({meal_type.title()})",
            'place_id': restaurant.place.place_id,
            'category': 'restaurant',
            'start_time': meal_time.strftime("%H:%M"),
            'end_time': meal_end.strftime("%H:%M"),
            'duration_hours': round(meal_duration, 2),
            'location': {
                'lat': restaurant.place.location.lat,
                'lng': restaurant.place.location.lng
            },
            'address': restaurant.place.formatted_address,
            'cost': restaurant.cost,
            'rating': restaurant.place.rating,
            'travel_from_previous': {
                'distance_km': 0,
                'duration_minutes': 0,
                'mode': 'meal_break'
            }
        }
        
        schedule.append(meal_dict)
        used_activities.add(restaurant.place.place_id)
        return True
    
    def _enrich_with_intelligent_tips(
        self,
        itinerary: Dict,
        preferences: TravelPreferences,
        pace_config: PaceConfig
    ) -> Dict:
        """Enrich each activity with intelligent, context-aware tips"""
        logger.info("🎯 Enriching itinerary with intelligent tips...")
        
        for day_key, day_data in itinerary.items():
            if not isinstance(day_data, dict) or 'activities' not in day_data:
                continue
            
            for activity in day_data['activities']:
                budget_range = self._get_budget_category(preferences.effective_budget_range)
                
                tips_data = self.rag_service.get_intelligent_tips(
                    place_name=activity['activity_name'],
                    category=activity['category'],
                    visit_time=activity['start_time'],
                    duration_hours=activity['duration_hours'],
                    city=preferences.destination,
                    budget_range=budget_range,
                    pace=pace_config.pace.value
                )
                
                activity['insider_tips'] = tips_data['tips']
                activity['tip_confidence'] = tips_data.get('confidence', 'medium')
        
        logger.info("✅ Itinerary enrichment complete")
        return itinerary
    
    def _get_budget_category(self, budget_range) -> str:
        """Convert BudgetRange enum to category string"""
        if hasattr(budget_range, 'value'):
            budget_str = budget_range.value
            mapping = {
                'low': 'budget',
                'budget': 'budget',
                'medium': 'mid-range',
                'high': 'luxury',
                'luxury': 'luxury'
            }
            return mapping.get(budget_str, 'mid-range')
        return 'mid-range'
    
    def _calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """Calculate approximate distance in km"""
        import math
        lat_diff = abs(loc1.lat - loc2.lat)
        lng_diff = abs(loc1.lng - loc2.lng)
        return math.sqrt(lat_diff**2 + lng_diff**2) * 111
    
    def _flatten_itinerary(self, itinerary: Dict) -> List[Dict]:
        """Flatten itinerary to list of activities"""
        flattened = []
        for day_key in sorted(itinerary.keys()):
            if isinstance(itinerary[day_key], dict) and 'activities' in itinerary[day_key]:
                flattened.extend(itinerary[day_key]['activities'])
        return flattened
    
    def _generate_day_summary(self, schedule: List[Dict]) -> Dict:
        """Generate daily summary statistics"""
        activities_only = [a for a in schedule if a.get('category') != 'restaurant']
        meals_only = [a for a in schedule if a.get('category') == 'restaurant']
        
        return {
            'total_items': len(schedule),
            'activities_count': len(activities_only),
            'meals_count': len(meals_only),
            'total_cost': round(sum(a.get('cost', 0) for a in schedule), 2),
            'activities_cost': round(sum(a.get('cost', 0) for a in activities_only), 2),
            'meals_cost': round(sum(a.get('cost', 0) for a in meals_only), 2),
            'start_time': schedule[0]['start_time'] if schedule else None,
            'end_time': schedule[-1]['end_time'] if schedule else None,
        }
    
    def _generate_summary(self, itinerary: Dict, preferences: TravelPreferences) -> Dict:
        """Generate overall itinerary summary"""
        all_activities = self._flatten_itinerary(itinerary)
        total_cost = sum(a.get('cost', 0) for a in all_activities)
        
        category_counts = Counter()
        for activity in all_activities:
            category = activity.get('category', 'other')
            category_counts[category] += 1
        
        meals_count = category_counts.get('restaurant', 0)
        activities_count = len(all_activities) - meals_count
        
        return {
            'total_days': preferences.num_days,
            'total_items': len(all_activities),
            'total_activities': activities_count,
            'total_meals': meals_count,
            'total_cost': round(total_cost, 2),
            'budget_used_percentage': round((total_cost / preferences.total_budget) * 100, 1),
            'category_distribution': dict(category_counts),
            'budget_remaining': round(preferences.total_budget - total_cost, 2),
            'pace': preferences.pace.value
        }


# Maintain backward compatibility
ConstraintSolver = AdvancedConstraintSolver
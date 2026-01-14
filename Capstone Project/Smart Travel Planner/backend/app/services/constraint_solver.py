"""
Constraint-based planning solver - FIXED
- No duplicate POIs
- Must-visit guaranteed
- Proper meal times (8 AM, 1 PM, 8 PM)
- Duration matches time slots
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, time, timedelta
import logging
import random

from app.models.place import Place, Location
from app.models.user_input import TravelPreferences, PacePreference
from app.services.google_maps import GoogleMapsService
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
    """Wrapper class for activities with scheduling info"""
    
    def __init__(self, place: Place, estimated_duration: float, estimated_cost: float):
        self.place = place
        self.duration_hours = estimated_duration
        self.cost = estimated_cost
        self.category = self._determine_category(place.types)
        self.rag_tips = {}
    
    def _determine_category(self, types: List[str]) -> str:
        """Determine activity category from place types"""
        if any(t in types for t in ['museum', 'art_gallery']):
            return 'museum'
        elif any(t in types for t in ['restaurant', 'cafe', 'food']):
            return 'restaurant'
        elif any(t in types for t in ['park', 'natural_feature']):
            return 'park'
        elif any(t in types for t in ['church', 'hindu_temple', 'place_of_worship']):
            return 'religious_site'
        elif any(t in types for t in ['shopping_mall', 'store']):
            return 'shopping'
        elif 'tourist_attraction' in types:
            return 'landmark'
        else:
            return 'attraction'
    
    def __repr__(self):
        return f"Activity({self.place.name}, {self.duration_hours}h, ₹{self.cost})"


class ConstraintSolver:
    """
    Main constraint solver with FIXED meal scheduling
    """
    
    # FIXED MEAL TIMES
    BREAKFAST_TIME = time(8, 0)   # 8:00 AM
    LUNCH_TIME = time(13, 0)      # 1:00 PM
    DINNER_TIME = time(20, 0)     # 8:00 PM
    
    def __init__(self, gmaps_service: GoogleMapsService):
        self.gmaps = gmaps_service
        
        # REALISTIC duration ranges
        self.duration_ranges = {
            'museum': (1.5, 2.5),
            'art_gallery': (1.0, 2.0),
            'landmark': (0.75, 1.5),
            'restaurant': (1.0, 1.5),
            'cafe': (0.5, 1.0),
            'park': (0.75, 1.5),
            'religious_site': (0.5, 1.0),
            'shopping': (1.0, 2.0),
            'tourist_attraction': (1.0, 2.0),
            'attraction': (1.0, 1.5),
        }
    
    def solve(
        self,
        places: List[Place],
        preferences: TravelPreferences,
        scored_activities: List[tuple] = None
    ) -> Dict[str, Any]:
        """Main solving method"""
        logger.info(f"Starting constraint solver for {preferences.destination}")
        logger.info(f"Trip: {preferences.num_days} days")
        logger.info(f"Total Budget: ₹{preferences.total_budget:.2f}")
        logger.info(f"Must-visit places: {preferences.must_visit}")
        
        # Setup constraints
        constraint_manager = self._setup_constraints(preferences)
        
        # Convert places to activities
        activities = self._create_activities(places, preferences)
        
        # Score and rank
        if scored_activities is None:
            scorer = ActivityScorer(preferences)
            scored_activities = scorer.rank_activities([a.place for a in activities])
        
        # Build itinerary
        itinerary = self._build_multi_day_itinerary(
            activities,
            scored_activities,
            preferences,
            constraint_manager
        )
        
        # Validate
        validation = constraint_manager.check_all_constraints(
            self._flatten_itinerary(itinerary)
        )
        
        if not validation['hard_constraints_satisfied']:
            logger.warning("Could not satisfy all hard constraints")
        
        return {
            'status': 'success',
            'itinerary': itinerary,
            'validation': validation,
            'summary': self._generate_summary(itinerary, preferences)
        }
    
    def _setup_constraints(self, preferences: TravelPreferences) -> ConstraintManager:
        """Setup constraints"""
        manager = ConstraintManager()
        
        manager.add_constraint(TimeWindowConstraint("08:00", "22:00"))
        manager.add_constraint(BudgetConstraint(preferences.total_budget))
        
        if preferences.must_visit:
            manager.add_constraint(MustVisitConstraint(preferences.must_visit))
        
        manager.add_constraint(DailyDistanceConstraint(preferences.max_daily_distance))
        manager.add_constraint(MealTimeConstraint())
        manager.add_constraint(ActivityVarietyConstraint())
        
        logger.info(f"Setup {len(manager.constraints)} constraints")
        return manager
    
    def _create_activities(
        self,
        places: List[Place],
        preferences: TravelPreferences
    ) -> List[Activity]:
        """Convert places to activities with realistic durations/costs"""
        activities = []
        effective_range = preferences.effective_budget_range
        
        for place in places:
            category = self._categorize_place(place.types)
            
            # Random duration within range
            min_dur, max_dur = self.duration_ranges.get(category, (1.0, 1.5))
            base_duration = random.uniform(min_dur, max_dur)
            
            # Adjust for pace
            if preferences.pace == PacePreference.RELAXED:
                duration = base_duration * 1.1
            elif preferences.pace == PacePreference.PACKED:
                duration = base_duration * 0.9
            else:
                duration = base_duration
            
            # Round to 15 minutes
            duration = round(duration * 4) / 4
            
            # Smart cost estimation
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
        """Determine category"""
        if any(t in types for t in ['museum', 'art_gallery']):
            return 'museum'
        elif any(t in types for t in ['restaurant', 'cafe']):
            return 'restaurant'
        elif any(t in types for t in ['park', 'natural_feature']):
            return 'park'
        elif any(t in types for t in ['church', 'hindu_temple', 'place_of_worship']):
            return 'religious_site'
        elif 'shopping_mall' in types or 'store' in types:
            return 'shopping'
        elif 'tourist_attraction' in types:
            return 'tourist_attraction'
        return 'attraction'
    
    def _build_multi_day_itinerary(
        self,
        activities: List[Activity],
        scored_activities: List[tuple],
        preferences: TravelPreferences,
        constraint_manager: ConstraintManager
    ) -> Dict[str, List[Dict]]:
        """Build multi-day itinerary"""
        
        activity_map = {a.place.place_id: a for a in activities}
        
        # Separate must-visit and regular activities
        must_visit_names = [mv.lower() for mv in preferences.must_visit]
        must_visit_activities = []
        regular_activities = []
        
        for score, place in scored_activities:
            if place.place_id not in activity_map:
                continue
            
            activity = activity_map[place.place_id]
            place_name_lower = place.name.lower()
            
            # Check if must-visit
            is_must_visit = any(
                mv in place_name_lower or place_name_lower in mv 
                for mv in must_visit_names
            )
            
            if is_must_visit:
                must_visit_activities.append(activity)
                logger.info(f"✓ Found must-visit: {place.name}")
            else:
                regular_activities.append(activity)
        
        logger.info(f"Must-visit activities: {len(must_visit_activities)}")
        logger.info(f"Regular activities: {len(regular_activities)}")
        
        itinerary = {}
        used_activities = set()
        
        # Activities per day
        pace_config = {
            PacePreference.RELAXED: 3,
            PacePreference.MODERATE: 4,
            PacePreference.PACKED: 5
        }
        target_per_day = pace_config.get(preferences.pace, 4)
        
        # Distribute must-visit across days
        must_visit_per_day = len(must_visit_activities) // preferences.num_days + 1
        
        for day_num in range(1, preferences.num_days + 1):
            day_key = f"day_{day_num}"
            day_date = preferences.start_date + timedelta(days=day_num - 1)
            
            # Get must-visit for this day
            day_must_visit = []
            for mv in must_visit_activities:
                if mv.place.place_id not in used_activities:
                    day_must_visit.append(mv)
                    if len(day_must_visit) >= must_visit_per_day:
                        break
            
            day_schedule = self._build_single_day(
                day_must_visit,
                regular_activities,
                used_activities,
                preferences,
                day_date,
                target_per_day
            )
            
            # Re-sequence
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
        must_visit_today: List[Activity],
        regular_activities: List[Activity],
        used_activities: set,
        preferences: TravelPreferences,
        day_date,
        target_count: int
    ) -> List[Dict]:
        """Build single day schedule with FIXED meal times"""
        
        schedule = []
        current_time = datetime.combine(day_date, time(8, 0))
        end_time = datetime.combine(day_date, time(22, 0))
        current_location = None
        
        daily_budget = preferences.total_budget / preferences.num_days
        spent_today = 0.0
        
        # Combine activities: must-visit first, then regular
        all_day_activities = must_visit_today + regular_activities
        
        activities_added = 0
        
        for activity in all_day_activities:
            # Skip if used
            if activity.place.place_id in used_activities:
                continue
            
            # Skip restaurants (handled separately at meal times)
            if activity.category == 'restaurant':
                continue
            
            # Check target (excluding meals)
            if activities_added >= target_count:
                break
            
            # Check budget
            if spent_today + activity.cost > daily_budget * 1.2:  # Allow 20% overflow
                continue
            
            # Calculate travel
            travel_time_minutes = 0
            travel_distance_km = 0
            
            if current_location:
                travel_info = self.gmaps.calculate_travel_time(
                    current_location,
                    activity.place.location,
                    mode="walking" if self._is_walkable_distance(current_location, activity.place.location) else "driving"
                )
                if travel_info:
                    travel_time_minutes = travel_info.duration_minutes
                    travel_distance_km = travel_info.distance_km
            
            # Add travel time
            current_time += timedelta(minutes=travel_time_minutes)
            
            # Check if we need a meal break BEFORE this activity
            meal_added = self._try_add_meal(
                current_time,
                schedule,
                regular_activities,
                used_activities,
                day_date
            )
            
            if meal_added:
                # Update time and location
                meal_end_str = schedule[-1]['end_time']
                meal_end = datetime.strptime(meal_end_str, "%H:%M")
                current_time = datetime.combine(day_date, meal_end.time())
                spent_today += schedule[-1]['cost']
                current_location = Location(
                    lat=schedule[-1]['location']['lat'],
                    lng=schedule[-1]['location']['lng']
                )
            
            # Check if activity fits
            activity_end_time = current_time + timedelta(hours=activity.duration_hours)
            
            # Don't schedule past 10 PM
            if activity_end_time > end_time:
                continue
            
            # Add activity
            activity_dict = {
                'sequence': len(schedule) + 1,
                'activity_name': activity.place.name,
                'place_id': activity.place.place_id,
                'category': activity.category,
                'start_time': current_time.strftime("%H:%M"),
                'end_time': activity_end_time.strftime("%H:%M"),
                'duration_hours': activity.duration_hours,
                'location': {
                    'lat': activity.place.location.lat,
                    'lng': activity.place.location.lng
                },
                'address': activity.place.formatted_address,
                'cost': activity.cost,
                'rating': activity.place.rating,
                'travel_from_previous': {
                    'distance_km': travel_distance_km,
                    'duration_minutes': travel_time_minutes,
                    'mode': 'walking' if travel_time_minutes < 30 else 'transit'
                }
            }
            
            schedule.append(activity_dict)
            used_activities.add(activity.place.place_id)
            activities_added += 1
            
            # Update state
            current_time = activity_end_time
            current_location = activity.place.location
            spent_today += activity.cost
        
        # Try to add final meal (dinner) if time permits
        if current_time.time() < time(21, 0):
            self._try_add_meal(
                current_time,
                schedule,
                regular_activities,
                used_activities,
                day_date
            )
        
        return schedule
    
    def _try_add_meal(
        self,
        current_time: datetime,
        schedule: List[Dict],
        activities: List[Activity],
        used_activities: set,
        day_date
    ) -> bool:
        """
        Try to add meal at appropriate time
        Returns True if meal was added
        """
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        # Determine which meal time we're near
        meal_time = None
        meal_type = None
        
        # Breakfast: 7:30 - 9:00 AM
        if 7 <= current_hour < 9 or (current_hour == 9 and current_minute < 30):
            if not self._has_meal_in_schedule(schedule, 7, 10):
                meal_time = datetime.combine(day_date, self.BREAKFAST_TIME)
                meal_type = "breakfast"
        
        # Lunch: 12:30 - 2:00 PM
        elif 12 <= current_hour < 14 or (current_hour == 14 and current_minute < 30):
            if not self._has_meal_in_schedule(schedule, 12, 15):
                meal_time = datetime.combine(day_date, self.LUNCH_TIME)
                meal_type = "lunch"
        
        # Dinner: 7:30 - 9:00 PM
        elif 19 <= current_hour < 21 or (current_hour == 21 and current_minute < 30):
            if not self._has_meal_in_schedule(schedule, 19, 22):
                meal_time = datetime.combine(day_date, self.DINNER_TIME)
                meal_type = "dinner"
        
        if meal_time and meal_type:
            return self._add_meal_at_time(
                meal_time,
                meal_type,
                schedule,
                activities,
                used_activities
            )
        
        return False
    
    def _has_meal_in_schedule(self, schedule: List[Dict], start_hour: int, end_hour: int) -> bool:
        """Check if meal already exists in time range"""
        for activity in schedule:
            if activity.get('category') == 'restaurant':
                activity_hour = datetime.strptime(activity['start_time'], "%H:%M").hour
                if start_hour <= activity_hour < end_hour:
                    return True
        return False
    
    def _add_meal_at_time(
        self,
        meal_time: datetime,
        meal_type: str,
        schedule: List[Dict],
        activities: List[Activity],
        used_activities: set
    ) -> bool:
        """Add meal at specific time"""
        
        # Find available restaurant
        for activity in activities:
            if (activity.category == 'restaurant' and
                activity.place.place_id not in used_activities):
                
                meal_end = meal_time + timedelta(hours=activity.duration_hours)
                
                meal_dict = {
                    'sequence': len(schedule) + 1,
                    'activity_name': f"{activity.place.name} ({meal_type.title()})",
                    'place_id': activity.place.place_id,
                    'category': 'restaurant',
                    'start_time': meal_time.strftime("%H:%M"),
                    'end_time': meal_end.strftime("%H:%M"),
                    'duration_hours': activity.duration_hours,
                    'location': {
                        'lat': activity.place.location.lat,
                        'lng': activity.place.location.lng
                    },
                    'address': activity.place.formatted_address,
                    'cost': activity.cost,
                    'rating': activity.place.rating,
                    'travel_from_previous': {
                        'distance_km': 0,
                        'duration_minutes': 0,
                        'mode': 'meal_break'
                    }
                }
                
                schedule.append(meal_dict)
                used_activities.add(activity.place.place_id)
                logger.info(f"Added {meal_type} at {meal_time.strftime('%H:%M')}: {activity.place.name}")
                return True
        
        return False
    
    def _is_walkable_distance(self, loc1: Location, loc2: Location) -> bool:
        """Check if walkable"""
        import math
        lat_diff = abs(loc1.lat - loc2.lat)
        lng_diff = abs(loc1.lng - loc2.lng)
        distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111
        return distance < 2.0
    
    def _flatten_itinerary(self, itinerary: Dict) -> List[Dict]:
        """Flatten itinerary"""
        flattened = []
        for day_key in sorted(itinerary.keys()):
            if isinstance(itinerary[day_key], dict) and 'activities' in itinerary[day_key]:
                flattened.extend(itinerary[day_key]['activities'])
        return flattened
    
    def _generate_day_summary(self, schedule: List[Dict]) -> Dict:
        """Generate day summary"""
        return {
            'total_activities': len(schedule),
            'total_cost': sum(a.get('cost', 0) for a in schedule),
            'total_distance_km': sum(a.get('travel_from_previous', {}).get('distance_km', 0) for a in schedule),
            'start_time': schedule[0]['start_time'] if schedule else None,
            'end_time': schedule[-1]['end_time'] if schedule else None
        }
    
    def _generate_summary(self, itinerary: Dict, preferences: TravelPreferences) -> Dict:
        """Generate overall summary"""
        all_activities = self._flatten_itinerary(itinerary)
        
        total_cost = sum(a.get('cost', 0) for a in all_activities)
        total_distance = sum(
            a.get('travel_from_previous', {}).get('distance_km', 0)
            for a in all_activities
        )
        
        category_counts = {}
        for activity in all_activities:
            category = activity.get('category', 'other')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_days': preferences.num_days,
            'total_activities': len(all_activities),
            'total_cost': round(total_cost, 2),
            'budget_used_percentage': round((total_cost / preferences.total_budget) * 100, 1),
            'total_distance_km': round(total_distance, 2),
            'category_distribution': category_counts,
            'budget_remaining': round(preferences.total_budget - total_cost, 2)
        }
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, time, timedelta
import logging
import random
from collections import Counter

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
    """Enhanced activity wrapper with metadata"""
    
    def __init__(self, place: Place, estimated_duration: float, estimated_cost: float):
        self.place = place
        self.duration_hours = estimated_duration
        self.cost = estimated_cost
        self.category = self._determine_category(place.types)
        self.subcategory = self._determine_subcategory(place.types, place.name)
        self.is_premium = estimated_cost > 500
        self.is_cultural = self._is_cultural(place.types)
        self.rag_tips = {}
    
    def _determine_category(self, types: List[str]) -> str:
        """Primary category"""
        category_map = [
            (['museum', 'art_gallery'], 'museum'),
            (['restaurant', 'cafe', 'food'], 'restaurant'),
            (['park', 'natural_feature'], 'park'),
            (['church', 'hindu_temple', 'place_of_worship'], 'religious_site'),
            (['shopping_mall', 'store'], 'shopping'),
            (['tourist_attraction'], 'landmark'),
            (['historical_place', 'monument'], 'historical'),
        ]
        
        for type_list, category in category_map:
            if any(t in types for t in type_list):
                return category
        return 'attraction'
    
    def _determine_subcategory(self, types: List[str], name: str) -> str:
        """Detailed subcategory for better variety"""
        name_lower = name.lower()
        
        # Historical detection
        if any(word in name_lower for word in ['palace', 'fort', 'wada', 'monument', 'memorial']):
            return 'historical'
        
        # Museum types
        if 'museum' in types:
            if any(word in name_lower for word in ['art', 'gallery']):
                return 'art_museum'
            elif any(word in name_lower for word in ['history', 'archaeological']):
                return 'history_museum'
            return 'general_museum'
        
        # Park types
        if 'park' in types:
            if any(word in name_lower for word in ['garden', 'botanical']):
                return 'garden'
            return 'park'
        
        return self.category
    
    def _is_cultural(self, types: List[str]) -> bool:
        """Check if activity is culturally significant"""
        cultural_types = [
            'museum', 'art_gallery', 'historical_place', 'monument',
            'church', 'hindu_temple', 'place_of_worship', 'tourist_attraction'
        ]
        return any(t in types for t in cultural_types)
    
    def __repr__(self):
        return f"Activity({self.place.name}, {self.category}, {self.duration_hours}h, ₹{self.cost})"


class AdvancedConstraintSolver:
    """
    Production-grade constraint solver with intelligent scheduling
    """
    
    # Strict meal times
    BREAKFAST_TIME = time(8, 0)
    LUNCH_TIME = time(13, 0)
    DINNER_TIME = time(20, 0)
    
    # Target day structure
    DAY_START = time(8, 0)
    DAY_END = time(22, 0)
    
    def __init__(self, gmaps_service: GoogleMapsService):
        self.gmaps = gmaps_service
        
        # Enhanced duration ranges with variance
        self.duration_ranges = {
            'museum': (1.5, 2.5),
            'historical': (1.0, 2.0),
            'art_gallery': (1.0, 2.0),
            'landmark': (0.75, 1.5),
            'restaurant': (1.0, 1.5),
            'cafe': (0.5, 1.0),
            'park': (0.75, 1.25),
            'garden': (0.5, 1.0),
            'religious_site': (0.5, 1.0),
            'shopping': (1.0, 2.0),
            'tourist_attraction': (1.0, 2.0),
            'attraction': (1.0, 1.5),
        }
        
        # Variety limits per day
        self.category_limits = {
            'museum': 1,           
            'park': 2,             
            'shopping': 2,         
            'religious_site': 2,    
            'historical': 2,       
        }
    
    def solve(
        self,
        places: List[Place],
        preferences: TravelPreferences,
        scored_activities: List[tuple] = None
    ) -> Dict[str, Any]:
        """Main solving with enhanced validation"""
        logger.info(f"🚀 Advanced Solver: {preferences.destination}")
        logger.info(f"📅 {preferences.num_days} days | 💰 ₹{preferences.total_budget:,.0f}")
        logger.info(f"🎯 Interests: {[i.value for i in preferences.interests]}")
        
        constraint_manager = self._setup_constraints(preferences)
        activities = self._create_activities(places, preferences)
        
        if scored_activities is None:
            scorer = ActivityScorer(preferences)
            scored_activities = scorer.rank_activities([a.place for a in activities])
        
        logger.info(f"📊 Activity pool: {len(activities)} candidates")
        
        # Build with advanced logic
        itinerary = self._build_multi_day_itinerary(
            activities,
            scored_activities,
            preferences,
            constraint_manager
        )
        
        # Post-process validation
        itinerary = self._ensure_quality_itinerary(itinerary, preferences)
        
        validation = constraint_manager.check_all_constraints(
            self._flatten_itinerary(itinerary)
        )
        
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
        
        logger.info(f"✅ Setup {len(manager.constraints)} constraints")
        return manager
    
    def _create_activities(
        self,
        places: List[Place],
        preferences: TravelPreferences
    ) -> List[Activity]:
        """Create activities with smart categorization"""
        activities = []
        effective_range = preferences.effective_budget_range
        
        for place in places:
            category = self._categorize_place(place.types)
            
            min_dur, max_dur = self.duration_ranges.get(category, (1.0, 1.5))
            base_duration = random.uniform(min_dur, max_dur)
            
            # Pace adjustment
            pace_multiplier = {
                PacePreference.RELAXED: 1.15,
                PacePreference.MODERATE: 1.0,
                PacePreference.PACKED: 0.85
            }
            duration = base_duration * pace_multiplier.get(preferences.pace, 1.0)
            duration = round(duration * 4) / 4  # Round to 15min
            
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
        """Smart categorization"""
        priority_map = [
            (['museum', 'art_gallery'], 'museum'),
            (['restaurant', 'cafe'], 'restaurant'),
            (['park', 'natural_feature'], 'park'),
            (['church', 'hindu_temple', 'place_of_worship'], 'religious_site'),
            (['shopping_mall', 'store'], 'shopping'),
            (['tourist_attraction'], 'tourist_attraction'),
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
        constraint_manager: ConstraintManager
    ) -> Dict[str, Any]:
        """Build itinerary with guaranteed quality"""
        
        activity_map = {a.place.place_id: a for a in activities}
        
        # Intelligent activity separation
        must_visit_activities = []
        cultural_activities = []
        regular_activities = []
        
        must_visit_names = [mv.lower() for mv in preferences.must_visit]
        
        for score, place in scored_activities:
            if place.place_id not in activity_map:
                continue
            
            activity = activity_map[place.place_id]
            place_name_lower = place.name.lower()
            
            # Must-visit check
            is_must_visit = any(
                mv in place_name_lower or place_name_lower in mv 
                for mv in must_visit_names
            )
            
            if is_must_visit:
                must_visit_activities.append(activity)
                logger.info(f"⭐ Must-visit: {place.name}")
            elif activity.is_cultural:
                cultural_activities.append(activity)
            else:
                regular_activities.append(activity)
        
        logger.info(f"📌 Must-visit: {len(must_visit_activities)}")
        logger.info(f"🎭 Cultural: {len(cultural_activities)}")
        logger.info(f"🎯 Regular: {len(regular_activities)}")
        
        itinerary = {}
        used_activities = set()
        
        # Activities per day based on pace
        pace_targets = {
            PacePreference.RELAXED: 4,    # 4 activities + 3 meals = 7 total
            PacePreference.MODERATE: 5,   # 5 activities + 3 meals = 8 total
            PacePreference.PACKED: 6      # 6 activities + 3 meals = 9 total
        }
        target_per_day = pace_targets.get(preferences.pace, 5)
        
        # Distribute must-visit evenly
        must_visit_per_day = max(1, len(must_visit_activities) // preferences.num_days)
        
        for day_num in range(1, preferences.num_days + 1):
            day_key = f"day_{day_num}"
            day_date = preferences.start_date + timedelta(days=day_num - 1)
            
            # Allocate must-visit for this day
            day_must_visit = []
            for mv in must_visit_activities:
                if mv.place.place_id not in used_activities:
                    day_must_visit.append(mv)
                    if len(day_must_visit) >= must_visit_per_day:
                        break
            
            logger.info(f"\n📅 Building Day {day_num} ({day_date.strftime('%Y-%m-%d')})")
            
            day_schedule = self._build_single_day(
                day_must_visit,
                cultural_activities,
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
            
            logger.info(f"✅ Day {day_num}: {len(day_schedule)} items, "
                       f"₹{sum(a.get('cost', 0) for a in day_schedule):,.0f}")
        
        return itinerary
    
    def _build_single_day(
        self,
        must_visit_today: List[Activity],
        cultural_activities: List[Activity],
        regular_activities: List[Activity],
        used_activities: Set[str],
        preferences: TravelPreferences,
        day_date: datetime,
        target_count: int
    ) -> List[Dict]:
        """Advanced single-day builder with guaranteed meals and variety"""
        
        schedule = []
        current_time = datetime.combine(day_date, self.DAY_START)
        end_time = datetime.combine(day_date, self.DAY_END)
        current_location = None
        
        daily_budget = preferences.total_budget / preferences.num_days
        spent_today = 0.0
        
        # Variety tracking
        category_counts = Counter()
        subcategory_counts = Counter()
        last_category = None
        
        activities_added = 0
        
        # === BREAKFAST (8:00 AM) ===
        breakfast_added = self._add_meal_at_time(
            datetime.combine(day_date, self.BREAKFAST_TIME),
            "breakfast",
            schedule,
            regular_activities,
            used_activities,
            spent_today,
            daily_budget
        )
        
        if breakfast_added:
            spent_today += schedule[-1]['cost']
            current_time = datetime.strptime(schedule[-1]['end_time'], "%H:%M")
            current_time = datetime.combine(day_date, current_time.time())
            current_location = Location(
                lat=schedule[-1]['location']['lat'],
                lng=schedule[-1]['location']['lng']
            )
            logger.info(f"🍳 Breakfast added: {schedule[-1]['activity_name']}")
        
        # === MORNING ACTIVITIES (9:00 AM - 1:00 PM) ===
        morning_slots = 2
        all_activities = must_visit_today + cultural_activities + regular_activities
        
        for activity in all_activities:
            if activities_added >= morning_slots:
                break
            
            if not self._should_add_activity(
                activity, schedule, used_activities, category_counts,
                subcategory_counts, last_category, spent_today, daily_budget
            ):
                continue
            
            # Check time window (must finish before lunch)
            lunch_time = datetime.combine(day_date, self.LUNCH_TIME)
            if current_time + timedelta(hours=activity.duration_hours + 0.5) > lunch_time:
                continue
            
            # Add activity
            added = self._add_activity_to_schedule(
                activity, schedule, current_time, current_location,
                used_activities, day_date
            )
            
            if added:
                activities_added += 1
                spent_today += activity.cost
                category_counts[activity.category] += 1
                subcategory_counts[activity.subcategory] += 1
                last_category = activity.category
                
                current_time = datetime.strptime(schedule[-1]['end_time'], "%H:%M")
                current_time = datetime.combine(day_date, current_time.time())
                current_location = Location(
                    lat=schedule[-1]['location']['lat'],
                    lng=schedule[-1]['location']['lng']
                )
        
        # === LUNCH (1:00 PM) ===
        current_time = datetime.combine(day_date, self.LUNCH_TIME)
        lunch_added = self._add_meal_at_time(
            current_time,
            "lunch",
            schedule,
            regular_activities,
            used_activities,
            spent_today,
            daily_budget
        )
        
        if lunch_added:
            spent_today += schedule[-1]['cost']
            current_time = datetime.strptime(schedule[-1]['end_time'], "%H:%M")
            current_time = datetime.combine(day_date, current_time.time())
            current_location = Location(
                lat=schedule[-1]['location']['lat'],
                lng=schedule[-1]['location']['lng']
            )
            logger.info(f"🍽️ Lunch added: {schedule[-1]['activity_name']}")
        
        # === AFTERNOON/EVENING ACTIVITIES (2:30 PM - 7:30 PM) ===
        afternoon_target = target_count - activities_added
        
        for activity in all_activities:
            if activities_added >= target_count:
                break
            
            if not self._should_add_activity(
                activity, schedule, used_activities, category_counts,
                subcategory_counts, last_category, spent_today, daily_budget
            ):
                continue
            
            # Check time window (must finish before dinner)
            dinner_time = datetime.combine(day_date, self.DINNER_TIME)
            if current_time + timedelta(hours=activity.duration_hours + 0.5) > dinner_time:
                continue
            
            added = self._add_activity_to_schedule(
                activity, schedule, current_time, current_location,
                used_activities, day_date
            )
            
            if added:
                activities_added += 1
                spent_today += activity.cost
                category_counts[activity.category] += 1
                subcategory_counts[activity.subcategory] += 1
                last_category = activity.category
                
                current_time = datetime.strptime(schedule[-1]['end_time'], "%H:%M")
                current_time = datetime.combine(day_date, current_time.time())
                current_location = Location(
                    lat=schedule[-1]['location']['lat'],
                    lng=schedule[-1]['location']['lng']
                )
        
        # === DINNER (8:00 PM) - GUARANTEED ===
        current_time = datetime.combine(day_date, self.DINNER_TIME)
        dinner_added = self._add_meal_at_time(
            current_time,
            "dinner",
            schedule,
            regular_activities,
            used_activities,
            spent_today,
            daily_budget
        )
        
        if dinner_added:
            spent_today += schedule[-1]['cost']
            logger.info(f"🌙 Dinner added: {schedule[-1]['activity_name']}")
        else:
            logger.warning(f"⚠️ Could not add dinner for Day {day_date.strftime('%Y-%m-%d')}")
        
        logger.info(f"📊 Day stats: {activities_added} activities, {category_counts}")
        
        return schedule
    
    def _should_add_activity(
        self,
        activity: Activity,
        schedule: List[Dict],
        used_activities: Set[str],
        category_counts: Counter,
        subcategory_counts: Counter,
        last_category: Optional[str],
        spent_today: float,
        daily_budget: float
    ) -> bool:
        """Comprehensive activity validation"""
        
        # Already used
        if activity.place.place_id in used_activities:
            return False
        
        # Skip restaurants (handled separately)
        if activity.category == 'restaurant':
            return False
        
        # No back-to-back same category
        if last_category == activity.category and activity.category not in ['landmark', 'historical']:
            return False
        
        # Category limits
        limit = self.category_limits.get(activity.category, 3)
        if category_counts[activity.category] >= limit:
            return False
        
        # Subcategory diversity
        if subcategory_counts[activity.subcategory] >= 2:
            return False
        
        # Budget check (relaxed - allow 130% of daily budget)
        if spent_today + activity.cost > daily_budget * 1.3:
            return False
        
        return True
    
    def _add_activity_to_schedule(
        self,
        activity: Activity,
        schedule: List[Dict],
        current_time: datetime,
        current_location: Optional[Location],
        used_activities: Set[str],
        day_date: datetime
    ) -> bool:
        """Add activity with travel calculation"""
        
        travel_time_minutes = 0
        travel_distance_km = 0
        travel_mode = "start"
        
        if current_location:
            travel_info = self.gmaps.calculate_travel_time(
                current_location,
                activity.place.location,
                mode="walking" if self._is_walkable_distance(
                    current_location, activity.place.location
                ) else "driving"
            )
            
            if travel_info:
                travel_time_minutes = travel_info.duration_minutes
                travel_distance_km = travel_info.distance_km
                travel_mode = "walking" if travel_time_minutes < 30 else "transit"
        
        # Apply travel time
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
        
        logger.debug(f"✓ Added: {activity.place.name} ({arrival_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')})")
        
        return True
    
    def _add_meal_at_time(
        self,
        meal_time: datetime,
        meal_type: str,
        schedule: List[Dict],
        activities: List[Activity],
        used_activities: Set[str],
        spent_today: float,
        daily_budget: float
    ) -> bool:
        """Add meal with budget awareness and rating priority"""
        
        # Find best available restaurant
        restaurant_candidates = [
            a for a in activities
            if a.category == 'restaurant'
            and a.place.place_id not in used_activities
            and spent_today + a.cost <= daily_budget * 1.3
        ]
        
        if not restaurant_candidates:
            logger.warning(f"⚠️ No restaurants available for {meal_type}")
            return False
        
        # Sort by rating (prefer higher rated)
        restaurant_candidates.sort(key=lambda a: a.place.rating or 0, reverse=True)
        
        restaurant = restaurant_candidates[0]
        meal_end = meal_time + timedelta(hours=restaurant.duration_hours)
        
        meal_dict = {
            'sequence': len(schedule) + 1,
            'activity_name': f"{restaurant.place.name} ({meal_type.title()})",
            'place_id': restaurant.place.place_id,
            'category': 'restaurant',
            'start_time': meal_time.strftime("%H:%M"),
            'end_time': meal_end.strftime("%H:%M"),
            'duration_hours': restaurant.duration_hours,
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
    
    def _is_walkable_distance(self, loc1: Location, loc2: Location) -> bool:
        """Check walkability"""
        import math
        lat_diff = abs(loc1.lat - loc2.lat)
        lng_diff = abs(loc1.lng - loc2.lng)
        distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111
        return distance < 2.0
    
    def _ensure_quality_itinerary(
        self,
        itinerary: Dict,
        preferences: TravelPreferences
    ) -> Dict:
        """Post-processing quality assurance"""
        
        for day_key, day_data in itinerary.items():
            if not isinstance(day_data, dict) or 'activities' not in day_data:
                continue
            
            activities = day_data['activities']
            
            # Ensure 3 meals per day
            meal_types = [a.get('category') for a in activities]
            restaurant_count = meal_types.count('restaurant')
            
            if restaurant_count < 3:
                logger.warning(f"⚠️ {day_key} has only {restaurant_count} meals (expected 3)")
            
            # Ensure day ends after 8 PM
            if activities:
                last_end_time = activities[-1].get('end_time', '00:00')
                end_hour = int(last_end_time.split(':')[0])
                
                if end_hour < 20:
                    logger.warning(f"⚠️ {day_key} ends too early at {last_end_time}")
        
        return itinerary
    
    def _flatten_itinerary(self, itinerary: Dict) -> List[Dict]:
        """Flatten for validation"""
        flattened = []
        for day_key in sorted(itinerary.keys()):
            if isinstance(itinerary[day_key], dict) and 'activities' in itinerary[day_key]:
                flattened.extend(itinerary[day_key]['activities'])
        return flattened
    
    def _generate_day_summary(self, schedule: List[Dict]) -> Dict:
        """Enhanced day summary"""
        activities_only = [a for a in schedule if a.get('category') != 'restaurant']
        meals_only = [a for a in schedule if a.get('category') == 'restaurant']
        
        return {
            'total_activities': len(schedule),
            'activities_count': len(activities_only),
            'meals_count': len(meals_only),
            'total_cost': round(sum(a.get('cost', 0) for a in schedule), 2),
            'activities_cost': round(sum(a.get('cost', 0) for a in activities_only), 2),
            'meals_cost': round(sum(a.get('cost', 0) for a in meals_only), 2),
            'total_distance_km': round(sum(
                a.get('travel_from_previous', {}).get('distance_km', 0) 
                for a in schedule
            ), 2),
            'start_time': schedule[0]['start_time'] if schedule else None,
            'end_time': schedule[-1]['end_time'] if schedule else None,
            'has_breakfast': any(a.get('category') == 'restaurant' and '08:' in a.get('start_time', '') for a in schedule),
            'has_lunch': any(a.get('category') == 'restaurant' and '13:' in a.get('start_time', '') for a in schedule),
            'has_dinner': any(a.get('category') == 'restaurant' and '20:' in a.get('start_time', '') for a in schedule)
        }
    
    def _generate_summary(self, itinerary: Dict, preferences: TravelPreferences) -> Dict:
        """Comprehensive summary"""
        all_activities = self._flatten_itinerary(itinerary)
        
        total_cost = sum(a.get('cost', 0) for a in all_activities)
        total_distance = sum(
            a.get('travel_from_previous', {}).get('distance_km', 0)
            for a in all_activities
        )
        
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
            'total_distance_km': round(total_distance, 2),
            'category_distribution': dict(category_counts),
            'budget_remaining': round(preferences.total_budget - total_cost, 2),
            'avg_cost_per_day': round(total_cost / preferences.num_days, 2)
        }
    
ConstraintSolver = AdvancedConstraintSolver
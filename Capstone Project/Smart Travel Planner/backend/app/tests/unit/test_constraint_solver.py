# tests/unit/test_constraint_solver.py
import pytest
from datetime import date, time
from app.services.constraint_solver import ConstraintSolver
from app.models.user_input import TravelPreferences, BudgetRange, PacePreference
from app.models.place import Place, Location

@pytest.fixture
def sample_preferences():
    """Sample travel preferences for testing"""
    return TravelPreferences(
        destination="Pune, India",
        start_date=date(2026, 1, 21),
        end_date=date(2026, 1, 23),  # 3 days
        budget_range=BudgetRange.MEDIUM,
        custom_budget=None,
        interests=["culture", "history"],
        must_visit=["Shaniwar Wada"],
        pace=PacePreference.MODERATE
    )

@pytest.fixture
def sample_places():
    """Sample places for testing"""
    return [
        Place(
            place_id="place1",
            name="Shaniwar Wada",
            formatted_address="Bajirao Road, Pune",
            location=Location(lat=18.5196, lng=73.8553),
            types=["tourist_attraction", "museum"],
            rating=4.4,
            user_ratings_total=15000,
            price_level=1
        ),
        Place(
            place_id="place2",
            name="Vohuman Cafe",
            formatted_address="FC Road, Pune",
            location=Location(lat=18.5204, lng=73.8567),
            types=["restaurant", "cafe"],
            rating=4.6,
            user_ratings_total=8000,
            price_level=1
        ),
        Place(
            place_id="place3",
            name="Aga Khan Palace",
            formatted_address="Nagar Road, Pune",
            location=Location(lat=18.5515, lng=73.9029),
            types=["tourist_attraction", "museum"],
            rating=4.5,
            user_ratings_total=12000,
            price_level=1
        )
    ]

class TestConstraintSolver:
    """Test constraint solver functionality"""
    
    def test_solver_initialization(self):
        """Test solver can be initialized"""
        from app.services.google_maps import GoogleMapsService
        gmaps = GoogleMapsService()
        solver = ConstraintSolver(gmaps)
        assert solver is not None
        assert solver.gmaps is not None
    
    def test_meal_time_constants(self):
        """Test meal times are correct"""
        from app.services.constraint_solver import ConstraintSolver
        from app.services.google_maps import GoogleMapsService
        
        solver = ConstraintSolver(GoogleMapsService())
        assert solver.BREAKFAST_TIME == time(8, 0)
        assert solver.LUNCH_TIME == time(13, 0)
        assert solver.DINNER_TIME == time(20, 0)
    
    def test_activity_creation(self, sample_preferences, sample_places):
        """Test activities are created with correct durations and costs"""
        from app.services.google_maps import GoogleMapsService
        
        solver = ConstraintSolver(GoogleMapsService())
        activities = solver._create_activities(sample_places, sample_preferences)
        
        assert len(activities) == 3
        
        # Check durations are in valid ranges
        for activity in activities:
            assert 0.5 <= activity.duration_hours <= 3.0
            assert activity.cost >= 0
            assert activity.category in ['museum', 'restaurant', 'park', 
                                        'religious_site', 'shopping', 
                                        'landmark', 'attraction']
    
    def test_categorize_place(self, sample_places):
        """Test place categorization logic"""
        from app.services.google_maps import GoogleMapsService
        
        solver = ConstraintSolver(GoogleMapsService())
        
        # Museum
        category1 = solver._categorize_place(["museum", "tourist_attraction"])
        assert category1 == "museum"
        
        # Restaurant
        category2 = solver._categorize_place(["restaurant", "food"])
        assert category2 == "restaurant"
        
        # Religious site
        category3 = solver._categorize_place(["church", "place_of_worship"])
        assert category3 == "religious_site"
    
    def test_must_visit_included(self, sample_preferences, sample_places):
        """Test must-visit places are included in itinerary"""
        from app.services.google_maps import GoogleMapsService
        from app.core.scoring import ActivityScorer
        
        solver = ConstraintSolver(GoogleMapsService())
        scorer = ActivityScorer(sample_preferences)
        scored_activities = scorer.rank_activities(sample_places)
        
        result = solver.solve(
            places=sample_places,
            preferences=sample_preferences,
            scored_activities=scored_activities
        )
        
        assert result['status'] == 'success'
        
        # Check Shaniwar Wada is in itinerary
        itinerary = result['itinerary']
        all_activities = []
        for day_key, day_data in itinerary.items():
            all_activities.extend(day_data['activities'])
        
        activity_names = [a['activity_name'] for a in all_activities]
        assert any('Shaniwar Wada' in name for name in activity_names), \
               "Must-visit place not found in itinerary"
    
    def test_no_duplicate_activities(self, sample_preferences, sample_places):
        """Test no place is scheduled twice"""
        from app.services.google_maps import GoogleMapsService
        from app.core.scoring import ActivityScorer
        
        solver = ConstraintSolver(GoogleMapsService())
        scorer = ActivityScorer(sample_preferences)
        scored_activities = scorer.rank_activities(sample_places)
        
        result = solver.solve(
            places=sample_places,
            preferences=sample_preferences,
            scored_activities=scored_activities
        )
        
        # Get all place IDs
        all_place_ids = []
        for day_key, day_data in result['itinerary'].items():
            for activity in day_data['activities']:
                all_place_ids.append(activity['place_id'])
        
        # Check no duplicates
        assert len(all_place_ids) == len(set(all_place_ids)), \
               "Found duplicate activities in itinerary"
    
    def test_budget_not_exceeded(self, sample_preferences, sample_places):
        """Test total cost doesn't exceed budget"""
        from app.services.google_maps import GoogleMapsService
        from app.core.scoring import ActivityScorer
        
        solver = ConstraintSolver(GoogleMapsService())
        scorer = ActivityScorer(sample_preferences)
        scored_activities = scorer.rank_activities(sample_places)
        
        result = solver.solve(
            places=sample_places,
            preferences=sample_preferences,
            scored_activities=scored_activities
        )
        
        total_cost = result['summary']['total_cost']
        total_budget = sample_preferences.total_budget
        
        assert total_cost <= total_budget * 1.1, \
               f"Cost {total_cost} exceeds budget {total_budget}"
    
    def test_operating_hours_respected(self, sample_preferences, sample_places):
        """Test all activities are within 8 AM - 10 PM"""
        from app.services.google_maps import GoogleMapsService
        from app.core.scoring import ActivityScorer
        from datetime import datetime
        
        solver = ConstraintSolver(GoogleMapsService())
        scorer = ActivityScorer(sample_preferences)
        scored_activities = scorer.rank_activities(sample_places)
        
        result = solver.solve(
            places=sample_places,
            preferences=sample_preferences,
            scored_activities=scored_activities
        )
        
        for day_key, day_data in result['itinerary'].items():
            for activity in day_data['activities']:
                start_time = datetime.strptime(activity['start_time'], "%H:%M").time()
                end_time = datetime.strptime(activity['end_time'], "%H:%M").time()
                
                assert start_time >= time(8, 0), \
                       f"Activity starts before 8 AM: {start_time}"
                assert end_time <= time(22, 0), \
                       f"Activity ends after 10 PM: {end_time}"
    
    def test_meals_at_correct_times(self, sample_preferences, sample_places):
        """Test meals are scheduled at breakfast/lunch/dinner times"""
        from app.services.google_maps import GoogleMapsService
        from app.core.scoring import ActivityScorer
        from datetime import datetime
        
        solver = ConstraintSolver(GoogleMapsService())
        scorer = ActivityScorer(sample_preferences)
        scored_activities = scorer.rank_activities(sample_places)
        
        result = solver.solve(
            places=sample_places,
            preferences=sample_preferences,
            scored_activities=scored_activities
        )
        
        meal_times = []
        for day_key, day_data in result['itinerary'].items():
            for activity in day_data['activities']:
                if activity['category'] == 'restaurant':
                    start_hour = datetime.strptime(activity['start_time'], "%H:%M").hour
                    meal_times.append(start_hour)
        
        # Check meals are around breakfast (8), lunch (13), dinner (20)
        for meal_hour in meal_times:
            assert (7 <= meal_hour <= 9) or \
                   (12 <= meal_hour <= 14) or \
                   (19 <= meal_hour <= 21), \
                   f"Meal at incorrect time: {meal_hour}:00"
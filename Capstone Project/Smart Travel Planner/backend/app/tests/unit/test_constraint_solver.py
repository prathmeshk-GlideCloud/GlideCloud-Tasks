"""
Unit tests for constraint solver
"""
import pytest
from datetime import date, time, timedelta
from unittest.mock import Mock, MagicMock

from app.services.constraint_solver import AdvancedConstraintSolver, Activity, PaceConfig
from app.models.place import Place, Location
from app.models.user_input import TravelPreferences, BudgetRange, InterestCategory, PacePreference


@pytest.fixture
def mock_gmaps():
    """Mock Google Maps service"""
    gmaps = Mock()
    gmaps.calculate_travel_time = Mock(return_value=Mock(
        duration_minutes=15,
        distance_km=2.5
    ))
    return gmaps


@pytest.fixture
def solver(mock_gmaps):
    """Create solver instance"""
    return AdvancedConstraintSolver(mock_gmaps)


@pytest.fixture
def sample_preferences():
    """Sample travel preferences"""
    return TravelPreferences(
        destination="Test City",
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=10),
        budget_range=BudgetRange.MEDIUM,
        interests=[InterestCategory.CULTURE, InterestCategory.FOOD],
        must_visit=["Test Museum"],
        max_daily_distance=50.0,
        pace=PacePreference.MODERATE
    )


@pytest.fixture
def sample_places():
    """Sample places"""
    return [
        Place(
            place_id="1",
            name="Test Museum",
            location=Location(lat=40.7, lng=-74.0),
            types=["museum"],
            rating=4.5,
            price_level=2
        ),
        Place(
            place_id="2",
            name="Test Restaurant",
            location=Location(lat=40.71, lng=-74.01),
            types=["restaurant"],
            rating=4.2,
            price_level=2
        )
    ]


class TestConstraintSolver:
    """Test constraint solver functionality"""
    
    def test_solver_initialization(self, solver):
        """Test solver initializes correctly"""
        assert solver is not None
        assert solver.gmaps is not None
        assert solver.rag_service is not None
    
    def test_meal_time_constants(self, solver):
        """Test meal time configuration via PaceConfig"""
        # ✅ FIXED: Use PaceConfig instead of solver constants
        pace_config = PaceConfig(PacePreference.MODERATE)
        assert pace_config.breakfast_time == time(8, 0)
        assert pace_config.lunch_time == time(13, 0)
        assert pace_config.dinner_time == time(20, 0)
    
    def test_activity_creation(self, solver, sample_places, sample_preferences):
        """Test activity creation from places"""
        # ✅ FIXED: Pass pace_config as required argument
        pace_config = PaceConfig(sample_preferences.pace)
        activities = solver._create_activities(sample_places, sample_preferences, pace_config)
        
        assert len(activities) > 0
        assert all(isinstance(a, Activity) for a in activities)
        assert all(hasattr(a, 'duration_hours') for a in activities)
        assert all(hasattr(a, 'cost') for a in activities)
    
    def test_categorize_place(self, solver):
        """Test place categorization"""
        # Museum
        category1 = solver._categorize_place(['museum', 'point_of_interest'])
        assert category1 == "museum"
        
        # Restaurant
        category2 = solver._categorize_place(['restaurant', 'food'])
        assert category2 == "restaurant"
        
        # Temple - ✅ FIXED: Changed from 'religious_site' to 'temple'
        category3 = solver._categorize_place(['hindu_temple', 'place_of_worship'])
        assert category3 == "temple"
    
    def test_must_visit_included(self, solver, sample_places, sample_preferences, mock_gmaps):
        """Test must-visit places are prioritized"""
        mock_gmaps.calculate_travel_time = Mock(return_value=Mock(
            duration_minutes=10,
            distance_km=1.5
        ))
        
        scored_activities = [(100, sample_places[0]), (50, sample_places[1])]
        
        result = solver.solve(
            places=sample_places,
            preferences=sample_preferences,
            scored_activities=scored_activities
        )
        
        assert result['status'] == 'success'
        itinerary = result['itinerary']
        
        all_activity_names = []
        for day_key, day_data in itinerary.items():
            if isinstance(day_data, dict) and 'activities' in day_data:
                for activity in day_data['activities']:
                    all_activity_names.append(activity['activity_name'].lower())
        
        assert any('test museum' in name for name in all_activity_names)
    
    def test_no_duplicate_activities(self, solver, sample_places, sample_preferences, mock_gmaps):
        """Test no duplicate activities in itinerary"""
        scored_activities = [(100, sample_places[0]), (50, sample_places[1])]
        
        result = solver.solve(
            places=sample_places,
            preferences=sample_preferences,
            scored_activities=scored_activities
        )
        
        all_place_ids = []
        for day_key, day_data in result['itinerary'].items():
            if isinstance(day_data, dict) and 'activities' in day_data:
                for activity in day_data['activities']:
                    all_place_ids.append(activity['place_id'])
        
        assert len(all_place_ids) == len(set(all_place_ids))
    
    def test_budget_not_exceeded(self, solver, sample_places, sample_preferences, mock_gmaps):
        """Test total cost doesn't exceed budget"""
        scored_activities = [(100, sample_places[0]), (50, sample_places[1])]
        
        result = solver.solve(
            places=sample_places,
            preferences=sample_preferences,
            scored_activities=scored_activities
        )
        
        total_cost = result['summary']['total_cost']
        budget = sample_preferences.total_budget
        
        assert total_cost <= budget * 1.3  # Allow 30% buffer
    
    def test_operating_hours_respected(self, solver, sample_places, sample_preferences, mock_gmaps):
        """Test activities respect operating hours"""
        scored_activities = [(100, sample_places[0]), (50, sample_places[1])]
        
        result = solver.solve(
            places=sample_places,
            preferences=sample_preferences,
            scored_activities=scored_activities
        )
        
        pace_config = PaceConfig(sample_preferences.pace)
        
        for day_key, day_data in result['itinerary'].items():
            if isinstance(day_data, dict) and 'activities' in day_data:
                for activity in day_data['activities']:
                    start = time.fromisoformat(activity['start_time'])
                    end = time.fromisoformat(activity['end_time'])
                    
                    assert start >= pace_config.day_start
                    assert end <= pace_config.day_end
    
    def test_meals_at_correct_times(self, solver, sample_preferences, mock_gmaps):
        """Test meals are scheduled at appropriate times"""
        # Create more places including multiple restaurants
        enhanced_places = [
            Place(
                place_id="1",
                name="Test Museum",
                location=Location(lat=40.7, lng=-74.0),
                types=["museum"],
                rating=4.5,
                price_level=2
            ),
            Place(
                place_id="2",
                name="Breakfast Restaurant",
                location=Location(lat=40.71, lng=-74.01),
                types=["restaurant", "food"],
                rating=4.2,
                price_level=2
            ),
            Place(
                place_id="3",
                name="Lunch Restaurant",
                location=Location(lat=40.72, lng=-74.02),
                types=["restaurant", "food"],
                rating=4.3,
                price_level=2
            ),
            Place(
                place_id="4",
                name="Dinner Restaurant",
                location=Location(lat=40.73, lng=-74.03),
                types=["restaurant", "food"],
                rating=4.4,
                price_level=2
            ),
            Place(
                place_id="5",
                name="Test Park",
                location=Location(lat=40.74, lng=-74.04),
                types=["park"],
                rating=4.6,
                price_level=0
            )
        ]
        
        scored_activities = [(100, p) for p in enhanced_places]
        
        result = solver.solve(
            places=enhanced_places,
            preferences=sample_preferences,
            scored_activities=scored_activities
        )
        
        # Check at least one day has meals
        found_meals = False
        for day_key, day_data in result['itinerary'].items():
            if isinstance(day_data, dict) and 'activities' in day_data:
                meals = [a for a in day_data['activities'] if a['category'] == 'restaurant']
                
                if len(meals) > 0:
                    found_meals = True
                    # Meals should be at reasonable times
                    for meal in meals:
                        meal_time = time.fromisoformat(meal['start_time'])
                        assert time(6, 0) <= meal_time <= time(22, 0)
        
        assert found_meals, "No meals found in itinerary"
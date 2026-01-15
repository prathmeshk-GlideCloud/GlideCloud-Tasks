"""
Pytest fixtures and configuration
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.google_maps import GoogleMapsService
from datetime import date, timedelta


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def gmaps_service():
    """Google Maps service instance"""
    return GoogleMapsService()


@pytest.fixture
def sample_location():
    """Sample location for testing"""
    from app.models.place import Location
    return Location(lat=48.8566, lng=2.3522)  # Paris


@pytest.fixture
def sample_preferences():
    """Sample travel preferences"""
    from app.models.user_input import TravelPreferences, BudgetRange
    
    return TravelPreferences(
        destination="Paris, France",
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=10),
        budget_range=BudgetRange.MEDIUM,
        interests=["culture", "food"]
    )


@pytest.fixture
def sample_preferences_low_budget():
    """Sample preferences with low budget"""
    from app.models.user_input import TravelPreferences, BudgetRange
    
    return TravelPreferences(
        destination="Tokyo, Japan",
        start_date=date.today() + timedelta(days=14),
        end_date=date.today() + timedelta(days=17),
        budget_range=BudgetRange.LOW,
        interests=["culture", "food"],
        must_visit=["Senso-ji Temple"]
    )
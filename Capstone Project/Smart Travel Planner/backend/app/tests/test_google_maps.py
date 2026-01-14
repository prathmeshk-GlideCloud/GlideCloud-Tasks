"""
Unit tests for Google Maps service
"""
import pytest
from app.services.google_maps import GoogleMapsService
from app.models.place import Location


def test_geocode_location(gmaps_service):
    """Test location geocoding"""
    location = gmaps_service.geocode_location("Paris, France")
    
    assert location is not None
    assert isinstance(location, Location)
    assert 48.8 < location.lat < 48.9  # Paris latitude range
    assert 2.3 < location.lng < 2.4    # Paris longitude range


def test_search_places(gmaps_service):
    """Test place search"""
    places = gmaps_service.search_places(
        query="museums",
        location="Paris, France",
        radius=5000
    )
    
    assert len(places) > 0
    assert all(hasattr(p, 'place_id') for p in places)
    assert all(hasattr(p, 'name') for p in places)


def test_calculate_travel_time(gmaps_service, sample_location):
    """Test travel time calculation"""
    # Paris to Eiffel Tower
    destination = Location(lat=48.8584, lng=2.2945)
    
    travel_info = gmaps_service.calculate_travel_time(
        origin=sample_location,
        destination=destination,
        mode="walking"
    )
    
    assert travel_info is not None
    assert travel_info.distance_meters > 0
    assert travel_info.duration_seconds > 0


def test_search_by_interest(gmaps_service):
    """Test interest-based search"""
    places = gmaps_service.search_places_by_interest(
        interest="culture",
        location="Paris, France",
        radius=10000
    )
    
    assert len(places) > 0
    # Check that places are related to culture
    assert any('museum' in p.types or 'art_gallery' in p.types for p in places)
"""
Manual testing script for Google Maps integration
"""
import sys
sys.path.append('..')

from app.services.google_maps import GoogleMapsService
from app.models.place import Location


def test_basic_functionality():
    """Test basic Google Maps functionality"""
    print("=" * 60)
    print("Testing Google Maps Integration")
    print("=" * 60)
    
    gmaps = GoogleMapsService()
    
    # Test 1: Geocoding
    print("\n1. Testing Geocoding...")
    location = gmaps.geocode_location("Paris, France")
    if location:
        print(f"   ✓ Paris coordinates: {location.lat}, {location.lng}")
    else:
        print("   ✗ Geocoding failed")
        return
    
    # Test 2: Place Search
    print("\n2. Testing Place Search...")
    places = gmaps.search_places(
        query="museums",
        location="Paris, France",
        radius=5000
    )
    print(f"   ✓ Found {len(places)} museums")
    if places:
        print(f"   Example: {places[0].name} (Rating: {places[0].rating})")
    
    # Test 3: Interest-based Search
    print("\n3. Testing Interest-based Search...")
    culture_places = gmaps.search_places_by_interest(
        interest="culture",
        location="Paris, France"
    )
    print(f"   ✓ Found {len(culture_places)} cultural places")
    
    # Test 4: Travel Time
    print("\n4. Testing Travel Time Calculation...")
    if len(places) >= 2:
        travel = gmaps.calculate_travel_time(
            origin=places[0].location,
            destination=places[1].location,
            mode="walking"
        )
        if travel:
            print(f"   ✓ Distance: {travel.distance_text}")
            print(f"   ✓ Duration: {travel.duration_text}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_basic_functionality()
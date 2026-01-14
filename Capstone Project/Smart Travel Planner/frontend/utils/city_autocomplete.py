"""
Real-time city autocomplete using Google Places API
"""
import requests
from typing import List
import os


def get_city_suggestions(search_term: str) -> List[str]:
    """
    Get city suggestions from Google Places Autocomplete API
    
    Args:
        search_term: User's input text
        
    Returns:
        List of city suggestions
    """
    # Return empty if search term is too short
    if not search_term or len(search_term) < 2:
        return []
    
    # Get API key from environment or config
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    # If no API key, return empty
    if not api_key:
        return []
    
    # Google Places Autocomplete endpoint
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    
    # Parameters for city-only search
    params = {
        'input': search_term,
        'types': '(cities)',  # Only cities
        'key': api_key
    }
    
    try:
        # Make API request with timeout
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if request was successful
        if data.get('status') == 'OK':
            predictions = data.get('predictions', [])
            
            # Extract city names
            cities = [pred['description'] for pred in predictions]
            
            return cities[:10]  # Return top 10 suggestions
        
        elif data.get('status') == 'ZERO_RESULTS':
            return []
        
        else:
            print(f"Google API Status: {data.get('status')}")
            return []
    
    except requests.exceptions.Timeout:
        print("Google Places API request timed out")
        return []
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching city suggestions: {e}")
        return []
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def search_cities_wrapper(search_term: str) -> List[str]:
    """
    Wrapper function for streamlit-searchbox
    
    Args:
        search_term: User's search input
        
    Returns:
        List of city suggestions
    """
    suggestions = get_city_suggestions(search_term)
    
    # If API returns no results, show a helpful message
    if not suggestions and search_term and len(search_term) >= 2:
        return [f"No cities found for '{search_term}'"]
    
    return suggestions
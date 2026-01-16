"""
Google Maps API integration service
"""
import googlemaps
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.config import settings
from app.models.place import Place, Location, TravelInfo, OpeningHours

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Service for interacting with Google Maps API"""
    
    def __init__(self):
        """Initialize Google Maps client"""
        self.client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        logger.info("Google Maps service initialized")
    
    def geocode_location(self, location: str) -> Optional[Location]:
        """Convert location string to coordinates"""
        try:
            result = self.client.geocode(location)
            if result:
                coords = result[0]['geometry']['location']
                return Location(lat=coords['lat'], lng=coords['lng'])
            return None
        except Exception as e:
            logger.error(f"Geocoding error for {location}: {e}")
            return None
    
    def search_places(
        self,
        query: str,
        location: str,
        radius: int = 10000,
        place_type: Optional[str] = None
    ) -> List[Place]:
        """Search for places using Google Places API"""
        try:
            # Geocode location
            if isinstance(location, str):
                coords = self.geocode_location(location)
                if not coords:
                    logger.error(f"Could not geocode location: {location}")
                    return []
            else:
                coords = location
            
            # Search places
            places_result = self.client.places_nearby(
                location=(coords.lat, coords.lng),
                radius=radius,
                keyword=query,
                type=place_type
            )
            
            # Parse results
            places = []
            for place_data in places_result.get('results', []):
                try:
                    place = self._parse_place(place_data)
                    places.append(place)
                except Exception as e:
                    logger.warning(f"Error parsing place: {e}")
                    continue
            
            logger.info(f"Found {len(places)} places for query: {query}")
            return places
            
        except Exception as e:
            logger.error(f"Places search error: {e}")
            return []
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information about a place"""
        try:
            result = self.client.place(
                place_id,
                fields=[
                    'name', 'formatted_address', 'formatted_phone_number',
                    'opening_hours', 'website', 'rating', 'reviews',
                    'price_level', 'geometry', 'types', 'photos'
                ]
            )
            return result.get('result')
        except Exception as e:
            logger.error(f"Error getting place details for {place_id}: {e}")
            return None
    
    def calculate_travel_time(
        self,
        origin: Location,
        destination: Location,
        mode: str = "driving",
        departure_time: Optional[datetime] = None
    ) -> Optional[TravelInfo]:
        """Calculate travel time between two locations"""
        try:
            if departure_time is None:
                departure_time = datetime.now()
            
            result = self.client.directions(
                origin=(origin.lat, origin.lng),
                destination=(destination.lat, destination.lng),
                mode=mode,
                departure_time=departure_time
            )
            
            if not result:
                return None
            
            leg = result[0]['legs'][0]
            
            return TravelInfo(
                origin=origin,
                destination=destination,
                distance_meters=leg['distance']['value'],
                distance_text=leg['distance']['text'],
                duration_seconds=leg['duration']['value'],
                duration_text=leg['duration']['text'],
                mode=mode
            )
            
        except Exception as e:
            logger.error(f"Error calculating travel time: {e}")
            return None
    
    def get_distance_matrix(
        self,
        origins: List[Location],
        destinations: List[Location],
        mode: str = "driving"
    ) -> Optional[List[List[TravelInfo]]]:
        """Get distance matrix for multiple origin-destination pairs"""
        try:
            origin_coords = [(o.lat, o.lng) for o in origins]
            dest_coords = [(d.lat, d.lng) for d in destinations]
            
            result = self.client.distance_matrix(
                origins=origin_coords,
                destinations=dest_coords,
                mode=mode
            )
            
            matrix = []
            for i, row in enumerate(result['rows']):
                matrix_row = []
                for j, element in enumerate(row['elements']):
                    if element['status'] == 'OK':
                        travel_info = TravelInfo(
                            origin=origins[i],
                            destination=destinations[j],
                            distance_meters=element['distance']['value'],
                            distance_text=element['distance']['text'],
                            duration_seconds=element['duration']['value'],
                            duration_text=element['duration']['text'],
                            mode=mode
                        )
                        matrix_row.append(travel_info)
                    else:
                        matrix_row.append(None)
                matrix.append(matrix_row)
            
            return matrix
            
        except Exception as e:
            logger.error(f"Error getting distance matrix: {e}")
            return None
    
    def search_places_by_interest(
        self,
        interest: str,
        location: str,
        radius: int = 10000
    ) -> List[Place]:
        """Search places based on interest category"""
        interest_mapping = {
            'culture': {
                'types': ['museum', 'art_gallery', 'library'],
                'queries': ['museums', 'art galleries', 'cultural centers']
            },
            'food': {
                'types': ['restaurant', 'cafe', 'bakery'],
                'queries': ['restaurants', 'cafes', 'local cuisine']
            },
            'adventure': {
                'types': ['park', 'amusement_park'],
                'queries': ['adventure activities', 'outdoor activities']
            },
            'nature': {
                'types': ['park', 'natural_feature'],
                'queries': ['parks', 'gardens', 'nature spots']
            },
            'shopping': {
                'types': ['shopping_mall', 'store'],
                'queries': ['shopping centers', 'markets']
            },
            'history': {
                'types': ['museum', 'historical_place'],
                'queries': ['historical sites', 'monuments']
            },
            'nightlife': {
                'types': ['bar', 'night_club'],
                'queries': ['bars', 'nightlife', 'entertainment']
            }
        }
        
        interest_lower = interest.lower()
        
        if interest_lower not in interest_mapping:
            return self.search_places(interest, location, radius)
        
        # Search by type
        all_places = []
        mapping = interest_mapping[interest_lower]
        
        for place_type in mapping['types']:
            places = self.search_places(
                query=place_type,
                location=location,
                radius=radius,
                place_type=place_type
            )
            all_places.extend(places)
        
        # Remove duplicates
        seen_ids = set()
        unique_places = []
        for place in all_places:
            if place.place_id not in seen_ids:
                seen_ids.add(place.place_id)
                unique_places.append(place)
        
        return unique_places
    
    def _parse_place(self, place_data: Dict) -> Place:
        """Parse Google Places API response into Place object"""
        location = Location(
            lat=place_data['geometry']['location']['lat'],
            lng=place_data['geometry']['location']['lng']
        )
        
        opening_hours = None
        if 'opening_hours' in place_data:
            opening_hours = OpeningHours(
                open_now=place_data['opening_hours'].get('open_now', False),
                weekday_text=place_data['opening_hours'].get('weekday_text')
            )
        
        return Place(
            place_id=place_data['place_id'],
            name=place_data['name'],
            formatted_address=place_data.get('vicinity'),
            location=location,
            rating=place_data.get('rating', 0.0),
            user_ratings_total=place_data.get('user_ratings_total', 0),
            types=place_data.get('types', []),
            price_level=place_data.get('price_level', 2),
            opening_hours=opening_hours,
            photos=place_data.get('photos', []),
            website=place_data.get('website')
        )
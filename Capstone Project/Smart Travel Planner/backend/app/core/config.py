import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

PLACES_RADIUS_METERS = 5000
MIN_RATING = 3.5

"""
Health check endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
import logging

from app.config import settings
from app.services.google_maps import GoogleMapsService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check() -> Dict:
    """Basic health check"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@router.get("/health/google-maps")
async def google_maps_health() -> Dict:
    """Check Google Maps API connection"""
    try:
        gmaps = GoogleMapsService()
        
        # Test geocoding
        location = gmaps.geocode_location("Paris, France")
        
        if location:
            return {
                "status": "healthy",
                "service": "Google Maps API",
                "test_result": "Geocoding successful"
            }
        else:
            raise HTTPException(
                status_code=503,
                detail="Google Maps API geocoding failed"
            )
            
    except Exception as e:
        logger.error(f"Google Maps health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Google Maps API error: {str(e)}"
        )
"""
API Client for backend communication
"""
import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """Client for Smart Travel Planner API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self) -> Dict:
        """Check API health"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def generate_itinerary(self, preferences: Dict, optimize_for: str = "time") -> Dict:
        """
        Generate travel itinerary

        Args:
            preferences: User preferences dict
            optimize_for: Optimization mode (time, cost, balanced)

        Returns:
            Itinerary result
        """
        try:
            # 🔒 Sanitize preferences (CRITICAL)
            clean_preferences = {
                k: v for k, v in preferences.items()
                if v is not None
            }

            # 🔒 Ensure required fields exist (backend expects these)
            required_fields = [
                "destination",
                "start_date",
                "end_date",
                "interests",
                "pace",
                "max_daily_distance"
            ]

            for field in required_fields:
                if field not in clean_preferences:
                    return {
                        "status": "error",
                        "message": f"Missing required field: {field}"
                    }

            payload = {
                "preferences": clean_preferences,
                "optimize_for": optimize_for
            }

            response = requests.post(
                f"{self.base_url}/api/planner/generate",
                json=payload,
                timeout=180  # solver + Google Maps can be slow
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Request timed out. Try reducing trip length or distance."
            }

        except requests.exceptions.HTTPError as e:
            return {
                "status": "error",
                "message": f"Backend rejected request: {e.response.text}"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {
                "status": "error",
                "message": f"Failed to connect to backend: {str(e)}"
            }

    
    def ask_question(self, question: str) -> Dict:
        """Ask travel question to RAG system"""
        try:
            response = requests.post(
                f"{self.base_url}/api/rag/ask",
                json={"question": question},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Question failed: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "confidence": 0.0
            }
"""
API Client with better error handling
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
    
    def generate_itinerary(
        self,
        preferences: Dict,
        optimize_for: str = "time",
        budget_mode: str = "range",
        custom_budget: Optional[float] = None
    ) -> Dict:
        """Generate travel itinerary"""
        try:
            # Ensure budget fields are set correctly
            if budget_mode == "custom_amount" and custom_budget:
                preferences["custom_budget"] = float(custom_budget)
                preferences["budget_range"] = None
            else:
                # Quick select mode
                preferences["custom_budget"] = None
                # budget_range should already be in preferences
            
            payload = {
                "preferences": preferences,
                "optimize_for": optimize_for
            }
            
            # Log the request for debugging
            logger.info(f"Sending request to {self.base_url}/api/planner/generate")
            logger.info(f"Payload: {payload}")
            
            response = requests.post(
                f"{self.base_url}/api/planner/generate",
                json=payload,
                timeout=300
            )
            
            # Check for errors
            if response.status_code != 200:
                error_detail = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                logger.error(f"API Error ({response.status_code}): {error_detail}")
                
                # Extract validation errors if present
                if response.status_code == 422:
                    try:
                        error_data = response.json()
                        if 'detail' in error_data:
                            errors = error_data['detail']
                            if isinstance(errors, list):
                                error_messages = [f"{err.get('loc', ['unknown'])[1]}: {err.get('msg', 'error')}" for err in errors]
                                return {
                                    "status": "error",
                                    "message": f"Validation errors:\n" + "\n".join(error_messages)
                                }
                    except:
                        pass
                
                return {
                    "status": "error",
                    "message": f"API Error ({response.status_code}): {error_detail}"
                }
            
            result = response.json()
            logger.info(f"Response status: {result.get('status')}")
            return result
            
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Request timed out. Try a more specific location."
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {
                "status": "error",
                "message": f"Connection error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def ask_question(self, question: str) -> Dict:
        """Ask travel question"""
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
            return {"answer": f"Error: {str(e)}", "confidence": 0.0}
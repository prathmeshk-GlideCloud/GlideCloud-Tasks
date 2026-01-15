import pytest
from datetime import date, timedelta
from app.models.user_input import TravelPreferences, BudgetRange
from pydantic import ValidationError

class TestTravelPreferences:
    
    def test_valid_preferences(self):
        """Test valid preferences are accepted"""
        prefs = TravelPreferences(
            destination="Pune, India",
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=5),
            budget_range=BudgetRange.MEDIUM,
            interests=["culture", "food"]
        )
        assert prefs.destination == "Pune, India"
        assert prefs.num_days == 5
    
    def test_past_start_date_rejected(self):
        """Test past dates are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TravelPreferences(
                destination="Pune",
                start_date=date.today() - timedelta(days=1),  # Past date
                end_date=date.today() + timedelta(days=5),
                budget_range=BudgetRange.MEDIUM,
                interests=["culture"]
            )
        assert "past" in str(exc_info.value).lower()
    
    def test_end_before_start_rejected(self):
        """Test end date before start date is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TravelPreferences(
                destination="Pune",
                start_date=date.today() + timedelta(days=5),
                end_date=date.today() + timedelta(days=1),  # Before start
                budget_range=BudgetRange.MEDIUM,
                interests=["culture"]
            )
        assert "after" in str(exc_info.value).lower()
    
    def test_custom_budget_validation(self):
        """Test custom budget validation"""
        # Too low
        with pytest.raises(ValidationError):
            TravelPreferences(
                destination="Pune",
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=5),
                custom_budget=2000,  # ₹400/day - too low
                interests=["culture"]
            )
        
        # Too high
        with pytest.raises(ValidationError):
            TravelPreferences(
                destination="Pune",
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=5),
                custom_budget=500000,  # ₹100K/day - unrealistic
                interests=["culture"]
            )
    
    def test_effective_budget_range_inference(self):
        """Test budget range is inferred from custom budget"""
        prefs = TravelPreferences(
            destination="Pune",
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=5),
            custom_budget=30000,  # ₹6000/day
            interests=["culture"]
        )
        assert prefs.effective_budget_range == BudgetRange.MEDIUM
    
    def test_either_budget_range_or_custom_required(self):
        """Test at least one budget field is required"""
        with pytest.raises(ValidationError) as exc_info:
            TravelPreferences(
                destination="Pune",
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=5),
                # No budget fields
                interests=["culture"]
            )
        assert "budget" in str(exc_info.value).lower()
"""
Input validation utilities
"""
from typing import List
from datetime import date


def validate_date_range(start_date: date, end_date: date) -> bool:
    """Validate date range"""
    if start_date >= end_date:
        return False
    if start_date < date.today():
        return False
    return True


def validate_budget(budget: float, num_days: int) -> bool:
    """Validate budget is reasonable"""
    daily_budget = budget / num_days
    # Minimum $50 per day
    return daily_budget >= 50


def sanitize_location_string(location: str) -> str:
    """Clean and sanitize location input"""
    return location.strip().title()
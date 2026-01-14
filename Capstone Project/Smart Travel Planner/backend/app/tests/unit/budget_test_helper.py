"""
Unit tests for budget helper utilities
"""
import pytest
from app.utils.budget_helper import BudgetHelper
from app.models.user_input import BudgetRange


def test_get_daily_budget():
    """Test daily budget calculation"""
    assert BudgetHelper.get_daily_budget(BudgetRange.LOW) == 75.0
    assert BudgetHelper.get_daily_budget(BudgetRange.MEDIUM) == 150.0
    assert BudgetHelper.get_daily_budget(BudgetRange.HIGH) == 300.0


def test_get_total_budget():
    """Test total budget calculation"""
    assert BudgetHelper.get_total_budget(BudgetRange.LOW, 3) == 225.0
    assert BudgetHelper.get_total_budget(BudgetRange.MEDIUM, 5) == 750.0
    assert BudgetHelper.get_total_budget(BudgetRange.HIGH, 7) == 2100.0


def test_get_activity_budget():
    """Test activity budget allocation"""
    # Low budget: $20/day activities
    assert BudgetHelper.get_activity_budget(BudgetRange.LOW, 3) == 60.0
    
    # Medium budget: $30/day activities
    assert BudgetHelper.get_activity_budget(BudgetRange.MEDIUM, 5) == 150.0
    
    # High budget: $60/day activities
    assert BudgetHelper.get_activity_budget(BudgetRange.HIGH, 7) == 420.0


def test_can_afford_activity():
    """Test activity affordability check"""
    # Low budget can afford $20-40 activities
    assert BudgetHelper.can_afford_activity(30, BudgetRange.LOW) == True
    assert BudgetHelper.can_afford_activity(50, BudgetRange.LOW) == False
    
    # Medium budget can afford $30-60 activities
    assert BudgetHelper.can_afford_activity(50, BudgetRange.MEDIUM) == True
    assert BudgetHelper.can_afford_activity(80, BudgetRange.MEDIUM) == False


def test_estimate_activity_cost():
    """Test activity cost estimation"""
    # Free activities
    assert BudgetHelper.estimate_activity_cost(0, BudgetRange.LOW) == 0
    assert BudgetHelper.estimate_activity_cost(0, BudgetRange.HIGH) == 0
    
    # Moderate activities (price_level = 2)
    low_cost = BudgetHelper.estimate_activity_cost(2, BudgetRange.LOW)
    med_cost = BudgetHelper.estimate_activity_cost(2, BudgetRange.MEDIUM)
    high_cost = BudgetHelper.estimate_activity_cost(2, BudgetRange.HIGH)
    
    assert low_cost < med_cost < high_cost
    assert med_cost == 25.0  # Base cost for price_level 2


def test_get_budget_info():
    """Test getting complete budget info"""
    info = BudgetHelper.get_budget_info(BudgetRange.MEDIUM)
    
    assert info['average'] == 150
    assert 'breakdown' in info
    assert info['breakdown']['accommodation'] == 60
    assert info['breakdown']['food'] == 45
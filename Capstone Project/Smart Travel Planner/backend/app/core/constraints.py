"""
Constraint classes for travel planning
These define the rules that must be satisfied when creating itineraries
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, time, timedelta
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class Constraint(ABC):
    """Base constraint class"""
    
    def __init__(self, priority: int, name: str):
        """
        Args:
            priority: 1 = Hard (must satisfy), 2 = Soft (should satisfy), 3 = Preference
            name: Human-readable constraint name
        """
        self.priority = priority
        self.name = name
    
    @abstractmethod
    def is_satisfied(self, schedule: List[Dict]) -> bool:
        """Check if constraint is satisfied"""
        pass
    
    @abstractmethod
    def get_violation_score(self, schedule: List[Dict]) -> float:
        """Calculate penalty for violating this constraint"""
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}(priority={self.priority}, name='{self.name}')"


class TimeWindowConstraint(Constraint):
    """Constraint for daily time windows - UPDATED TO 8 AM - 10 PM"""
    
    def __init__(self, start_time: str = "08:00", end_time: str = "22:00"):
        super().__init__(priority=1, name="Time Window")
        self.start_time = datetime.strptime(start_time, "%H:%M").time()
        self.end_time = datetime.strptime(end_time, "%H:%M").time()
    
    def is_satisfied(self, schedule: List[Dict]) -> bool:
        """Check if all activities are within time window"""
        for activity in schedule:
            if 'start_time' not in activity or 'end_time' not in activity:
                continue
            
            start = self._parse_time(activity['start_time'])
            end = self._parse_time(activity['end_time'])
            
            if start < self.start_time or end > self.end_time:
                return False
        
        return True
    
    def get_violation_score(self, schedule: List[Dict]) -> float:
        """Penalty for activities outside time window"""
        penalty = 0.0
        for activity in schedule:
            start = self._parse_time(activity.get('start_time', '09:00'))
            end = self._parse_time(activity.get('end_time', '09:00'))
            
            if start < self.start_time:
                penalty += 100.0
            if end > self.end_time:
                penalty += 100.0
        
        return penalty
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object"""
        if isinstance(time_str, time):
            return time_str
        return datetime.strptime(str(time_str), "%H:%M").time()


class BudgetConstraint(Constraint):
    """Constraint for total budget"""
    
    def __init__(self, max_budget: float):
        super().__init__(priority=1, name="Budget")
        self.max_budget = max_budget
    
    def is_satisfied(self, schedule: List[Dict]) -> bool:
        """Check if total cost is within budget"""
        total_cost = sum(activity.get('cost', 0) for activity in schedule)
        return total_cost <= self.max_budget
    
    def get_violation_score(self, schedule: List[Dict]) -> float:
        """Penalty proportional to budget overage"""
        total_cost = sum(activity.get('cost', 0) for activity in schedule)
        if total_cost > self.max_budget:
            overage_percentage = (total_cost - self.max_budget) / self.max_budget
            return overage_percentage * 1000.0  # Heavy penalty
        return 0.0


class DailyDistanceConstraint(Constraint):
    """Constraint for maximum daily travel distance"""
    
    def __init__(self, max_daily_km: float = 50.0):
        super().__init__(priority=2, name="Daily Distance")
        self.max_daily_km = max_daily_km
    
    def is_satisfied(self, schedule: List[Dict]) -> bool:
        """Check if total daily travel is within limit"""
        total_distance = sum(
            activity.get('travel_from_previous', {}).get('distance_km', 0)
            for activity in schedule
        )
        return total_distance <= self.max_daily_km
    
    def get_violation_score(self, schedule: List[Dict]) -> float:
        """Penalty for exceeding daily distance"""
        total_distance = sum(
            activity.get('travel_from_previous', {}).get('distance_km', 0)
            for activity in schedule
        )
        if total_distance > self.max_daily_km:
            excess = total_distance - self.max_daily_km
            return excess * 5.0  # Penalty per excess km
        return 0.0


class MustVisitConstraint(Constraint):
    """Constraint for must-visit places"""
    
    def __init__(self, must_visit_places: List[str]):
        super().__init__(priority=1, name="Must Visit")
        self.must_visit_places = [p.lower().strip() for p in must_visit_places]
    
    def is_satisfied(self, schedule: List[Dict]) -> bool:
        """Check if all must-visit places are included"""
        if not self.must_visit_places:
            return True
        
        visited = [
            activity.get('activity_name', '').lower().strip()
            for activity in schedule
        ]
        
        for must_visit in self.must_visit_places:
            # Check if any visited place contains the must-visit name
            if not any(must_visit in v for v in visited):
                return False
        
        return True
    
    def get_violation_score(self, schedule: List[Dict]) -> float:
        """Heavy penalty for missing must-visit places"""
        if not self.must_visit_places:
            return 0.0
        
        visited = [
            activity.get('activity_name', '').lower().strip()
            for activity in schedule
        ]
        
        missing_count = 0
        for must_visit in self.must_visit_places:
            if not any(must_visit in v for v in visited):
                missing_count += 1
        
        return missing_count * 500.0  # Very heavy penalty


class MealTimeConstraint(Constraint):
    """Constraint to ensure meals at appropriate times"""
    
    def __init__(self):
        super().__init__(priority=2, name="Meal Times")
        self.breakfast_window = (time(8, 0), time(10, 0))
        self.lunch_window = (time(12, 0), time(14, 30))
        self.dinner_window = (time(18, 30), time(21, 0))
    
    def is_satisfied(self, schedule: List[Dict]) -> bool:
        """Check if meals are scheduled at appropriate times"""
        # Soft constraint - always returns True but provides guidance via score
        return True
    
    def get_violation_score(self, schedule: List[Dict]) -> float:
        """Penalty for meals at odd times"""
        penalty = 0.0
        
        for activity in schedule:
            if activity.get('category') == 'restaurant':
                start = self._parse_time(activity.get('start_time', '12:00'))
                
                # Check if meal is during any meal window
                in_window = (
                    self._time_in_window(start, self.breakfast_window) or
                    self._time_in_window(start, self.lunch_window) or
                    self._time_in_window(start, self.dinner_window)
                )
                
                if not in_window:
                    penalty += 20.0
        
        return penalty
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string"""
        if isinstance(time_str, time):
            return time_str
        return datetime.strptime(str(time_str), "%H:%M").time()
    
    def _time_in_window(self, t: time, window: tuple) -> bool:
        """Check if time is within window"""
        return window[0] <= t <= window[1]


class ActivityVarietyConstraint(Constraint):
    """Constraint to ensure variety in activities"""
    
    def __init__(self):
        super().__init__(priority=3, name="Activity Variety")
    
    def is_satisfied(self, schedule: List[Dict]) -> bool:
        """Always satisfied - this is a preference"""
        return True
    
    def get_violation_score(self, schedule: List[Dict]) -> float:
        penalty = 0.0

        for i in range(len(schedule) - 1):
            c1 = schedule[i].get('category')
            c2 = schedule[i + 1].get('category')

            if c1 == c2 and c1 != 'restaurant':
                penalty += 40.0   # was 10

            if i < len(schedule) - 2:
                c3 = schedule[i + 2].get('category')
                if c1 == c2 == c3:
                    penalty += 100.0  # strong discouragement

        return penalty


class ConstraintManager:
    """Manages all constraints for a planning session"""
    
    def __init__(self):
        self.constraints: List[Constraint] = []
    
    def add_constraint(self, constraint: Constraint):
        """Add a constraint"""
        self.constraints.append(constraint)
        logger.debug(f"Added constraint: {constraint}")
    
    def check_all_constraints(self, schedule: List[Dict]) -> Dict[str, Any]:
        """
        Check all constraints and return detailed results
        
        Returns:
            Dictionary with satisfaction status and scores
        """
        results = {
            'all_satisfied': True,
            'hard_constraints_satisfied': True,
            'total_penalty': 0.0,
            'constraint_details': []
        }
        
        for constraint in self.constraints:
            satisfied = constraint.is_satisfied(schedule)
            penalty = constraint.get_violation_score(schedule)
            
            results['constraint_details'].append({
                'name': constraint.name,
                'priority': constraint.priority,
                'satisfied': satisfied,
                'penalty': penalty
            })
            
            results['total_penalty'] += penalty
            
            if not satisfied:
                results['all_satisfied'] = False
                if constraint.priority == 1:  # Hard constraint
                    results['hard_constraints_satisfied'] = False
        
        return results
    
    def get_hard_constraints(self) -> List[Constraint]:
        """Get all hard constraints (priority 1)"""
        return [c for c in self.constraints if c.priority == 1]
    
    def get_soft_constraints(self) -> List[Constraint]:
        """Get all soft constraints (priority 2+)"""
        return [c for c in self.constraints if c.priority >= 2]
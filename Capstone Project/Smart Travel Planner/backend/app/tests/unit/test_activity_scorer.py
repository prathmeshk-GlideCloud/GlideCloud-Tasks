# tests/unit/test_activity_scorer.py
import pytest
from app.core.scoring import ActivityScorer
from app.models.user_input import TravelPreferences, BudgetRange
from app.models.place import Place, Location
from datetime import date

@pytest.fixture
def sample_preferences():
    return TravelPreferences(
        destination="Pune, India",
        start_date=date(2026, 1, 21),
        end_date=date(2026, 1, 23),
        budget_range=BudgetRange.MEDIUM,
        interests=["culture", "history"],
        must_visit=["Shaniwar Wada"],
        pace="moderate"
    )

class TestActivityScorer:
    
    def test_scorer_initialization(self, sample_preferences):
        """Test scorer can be initialized with preferences"""
        scorer = ActivityScorer(sample_preferences)
        assert scorer.destination == "Pune, India"
        assert scorer.budget_range == BudgetRange.MEDIUM
        assert "culture" in scorer.interests
    
    def test_must_visit_gets_high_score(self, sample_preferences):
        """Test must-visit places get bonus score"""
        scorer = ActivityScorer(sample_preferences)
        
        must_visit_place = Place(
            place_id="1",
            name="Shaniwar Wada",
            formatted_address="Pune",
            location=Location(lat=18.5196, lng=73.8553),
            types=["tourist_attraction"],
            rating=4.5,
            user_ratings_total=10000,
            price_level=1
        )
        
        regular_place = Place(
            place_id="2",
            name="Regular Place",
            formatted_address="Pune",
            location=Location(lat=18.5196, lng=73.8553),
            types=["tourist_attraction"],
            rating=4.5,
            user_ratings_total=10000,
            price_level=1
        )
        
        must_visit_score = scorer.score_activity(must_visit_place)
        regular_score = scorer.score_activity(regular_place)
        
        # Must-visit should get 200 point bonus
        assert must_visit_score > regular_score + 150
    
    def test_interest_match_scoring(self, sample_preferences):
        """Test activities matching interests get higher scores"""
        scorer = ActivityScorer(sample_preferences)
        
        museum = Place(
            place_id="1",
            name="Museum",
            formatted_address="Pune",
            location=Location(lat=18.5196, lng=73.8553),
            types=["museum"],  # Matches "culture" interest
            rating=4.0,
            user_ratings_total=5000,
            price_level=2
        )
        
        mall = Place(
            place_id="2",
            name="Shopping Mall",
            formatted_address="Pune",
            location=Location(lat=18.5196, lng=73.8553),
            types=["shopping_mall"],  # Doesn't match interests
            rating=4.0,
            user_ratings_total=5000,
            price_level=2
        )
        
        museum_score = scorer.score_activity(museum)
        mall_score = scorer.score_activity(mall)
        
        assert museum_score > mall_score
    
    def test_ranking_preserves_order(self, sample_preferences):
        """Test ranking returns activities in score order"""
        scorer = ActivityScorer(sample_preferences)
        
        places = [
            Place(
                place_id="1", 
                name="Low", 
                formatted_address="Address A", 
                location=Location(lat=18.5196, lng=73.8553),
                types=["park"], 
                rating=3.0, 
                user_ratings_total=100, 
                price_level=1
            ),
            Place(
                place_id="2", 
                name="High", 
                formatted_address="Address B", 
                location=Location(lat=18.5204, lng=73.8567),
                types=["museum"], 
                rating=4.8, 
                user_ratings_total=10000, 
                price_level=2
            ),
            Place(
                place_id="3", 
                name="Medium", 
                formatted_address="Address C", 
                location=Location(lat=18.5515, lng=73.9029),
                types=["museum"], 
                rating=4.0, 
                user_ratings_total=5000, 
                price_level=2
            ),
        ]
        
        ranked = scorer.rank_activities(places)
        scores = [score for score, place in ranked]
        
        # Scores should be descending
        assert scores == sorted(scores, reverse=True), \
               f"Scores not in descending order: {scores}"
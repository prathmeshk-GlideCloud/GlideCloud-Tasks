"""
Unit tests for RAG service
"""
import pytest
from app.services.rag_service import IntelligentRAGService
from app.models.user_input import BudgetRange, PacePreference


@pytest.fixture
def rag_service():
    """Create RAG service instance"""
    return IntelligentRAGService()


def test_get_tips_for_activity_type(rag_service):
    """Test getting tips for activity type"""
    # ✅ FIXED: Returns different format now
    tips = rag_service.get_tips_for_activity_type("museum", n_results=3)
    
    assert len(tips) > 0
    assert isinstance(tips, list)
    assert 'text' in tips[0]  # Legacy format has 'text' key


def test_get_intelligent_tips(rag_service):
    """✅ NEW TEST: Test intelligent tips generation"""
    result = rag_service.get_intelligent_tips(
        place_name="Shaniwar Wada",
        category="historical",
        visit_time="09:00",
        duration_hours=1.5,
        city="Pune",
        budget_range="mid-range",
        pace="moderate"
    )
    
    assert 'tips' in result
    assert 'confidence' in result
    assert 'place_name' in result
    assert len(result['tips']) > 0


def test_place_specific_knowledge(rag_service):
    """✅ NEW TEST: Test place-specific knowledge"""
    # Test known place
    result = rag_service.get_intelligent_tips(
        place_name="Shaniwar Wada",
        category="landmark",
        visit_time="09:00",
        duration_hours=1.5
    )
    
    # Should have high confidence for known places
    assert result['confidence'] == 'high'
    assert result['tip_type'] == 'place_specific'


def test_category_based_tips(rag_service):
    """✅ NEW TEST: Test category-based tips fallback"""
    # Test unknown place
    result = rag_service.get_intelligent_tips(
        place_name="Unknown Museum",
        category="museum",
        visit_time="09:00",
        duration_hours=1.5
    )
    
    # Should fall back to category tips
    assert result['tip_type'] == 'category_based'
    assert len(result['tips']) > 0


def test_enrich_activity(rag_service):
    """Test activity enrichment"""
    # ✅ FIXED: New method returns different format
    enrichment = rag_service.enrich_activity_with_tips(
        activity_name="Test Museum",
        activity_type="museum",
        category="museum",
        visit_time="09:00",
        duration_hours=1.5
    )
    
    # New format has 'tips' instead of 'general_tip'
    assert 'tips' in enrichment
    assert 'confidence' in enrichment
    assert isinstance(enrichment['tips'], list)


def test_get_collection_stats(rag_service):
    """Test getting collection statistics"""
    stats = rag_service.get_collection_stats()
    
    assert stats is not None
    # ✅ FIXED: Changed from 'total_documents' to 'total_places'
    assert 'total_places' in stats
    assert 'type' in stats
    assert stats['type'] == 'intelligent_context_aware'


def test_add_place_knowledge(rag_service):
    """✅ NEW TEST: Test adding place knowledge"""
    place_data = {
        'name': 'Test Place',
        'best_time': 'Morning',
        'tips': ['Tip 1', 'Tip 2']
    }
    
    success = rag_service.add_place_knowledge(place_data)
    assert success is True


def test_normalize_place_name(rag_service):
    """✅ NEW TEST: Test place name normalization"""
    # Test normalization
    normalized1 = rag_service._normalize_place_name("Shaniwar Wada")
    normalized2 = rag_service._normalize_place_name("shaniwarwada")
    
    # Both should normalize to same key
    assert normalized1 == normalized2 == 'shaniwar_wada'


def test_context_aware_timing(rag_service):
    """✅ NEW TEST: Test time-aware tips"""
    # Morning visit
    morning_tips = rag_service.get_intelligent_tips(
        place_name="Test Museum",
        category="museum",
        visit_time="09:00",
        duration_hours=1.5
    )
    
    # Evening visit
    evening_tips = rag_service.get_intelligent_tips(
        place_name="Test Museum",
        category="museum",
        visit_time="18:00",
        duration_hours=1.5
    )
    
    # Tips should exist for both
    assert len(morning_tips['tips']) > 0
    assert len(evening_tips['tips']) > 0


def test_budget_aware_tips(rag_service):
    """✅ NEW TEST: Test budget-aware tips"""
    # Budget traveler
    budget_tips = rag_service.get_intelligent_tips(
        place_name="Test Restaurant",
        category="restaurant",
        visit_time="12:00",
        duration_hours=1.0,
        budget_range="budget"
    )
    
    # Luxury traveler
    luxury_tips = rag_service.get_intelligent_tips(
        place_name="Test Restaurant",
        category="restaurant",
        visit_time="12:00",
        duration_hours=1.0,
        budget_range="luxury"
    )
    
    # Both should have tips
    assert len(budget_tips['tips']) > 0
    assert len(luxury_tips['tips']) > 0


def test_pace_aware_tips(rag_service):
    """✅ NEW TEST: Test pace-aware tips"""
    # Relaxed pace
    relaxed_tips = rag_service.get_intelligent_tips(
        place_name="Test Park",
        category="park",
        visit_time="10:00",
        duration_hours=1.0,
        pace="relaxed"
    )
    
    # Packed pace
    packed_tips = rag_service.get_intelligent_tips(
        place_name="Test Park",
        category="park",
        visit_time="10:00",
        duration_hours=1.0,
        pace="packed"
    )
    
    # Both should have tips
    assert len(relaxed_tips['tips']) > 0
    assert len(packed_tips['tips']) > 0
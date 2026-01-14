"""
Unit tests for universal RAG service
"""
import pytest
from app.services.rag_service import RAGService
from app.models.user_input import BudgetRange, PacePreference


@pytest.fixture
def rag_service():
    """RAG service fixture"""
    return RAGService()


def test_get_tips_for_activity_type(rag_service):
    """Test getting tips for activity type"""
    tips = rag_service.get_tips_for_activity_type("museum", n_results=2)
    
    assert isinstance(tips, list)
    # Tips might be empty if DB not populated, which is okay for testing
    if tips:
        assert 'text' in tips[0]
        assert 'metadata' in tips[0]


def test_get_budget_wisdom(rag_service):
    """Test budget wisdom retrieval"""
    wisdom = rag_service.get_budget_wisdom(BudgetRange.MEDIUM)
    
    # May be empty if DB not populated
    assert isinstance(wisdom, dict)


def test_get_pace_guidance(rag_service):
    """Test pace guidance retrieval"""
    guidance = rag_service.get_pace_guidance(PacePreference.MODERATE)
    
    assert isinstance(guidance, dict)


def test_enrich_activity(rag_service):
    """Test activity enrichment"""
    enrichment = rag_service.enrich_activity_with_tips(
        activity_name="Test Museum",
        activity_type="museum",
        category="culture"
    )
    
    assert isinstance(enrichment, dict)
    assert 'general_tip' in enrichment
    assert 'timing_tip' in enrichment


def test_answer_question(rag_service):
    """Test question answering"""
    result = rag_service.answer_question(
        question="What's the best time to visit museums?"
    )
    
    assert 'question' in result
    assert 'answer' in result
    assert 'confidence' in result
    assert isinstance(result['confidence'], float)


def test_get_collection_stats(rag_service):
    """Test stats retrieval"""
    stats = rag_service.get_collection_stats()
    
    assert 'total_documents' in stats
    assert 'collection_name' in stats
    assert stats['type'] == 'universal_travel_wisdom'
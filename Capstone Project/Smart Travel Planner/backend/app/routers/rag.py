"""
RAG (Universal Travel Wisdom) API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from app.services.rag_service import RAGService
from app.models.user_input import BudgetRange, PacePreference

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize RAG service
rag_service = RAGService()


class QuestionRequest(BaseModel):
    """Question request model"""
    question: str = Field(..., min_length=3, description="User question")
    n_results: int = Field(3, ge=1, le=10, description="Number of results")


class AnswerResponse(BaseModel):
    """Answer response model"""
    question: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]


class TipsRequest(BaseModel):
    """Request for activity-specific tips"""
    activity_type: str = Field(..., description="Type of activity")
    n_results: int = Field(3, ge=1, le=5)


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a general travel question
    
    Returns intelligent answer based on universal travel wisdom
    """
    try:
        result = rag_service.answer_question(
            question=request.question,
            n_results=request.n_results
        )
        
        return AnswerResponse(**result)
    
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tips/activity")
async def get_activity_tips(request: TipsRequest):
    """
    Get tips for a specific activity type
    """
    try:
        tips = rag_service.get_tips_for_activity_type(
            activity_type=request.activity_type,
            n_results=request.n_results
        )
        
        return {
            "activity_type": request.activity_type,
            "tips": tips,
            "count": len(tips)
        }
    
    except Exception as e:
        logger.error(f"Error getting activity tips: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wisdom/budget/{budget_range}")
async def get_budget_wisdom(budget_range: BudgetRange):
    """
    Get budget-specific travel wisdom
    """
    try:
        wisdom = rag_service.get_budget_wisdom(budget_range)
        
        if wisdom:
            return wisdom
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No wisdom found for budget range: {budget_range}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting budget wisdom: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wisdom/pace/{pace}")
async def get_pace_guidance(pace: PacePreference):
    """
    Get guidance for trip pacing
    """
    try:
        guidance = rag_service.get_pace_guidance(pace)
        
        if guidance:
            return guidance
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No guidance found for pace: {pace}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pace guidance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tips/general")
async def get_general_tips(
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    n_results: int = Query(5, ge=1, le=10)
):
    """
    Get general travel tips
    
    Query params:
    - categories: Optional comma-separated list (e.g., "timing,budget,safety")
    - n_results: Number of tips to return
    """
    try:
        category_list = categories.split(',') if categories else None
        
        tips = rag_service.get_general_tips(
            categories=category_list,
            n_results=n_results
        )
        
        return {
            "tips": tips,
            "count": len(tips),
            "categories": category_list
        }
    
    except Exception as e:
        logger.error(f"Error getting general tips: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enrich/activity")
async def enrich_activity(
    activity_name: str = Query(..., description="Activity name"),
    activity_type: str = Query(..., description="Activity type"),
    category: str = Query(..., description="General category")
):
    """
    Get enrichment tips for a specific activity
    """
    try:
        enrichment = rag_service.enrich_activity_with_tips(
            activity_name=activity_name,
            activity_type=activity_type,
            category=category
        )
        
        return {
            "activity_name": activity_name,
            "enrichment": enrichment
        }
    
    except Exception as e:
        logger.error(f"Error enriching activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_rag_stats():
    """
    Get RAG knowledge base statistics
    """
    try:
        stats = rag_service.get_collection_stats()
        return stats
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
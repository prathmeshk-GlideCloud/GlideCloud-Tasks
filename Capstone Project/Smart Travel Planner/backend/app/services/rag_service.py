"""
RAG Service - Using ChromaDB default embeddings (no external API needed)
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import json
import logging
from pathlib import Path

from app.config import settings
from app.models.user_input import BudgetRange, PacePreference

logger = logging.getLogger(__name__)


class RAGService:
    """
    Universal RAG service using ChromaDB's built-in embeddings
    No external API or model downloads required
    """
    
    def __init__(self):
        """Initialize RAG service"""
        # Setup ChromaDB
        db_path = Path(settings.CHROMADB_PATH)
        db_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(db_path))
        
        # Use ChromaDB's default embedding function (no API key needed!)
        logger.info("Using ChromaDB built-in embedding function")
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="universal_travel_wisdom",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info("RAG service initialized successfully")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Add documents to the knowledge base
        ChromaDB automatically generates embeddings
        """
        if not documents:
            return 0
        
        texts = []
        metadatas = []
        ids = []
        
        for i, doc in enumerate(documents):
            if 'text' not in doc:
                logger.warning(f"Document {i} missing 'text' field, skipping")
                continue
            
            texts.append(doc['text'])
            metadatas.append(doc.get('metadata', {}))
            ids.append(doc.get('id', f"doc_{i}_{hash(doc['text'])}"))
        
        if not texts:
            return 0
        
        # Add to collection - ChromaDB auto-generates embeddings
        logger.info(f"Adding {len(texts)} documents (generating embeddings automatically)...")
        
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(texts)} documents to knowledge base")
        return len(texts)
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Query the knowledge base"""
        
        # Query collection - ChromaDB handles embeddings automatically
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if 'distances' in results else None,
                    'relevance_score': 1 - results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
    
    def get_tips_for_activity_type(
        self,
        activity_type: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Get relevant tips for a specific activity type"""
        query = f"best practices and tips for visiting {activity_type}"
        
        # Try with filter first
        try:
            results = self.query(
                query_text=query,
                n_results=n_results,
                where={"applicable_to": activity_type}
            )
            if results:
                return results
        except:
            pass
        
        # Fallback to query without filter
        return self.query(query_text=query, n_results=n_results)
    
    def get_budget_wisdom(self, budget_range: BudgetRange) -> Dict[str, Any]:
        """Get budget-specific wisdom"""
        query = f"budget tips and advice for {budget_range.value} budget travelers"
        
        try:
            results = self.query(
                query_text=query,
                n_results=3,
                where={"constraint_type": "budget"}
            )
        except:
            results = self.query(query_text=query, n_results=3)
        
        if results:
            return {
                'wisdom': results[0]['text'],
                'metadata': results[0]['metadata'],
                'additional_tips': [r['text'] for r in results[1:]]
            }
        
        return {}
    
    def get_timing_tips(self, activity_type: str) -> List[str]:
        """Get timing-related tips for activity type"""
        try:
            results = self.query(
                query_text=f"best time to visit {activity_type}",
                n_results=3,
                where={"category": "timing"}
            )
        except:
            results = self.query(
                query_text=f"best time to visit {activity_type}",
                n_results=3
            )
        
        return [r['text'] for r in results]
    
    def get_general_tips(
        self,
        categories: List[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Get general travel tips"""
        if categories:
            all_tips = []
            for category in categories:
                try:
                    results = self.query(
                        query_text=f"travel tips for {category}",
                        n_results=2,
                        where={"category": category}
                    )
                except:
                    results = self.query(
                        query_text=f"travel tips for {category}",
                        n_results=2
                    )
                all_tips.extend(results)
            return all_tips[:n_results]
        else:
            query = "essential travel tips and best practices"
            return self.query(query_text=query, n_results=n_results)
    
    def get_pace_guidance(self, pace: PacePreference) -> Dict[str, Any]:
        """Get guidance for trip pace"""
        try:
            results = self.query(
                query_text=f"travel planning for {pace.value} pace",
                n_results=1,
                where={"pace_type": pace.value}
            )
        except:
            results = self.query(
                query_text=f"travel planning for {pace.value} pace",
                n_results=1
            )
        
        if results:
            return {
                'guidance': results[0]['text'],
                'metadata': results[0]['metadata']
            }
        
        return {}
    
    def enrich_activity_with_tips(
        self,
        activity_name: str,
        activity_type: str,
        category: str
    ) -> Dict[str, Any]:
        """Get relevant tips to enrich an activity"""
        
        # Normalize activity type
        type_mapping = {
            'museum': 'museum',
            'art_gallery': 'museum',
            'tourist_attraction': 'landmark',
            'point_of_interest': 'landmark',
            'restaurant': 'restaurant',
            'cafe': 'restaurant',
            'park': 'park',
            'church': 'religious_site',
            'place_of_worship': 'religious_site',
            'shopping_mall': 'shopping',      # ✅ Add this
            'store': 'shopping',              # ✅ Add this
            'market': 'market'
        }
        
        normalized_type = type_mapping.get(activity_type, category)
        
        if normalized_type == 'shopping':
            # Get shopping-specific tips, avoid food mentions
            tips = self.get_tips_for_activity_type('shopping_mall', n_results=2)
        elif normalized_type == 'restaurant':
            tips = self.get_tips_for_activity_type('restaurant', n_results=2)
        else:
            tips = self.get_tips_for_activity_type(normalized_type, n_results=2)
        
        timing_tips = self.get_timing_tips(normalized_type)
        
        enrichment = {
            'general_tip': tips[0]['text'] if tips else None,
            'timing_tip': timing_tips[0] if timing_tips else None,
            'best_practices': []
        }
        
        # Extract best practices from metadata if available
        if tips and 'best_practices' in tips[0].get('metadata', {}):
            enrichment['best_practices'] = tips[0]['metadata']['best_practices']
        
        return enrichment
    
    def answer_question(
        self,
        question: str,
        n_results: int = 3
    ) -> Dict[str, Any]:
        """Answer a general travel question"""
        
        # Retrieve relevant documents
        results = self.query(query_text=question, n_results=n_results)
        
        if not results:
            return {
                "question": question,
                "answer": "I don't have specific information about that. However, I recommend researching the destination's official tourism website or checking recent traveler reviews.",
                "confidence": 0.0,
                "sources": []
            }
        
        # Generate answer from top results
        answer = self._generate_answer(question, results)
        
        # Calculate confidence
        confidence = sum(r['relevance_score'] for r in results if r['relevance_score']) / len(results) if results else 0.0
        
        return {
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "sources": results[:2]
        }
    
    def _generate_answer(self, question: str, context_docs: List[Dict]) -> str:
        """Generate answer from retrieved context"""
        if not context_docs:
            return "I couldn't find relevant information to answer your question."
        
        question_lower = question.lower()
        
        # Combine top results
        tips = []
        for doc in context_docs[:3]:
            tips.append(doc['text'])
        
        # Build answer based on question type
        if any(word in question_lower for word in ['best time', 'when', 'timing']):
            answer = "**Timing Recommendations:**\n\n" + "\n\n".join(f"• {tip}" for tip in tips)
        
        elif any(word in question_lower for word in ['budget', 'cheap', 'save money', 'cost']):
            answer = "**Budget Tips:**\n\n" + "\n\n".join(f"• {tip}" for tip in tips)
        
        elif any(word in question_lower for word in ['how to', 'best way', 'should i']):
            answer = "**Best Practices:**\n\n" + "\n\n".join(f"• {tip}" for tip in tips)
        
        else:
            answer = "**Travel Wisdom:**\n\n" + "\n\n".join(f"• {tip}" for tip in tips)
        
        return answer
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            self.client.delete_collection(name="universal_travel_wisdom")
            self.collection = self.client.get_or_create_collection(
                name="universal_travel_wisdom",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection.name,
                "embedding_model": "ChromaDB Default",
                "type": "universal_travel_wisdom"
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
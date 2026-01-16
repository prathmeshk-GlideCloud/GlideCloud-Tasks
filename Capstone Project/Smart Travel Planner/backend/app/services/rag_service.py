"""
Enhanced RAG Service - Context-Aware Travel Tips
"""
import chromadb
from typing import List, Dict, Optional, Any
import logging
from pathlib import Path

from app.config import settings
from app.models.user_input import BudgetRange, PacePreference

logger = logging.getLogger(__name__)


class IntelligentRAGService:
    """Enhanced RAG service with context-aware tip generation"""
    
    def __init__(self):
        """Initialize RAG service"""
        db_path = Path(settings.CHROMADB_PATH)
        db_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self.client.get_or_create_collection(
            name="intelligent_travel_tips",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.place_knowledge = self._load_place_knowledge()
        logger.info("Intelligent RAG service initialized")
    
    def _load_place_knowledge(self) -> Dict[str, Dict]:
        """Load place-specific knowledge"""
        return {
            'shaniwar_wada': {
                'name': 'Shaniwar Wada',
                'best_time': 'Early morning (7-9 AM) to avoid crowds, or evening for light show',
                'duration_tip': 'Allow 1.5-2 hours for thorough exploration',
                'tips': [
                    'Light and sound show at 7 PM daily (₹25 per person)',
                    'Photography allowed but no flash inside historical sections',
                    'Wear comfortable walking shoes - lots of stairs and uneven surfaces',
                    'Entry fee: ₹5 for Indians, ₹300 for foreigners',
                    'Closed on Mondays',
                    'Best photo spots: Main entrance, fountain courtyard'
                ],
                'insider': [
                    'Visit the Hazari Karanje (fountain) early morning when light is perfect',
                    'Local guides available at entrance for ₹200-300',
                    'Combine with nearby Dagdusheth Temple (15 min walk)'
                ],
                'avoid': 'Weekends and public holidays get very crowded',
                'nearby': 'Dagdusheth Ganpati Temple, Tulsi Baug Market',
                'season_tips': {
                    'summer': 'Visit early morning before 10 AM - gets very hot',
                    'monsoon': 'Beautiful gardens but carry umbrella',
                    'winter': 'Perfect weather for exploring'
                }
            },
            'aga_khan_palace': {
                'name': 'Aga Khan Palace',
                'best_time': 'Morning (9-11 AM) for better lighting and fewer crowds',
                'duration_tip': 'Plan for 1-2 hours',
                'tips': [
                    'Major historical site related to Gandhi and freedom movement',
                    'Photography allowed in gardens, restricted inside museum',
                    'Entry fee: ₹25 for Indians, ₹300 for foreigners',
                    'Open 9 AM - 5:30 PM daily',
                    'Audio guides available for ₹50'
                ],
                'insider': [
                    'Visit the Gandhi memorial and Kasturba Gandhi Samadhi',
                    'Beautiful Italian-style gardens perfect for photography',
                    'Small cafe inside for refreshments'
                ],
                'avoid': 'Tuesday afternoons - maintenance work',
                'nearby': 'Koregaon Park, Osho Ashram',
                'season_tips': {
                    'monsoon': 'Gardens are lush and beautiful',
                    'winter': 'Best time to visit, pleasant weather'
                }
            },
            'dagdusheth_temple': {
                'name': 'Dagdusheth Halwai Ganpati Temple',
                'best_time': 'Early morning (6-8 AM) for peaceful darshan, avoid evenings (crowded)',
                'duration_tip': '30-45 minutes',
                'tips': [
                    'Remove shoes before entering (free locker facility)',
                    'Free darshan, donations voluntary',
                    'Dress modestly - cover shoulders and knees',
                    'No photography inside temple',
                    'Famous during Ganesh Chaturthi (August-September)'
                ],
                'insider': [
                    'Accept the prasad (blessed offering) - modak or ladoo',
                    'Visit the smaller temples in the complex',
                    'Extremely crowded on Tuesdays - Ganesh holy day'
                ],
                'avoid': 'Tuesday evenings and festival days if you want quick darshan',
                'nearby': 'Shaniwar Wada (10 min walk), Tulsi Baug market',
                'season_tips': {
                    'festival': 'Ganesh Chaturthi (Aug-Sep) - incredible decorations but 2-3 hour wait'
                }
            },
            'saras_baug': {
                'name': 'Saras Baug',
                'best_time': 'Early morning (6-8 AM) or evening (5-7 PM)',
                'duration_tip': '45 minutes to 1 hour',
                'tips': [
                    'Free entry to garden, small fee for temple',
                    'Popular jogging and walking spot',
                    'Boating available (₹50 per person)',
                    'Food stalls outside the garden',
                    'Well-maintained children play area'
                ],
                'insider': [
                    'Visit Talyatla Ganesh temple inside the garden',
                    'Best for morning walks or evening relaxation',
                    'Street food vendors outside serve excellent vada pav'
                ],
                'avoid': 'Midday heat in summer',
                'nearby': 'Parvati Hill, Sinhagad Road eateries'
            },
            'pataleshwar_caves': {
                'name': 'Pataleshwar Cave Temple',
                'best_time': 'Morning (8-11 AM) or late afternoon (4-6 PM)',
                'duration_tip': '30-45 minutes',
                'tips': [
                    'Ancient rock-cut cave temple from 8th century',
                    'Free entry',
                    'Remove shoes before entering',
                    'Cool interior even in summer',
                    'Photography allowed'
                ],
                'insider': [
                    'Notice the Nandi sculpture carved from single rock',
                    'Peaceful spot in middle of busy city',
                    'Located right in Shivajinagar - combine with shopping'
                ],
                'nearby': 'Shivajinagar market, JM Road shopping',
                'season_tips': {
                    'monsoon': 'Cave stays dry and cool'
                }
            },
            'sinhagad_fort': {
                'name': 'Sinhagad Fort',
                'best_time': 'Early morning (6-9 AM) for sunrise and cool weather',
                'duration_tip': '2-3 hours including trek',
                'tips': [
                    'Located 30 km from Pune - plan transport',
                    'Can trek up (1.5 hours) or drive/take shared jeep',
                    'Wear good trekking shoes',
                    'Carry water - limited shops at top',
                    'Entry fee: ₹25',
                    'Famous for kanda bhaji (onion fritters) and mastani'
                ],
                'insider': [
                    'Start trek at 6 AM to avoid heat',
                    'Try the famous "Sinhagad kanda bhaji" at top',
                    'Visit Tanaji memorial',
                    'Monsoon: Extremely beautiful but slippery - be careful'
                ],
                'avoid': 'Midday heat in summer, weekends get very crowded',
                'season_tips': {
                    'monsoon': 'Spectacular views but very slippery - trek carefully',
                    'winter': 'Perfect trekking weather',
                    'summer': 'Only go very early morning'
                }
            }
        }
    
    def get_intelligent_tips(
        self,
        place_name: str,
        category: str,
        visit_time: str,
        duration_hours: float,
        city: str = "Pune",
        budget_range: str = "mid-range",
        pace: str = "moderate",
        user_interests: List[str] = None
    ) -> Dict[str, Any]:
        """Generate intelligent, context-aware tips for a specific place"""
        normalized_name = self._normalize_place_name(place_name)
        
        if normalized_name in self.place_knowledge:
            return self._generate_specific_tips(
                normalized_name, visit_time, duration_hours, budget_range, pace
            )
        
        return self._generate_category_tips(
            place_name, category, visit_time, duration_hours, 
            city, budget_range, pace
        )
    
    def _normalize_place_name(self, name: str) -> str:
        """Normalize place name for lookup"""
        name_lower = name.lower()
        
        mapping = {
            'shaniwar wada': 'shaniwar_wada',
            'shaniwarwada': 'shaniwar_wada',
            'aga khan palace': 'aga_khan_palace',
            'agakhan palace': 'aga_khan_palace',
            'dagdusheth': 'dagdusheth_temple',
            'dagdusheth ganpati': 'dagdusheth_temple',
            'dagdusheth halwai': 'dagdusheth_temple',
            'saras baug': 'saras_baug',
            'sarasbaug': 'saras_baug',
            'pataleshwar': 'pataleshwar_caves',
            'pataleshwar cave': 'pataleshwar_caves',
            'sinhagad': 'sinhagad_fort',
            'sinhgad fort': 'sinhagad_fort',
        }
        
        for key, value in mapping.items():
            if key in name_lower:
                return value
        
        return name_lower.replace(' ', '_')
    
    def _generate_specific_tips(
        self,
        place_key: str,
        visit_time: str,
        duration_hours: float,
        budget_range: str,
        pace: str
    ) -> Dict[str, Any]:
        """Generate tips from specific place knowledge"""
        place_data = self.place_knowledge[place_key]
        time_category = self._categorize_time(visit_time)
        
        tips = []
        
        if 'best_time' in place_data:
            tips.append(f"⏰ {place_data['best_time']}")
        
        if 'tips' in place_data:
            tips.extend([f"• {tip}" for tip in place_data['tips'][:3]])
        
        if 'insider' in place_data:
            tips.extend([f"💎 {tip}" for tip in place_data['insider'][:2]])
        
        if 'avoid' in place_data and time_category in ['afternoon', 'weekend']:
            tips.append(f"⚠️ {place_data['avoid']}")
        
        if 'nearby' in place_data:
            tips.append(f"📍 Nearby: {place_data['nearby']}")
        
        if 'duration_tip' in place_data:
            tips.append(f"⌚ {place_data['duration_tip']}")
        
        return {
            'place_name': place_data['name'],
            'tips': tips,
            'tip_type': 'place_specific',
            'confidence': 'high',
            'source': 'curated_knowledge'
        }
    
    def _generate_category_tips(
        self,
        place_name: str,
        category: str,
        visit_time: str,
        duration_hours: float,
        city: str,
        budget_range: str,
        pace: str
    ) -> Dict[str, Any]:
        """Generate intelligent category-based tips"""
        time_category = self._categorize_time(visit_time)
        
        category_tips = {
            'museum': {
                'general': [
                    '• Arrive within first hour of opening for fewer crowds',
                    '• Photography rules vary - check at entrance',
                    '• Allow minimum 1.5-2 hours for proper exploration'
                ],
                'timing': {
                    'morning': '• Perfect timing - museums are less crowded in mornings',
                    'afternoon': '• Consider taking breaks - museum fatigue is real',
                    'evening': '• Check closing time - museums typically close by 5-6 PM'
                },
                'budget': {
                    'budget': '• Many museums offer student/senior discounts',
                    'luxury': '• Consider hiring a private guide for deeper insights'
                }
            },
            'temple': {
                'general': [
                    '• Remove shoes before entering (locker facilities usually free)',
                    '• Dress modestly - shoulders and knees covered',
                    '• No photography inside temple premises',
                    '• Accept prasad (blessed offering) if offered'
                ],
                'timing': {
                    'morning': '• Excellent choice - early morning darshan is peaceful',
                    'afternoon': '• Temples may be less crowded now',
                    'evening': '⚠️ Evening aarti times can be very crowded (usually 6-8 PM)'
                },
                'insider': [
                    '💎 Tuesday is considered auspicious for Ganesh temples - expect crowds',
                    '💎 Donate in the designated donation box if you wish'
                ]
            },
            'park': {
                'general': [
                    '• Best during early morning or late evening',
                    '• Carry water bottle and sunscreen',
                    '• Great for relaxation between activities'
                ],
                'timing': {
                    'morning': '• Perfect time for parks - cool and pleasant',
                    'afternoon': '⚠️ Can be very hot - seek shaded areas',
                    'evening': '• Lovely time for parks - evening breeze and sunset'
                },
                'pace': {
                    'relaxed': '• Perfect for your pace - enjoy the tranquility',
                    'packed': '• Quick visit recommended - 30-45 minutes'
                }
            },
            'historical': {
                'general': [
                    '• Wear comfortable walking shoes',
                    '• Carry water - historical sites often lack facilities',
                    '• Consider hiring a guide for historical context'
                ],
                'timing': {
                    'morning': '• Ideal timing - cooler weather for exploring',
                    'afternoon': '⚠️ Can be hot - carry hat/cap and water',
                    'evening': '• Check closing time - many close by 6 PM'
                }
            },
            'shopping': {
                'general': [
                    '• Bargaining is common in local markets',
                    '• Fixed prices in malls and branded stores',
                    '• Carry reusable bags'
                ],
                'timing': {
                    'morning': '• Shops may just be opening - some open by 11 AM',
                    'afternoon': '• Good time - shops are less crowded',
                    'evening': '• Peak shopping hours - expect crowds'
                },
                'budget': {
                    'budget': '• Local markets offer better prices than malls',
                    'luxury': '• Premium brands available in major malls'
                }
            },
            'landmark': {
                'general': [
                    '• Research viewpoints and photo spots beforehand',
                    '• Check if advance tickets are required',
                    '• Plan for crowds at popular landmarks'
                ],
                'timing': {
                    'morning': '• Excellent for photography - good natural light',
                    'afternoon': '• Harsh sunlight - photos may have strong shadows',
                    'evening': '• Great for golden hour photography'
                }
            },
            'restaurant': {
                'general': [
                    '• Book popular restaurants in advance',
                    '• Ask locals for authentic recommendations',
                    '• Try local specialties'
                ],
                'timing': {
                    'breakfast': f'• {visit_time} - Good timing for breakfast',
                    'lunch': f'• {visit_time} - Lunch hour, may be crowded',
                    'dinner': f'• {visit_time} - Dinner time, book ahead if popular'
                },
                'budget': {
                    'budget': '• Local eateries offer authentic food at better prices',
                    'luxury': '• Fine dining experience - dress code may apply'
                }
            }
        }
        
        tips = []
        cat_tips = category_tips.get(category, category_tips.get('landmark', {}))
        
        if 'general' in cat_tips:
            tips.extend(cat_tips['general'][:3])
        
        if 'timing' in cat_tips and time_category in cat_tips['timing']:
            tips.append(cat_tips['timing'][time_category])
        
        if 'budget' in cat_tips and budget_range in cat_tips['budget']:
            tips.append(f"💰 {cat_tips['budget'][budget_range]}")
        
        if 'pace' in cat_tips and pace in cat_tips['pace']:
            tips.append(cat_tips['pace'][pace])
        
        if 'insider' in cat_tips:
            tips.extend(cat_tips['insider'][:1])
        
        return {
            'place_name': place_name,
            'tips': tips[:5],
            'tip_type': 'category_based',
            'confidence': 'medium',
            'source': 'intelligent_generation'
        }
    
    def _categorize_time(self, visit_time: str) -> str:
        """Categorize time of day"""
        try:
            hour = int(visit_time.split(':')[0])
            if 5 <= hour < 12:
                return 'morning'
            elif 12 <= hour < 17:
                return 'afternoon'
            else:
                return 'evening'
        except:
            return 'morning'
    
    def add_place_knowledge(self, place_data: Dict[str, Any]) -> bool:
        """Add new place-specific knowledge"""
        try:
            place_key = self._normalize_place_name(place_data['name'])
            self.place_knowledge[place_key] = place_data
            logger.info(f"Added knowledge for {place_data['name']}")
            return True
        except Exception as e:
            logger.error(f"Error adding place knowledge: {e}")
            return False
    
    # Legacy methods for backward compatibility
    def get_tips_for_activity_type(self, activity_type: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Legacy method - returns generic tips"""
        tips = self._generate_category_tips(
            place_name="Generic " + activity_type,
            category=activity_type,
            visit_time="09:00",
            duration_hours=1.5,
            city="Unknown",
            budget_range="mid-range",
            pace="moderate"
        )
        return [{'text': tip} for tip in tips['tips']]
    
    def enrich_activity_with_tips(
        self,
        activity_name: str,
        activity_type: str,
        category: str,
        visit_time: str = "09:00",
        duration_hours: float = 1.5,
        city: str = "Pune",
        budget_range: str = "mid-range",
        pace: str = "moderate"
    ) -> Dict[str, Any]:
        """Enhanced enrichment with intelligent tips"""
        return self.get_intelligent_tips(
            place_name=activity_name,
            category=category,
            visit_time=visit_time,
            duration_hours=duration_hours,
            city=city,
            budget_range=budget_range,
            pace=pace
        )
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get stats"""
        return {
            "total_places": len(self.place_knowledge),
            "type": "intelligent_context_aware",
            "embedding_model": "ChromaDB Default",
            "places_covered": list(self.place_knowledge.keys())
        }


# Maintain backward compatibility
RAGService = IntelligentRAGService
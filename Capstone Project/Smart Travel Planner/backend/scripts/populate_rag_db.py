"""
Script to populate RAG knowledge base with universal travel wisdom
FIXED VERSION - No import issues
"""
import sys
import json
from pathlib import Path

# Add backend directory to path - WORKS FOR ALL CASES
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

# Now we can import
try:
    from app.services.rag_service import RAGService
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Using fallback standalone mode...")
    
    # Fallback to standalone ChromaDB
    import chromadb
    
    def populate_standalone():
        """Standalone population without app imports"""
        print("=" * 60)
        print("Populating RAG Database (Standalone Mode)")
        print("=" * 60)
        
        data_file = backend_dir.parent / "data" / "tourism_content" / "universal_travel_tips.json"
        db_path = backend_dir.parent / "data" / "chromadb"
        
        if not data_file.exists():
            print(f"\n✗ Error: Data file not found at {data_file}")
            return
        
        db_path.mkdir(parents=True, exist_ok=True)
        
        print("\n1. Initializing ChromaDB...")
        client = chromadb.PersistentClient(path=str(db_path))
        collection = client.get_or_create_collection(
            name="universal_travel_wisdom",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"   Current documents: {collection.count()}")
        
        print("\n2. Loading data...")
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"   Loaded {len(data.get('general_tips', []))} tips")
        
        print("\n3. Preparing documents...")
        documents = []
        metadatas = []
        ids = []
        
        for tip in data.get('general_tips', []):
            doc_text = f"{tip['tip']}\n\nReasoning: {tip['reasoning']}"
            documents.append(doc_text)
            metadatas.append({
                'category': tip['category'],
                'applicable_to': tip['applicable_to']
            })
            ids.append(tip['id'])
        
        for wisdom in data.get('constraint_wisdom', []):
            doc_text = f"Constraint: {wisdom['constraint_type']}\n\n{wisdom['wisdom']}"
            documents.append(doc_text)
            metadatas.append({'constraint_type': wisdom['constraint_type']})
            ids.append(wisdom['id'])
        
        for activity in data.get('activity_type_wisdom', []):
            doc_text = f"Activity: {activity['activity_type']}\n\n"
            doc_text += "\n".join(f"• {p}" for p in activity['best_practices'])
            documents.append(doc_text)
            metadatas.append({'activity_type': activity['activity_type']})
            ids.append(f"activity_{activity['activity_type']}")
        
        print(f"   Prepared {len(documents)} documents")
        
        if collection.count() > 0:
            response = input("\n   Clear existing data? (y/n): ")
            if response.lower() == 'y':
                client.delete_collection("universal_travel_wisdom")
                collection = client.get_or_create_collection(
                    name="universal_travel_wisdom",
                    metadata={"hnsw:space": "cosine"}
                )
        
        print("\n4. Adding to database...")
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"   ✓ Added {len(documents)} documents")
        
        print("\n5. Verifying...")
        print(f"   Total documents: {collection.count()}")
        
        # Test
        results = collection.query(query_texts=["museum tips"], n_results=1)
        print(f"\n6. Test query: {len(results['documents'][0])} results")
        
        print("\n" + "=" * 60)
        print("✓ Population Complete!")
        print("=" * 60)
    
    populate_standalone()
    sys.exit(0)


def load_universal_tips(file_path: str) -> dict:
    """Load universal travel tips from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def prepare_documents_from_tips(data: dict) -> list:
    """Convert universal tips into documents for RAG"""
    documents = []
    
    # Process general tips
    for tip in data.get('general_tips', []):
        doc_text = f"{tip['tip']}\n\n"
        doc_text += f"Reasoning: {tip['reasoning']}\n"
        doc_text += f"Applicable to: {tip['applicable_to']}\n"
        doc_text += f"Confidence: {tip['confidence']}"
        
        documents.append({
            'text': doc_text,
            'metadata': {
                'id': tip['id'],
                'category': tip['category'],
                'applicable_to': tip['applicable_to'],
                'confidence': tip['confidence'],
                'tags': ','.join(tip['tags'])
            },
            'id': tip['id']
        })
    
    # Process constraint wisdom
    for wisdom in data.get('constraint_wisdom', []):
        doc_text = f"Constraint Wisdom - {wisdom['constraint_type'].title()}\n\n"
        doc_text += wisdom['wisdom']
        
        if 'allocation_guide' in wisdom:
            doc_text += f"\n\nRecommended allocation: {json.dumps(wisdom['allocation_guide'])}"
        
        if 'typical_durations' in wisdom:
            doc_text += f"\n\nTypical durations: {json.dumps(wisdom['typical_durations'])}"
        
        metadata = {
            'id': wisdom['id'],
            'constraint_type': wisdom['constraint_type'],
            'type': 'constraint_wisdom'
        }
        
        if 'range' in wisdom:
            metadata['range'] = wisdom['range']
        if 'pace_type' in wisdom:
            metadata['pace_type'] = wisdom['pace_type']
        
        documents.append({
            'text': doc_text,
            'metadata': metadata,
            'id': wisdom['id']
        })
    
    # Process activity type wisdom
    for activity in data.get('activity_type_wisdom', []):
        doc_text = f"Best Practices for {activity['activity_type'].title()}\n\n"
        
        doc_text += "Best Practices:\n"
        doc_text += "\n".join(f"• {practice}" for practice in activity['best_practices'])
        
        doc_text += "\n\nCommon Mistakes to Avoid:\n"
        doc_text += "\n".join(f"• {mistake}" for mistake in activity['common_mistakes'])
        
        doc_text += f"\n\nTypical Duration: {activity['typical_duration']} hours"
        
        documents.append({
            'text': doc_text,
            'metadata': {
                'id': f"activity_wisdom_{activity['activity_type']}",
                'activity_type': activity['activity_type'],
                'applicable_to': activity['activity_type'],
                'typical_duration': activity['typical_duration'],
                'type': 'activity_wisdom',
                'best_practices': json.dumps(activity['best_practices'])
            },
            'id': f"activity_wisdom_{activity['activity_type']}"
        })
    
    return documents


def main():
    """Main function using app imports"""
    logger.info("=" * 60)
    logger.info("Populating Universal Travel Wisdom Database")
    logger.info("=" * 60)
    
    logger.info("\n1. Initializing RAG service...")
    rag = RAGService()
    
    stats = rag.get_collection_stats()
    logger.info(f"   Current documents in DB: {stats.get('total_documents', 0)}")
    
    if stats.get('total_documents', 0) > 0:
        response = input("\n   Existing data found. Clear and repopulate? (y/n): ")
        if response.lower() == 'y':
            logger.info("   Clearing existing data...")
            rag.clear_collection()
    
    logger.info("\n2. Loading universal travel wisdom...")
    data_file = backend_dir.parent / "data" / "tourism_content" / "universal_travel_tips.json"
    
    if not data_file.exists():
        logger.error(f"   Data file not found: {data_file}")
        logger.error("   Please create the file with universal travel tips")
        return
    
    data = load_universal_tips(str(data_file))
    logger.info(f"   Loaded:")
    logger.info(f"   - {len(data.get('general_tips', []))} general tips")
    logger.info(f"   - {len(data.get('constraint_wisdom', []))} constraint wisdom entries")
    logger.info(f"   - {len(data.get('activity_type_wisdom', []))} activity type guides")
    
    logger.info("\n3. Preparing documents...")
    documents = prepare_documents_from_tips(data)
    logger.info(f"   Prepared {len(documents)} documents")
    
    logger.info("\n4. Adding documents to RAG...")
    added = rag.add_documents(documents)
    logger.info(f"   Successfully added {added} documents")
    
    logger.info("\n5. Verifying...")
    final_stats = rag.get_collection_stats()
    logger.info(f"   Total documents in DB: {final_stats.get('total_documents', 0)}")
    
    logger.info("\n6. Testing with sample queries...")
    test_queries = [
        "What's the best time to visit museums?",
        "How can I save money on food while traveling?"
    ]
    
    for query in test_queries:
        result = rag.answer_question(query, n_results=2)
        logger.info(f"\n   Q: {query}")
        logger.info(f"   Confidence: {result['confidence']:.2f}")
        logger.info(f"   A: {result['answer'][:100]}...")
    
    logger.info("\n" + "=" * 60)
    logger.info("Universal Travel Wisdom Database populated successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
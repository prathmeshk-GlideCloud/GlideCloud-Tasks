"""
Test configuration import
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("=" * 60)
print("Testing Configuration Import")
print("=" * 60)

print("\n1. Testing basic import...")
try:
    import app.config
    print("   ✓ app.config module found")
except ModuleNotFoundError as e:
    print(f"   ✗ Failed: {e}")
    print("\n   Checking if app/__init__.py exists...")
    init_file = backend_dir / "app" / "__init__.py"
    print(f"   {init_file}: {init_file.exists()}")
    sys.exit(1)

print("\n2. Testing settings import...")
try:
    from app.config import settings
    print("   ✓ Settings imported successfully")
    print(f"   App Name: {settings.APP_NAME}")
    print(f"   ChromaDB Path: {settings.CHROMADB_PATH}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

print("\n3. Testing RAG service import...")
try:
    from app.services.rag_service import RAGService
    print("   ✓ RAG Service imported successfully")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Testing RAG initialization...")
try:
    rag = RAGService()
    stats = rag.get_collection_stats()
    print("   ✓ RAG Service initialized")
    print(f"   Documents: {stats.get('total_documents', 0)}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All tests passed!")
print("=" * 60)
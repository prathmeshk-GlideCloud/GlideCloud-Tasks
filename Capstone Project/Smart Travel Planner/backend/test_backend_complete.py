"""
Test complete backend flow - INDIAN BUDGET
"""
from datetime import date, timedelta
import requests
import json

API_URL = "http://localhost:8000"

print("=" * 60)
print("Testing Complete Backend - Indian Budget System")
print("=" * 60)

# Test itinerary generation
print("\n🧪 Testing itinerary generation...")
print("   This may take 30-60 seconds...")

itinerary_request = {
    "preferences": {
        "destination": "Jaipur, India",
        "start_date": str(date.today() + timedelta(days=7)),
        "end_date": str(date.today() + timedelta(days=10)),  # 4 days
        "budget_range": "medium",  # ₹30K-60K
        "interests": ["culture", "history", "food"],
        "must_visit": ["Hawa Mahal", "Amber Fort"],
        "dietary_restrictions": [],
        "max_daily_distance": 40.0,
        "pace": "moderate"
    },
    "optimize_for": "time"
}

response = requests.post(
    f"{API_URL}/api/planner/generate",
    json=itinerary_request,
    timeout=120
)

print(f"   Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"   ✓ Status: {result['status']}")
    
    if result.get('summary'):
        summary = result['summary']
        print(f"   ✓ Total activities: {summary['total_activities']}")
        print(f"   ✓ Total cost: ₹{summary['total_cost']:,.2f}")
        print(f"   ✓ Budget used: {summary['budget_used_percentage']}%")
        print(f"   ✓ Budget remaining: ₹{summary['budget_remaining']:,.2f}")
    
    # Show operating hours
    if result.get('itinerary') and 'day_1' in result['itinerary']:
        day1 = result['itinerary']['day_1']
        summary = day1.get('summary', {})
        print(f"\n   📅 Day 1 schedule:")
        print(f"      Start: {summary.get('start_time', 'N/A')}")
        print(f"      End: {summary.get('end_time', 'N/A')}")
        print(f"      Activities: {len(day1.get('activities', []))}")
    
    # Save
    with open('test_itinerary_indian.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\n   ✓ Full itinerary saved to: test_itinerary_indian.json")
else:
    print(f"   ✗ Error: {response.text}")

print("\n" + "=" * 60)
print("✅ Testing complete!")
print("=" * 60)
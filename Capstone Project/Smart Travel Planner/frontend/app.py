import streamlit as st
from datetime import date, timedelta
import json
from utils.api_client import APIClient
from utils.city_autocomplete import search_cities_wrapper
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Smart Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

api = APIClient()

# Enhanced CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .activity-item {
        background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .activity-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    .activity-time {
        font-size: 1.05rem;
        font-weight: 600;
        color: #667eea;
        margin-bottom: 0.5rem;
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background-color: #f0f3ff;
        border-radius: 20px;
    }
    .activity-name {
        font-size: 1.4rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.7rem;
        line-height: 1.4;
    }
    .activity-address {
        color: #7f8c8d;
        font-size: 0.95rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .activity-tips {
        background-color: #f8f9ff;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 3px solid #667eea;
    }
    .activity-tips-title {
        color: #667eea;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .activity-tips-content {
        color: #555;
        line-height: 1.7;
        font-size: 0.9rem;
    }
    .activity-footer {
        display: flex;
        gap: 2rem;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #e0e0e0;
        font-size: 0.95rem;
    }
    .activity-footer-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #555;
    }
    .day-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    .day-header h2 {
        margin: 0;
        font-size: 1.8rem;
    }
    .day-header p {
        margin: 0.7rem 0 0 0;
        opacity: 0.95;
        font-size: 1.05rem;
    }
    .day-summary {
        background: linear-gradient(135deg, #e8f4f8 0%, #f0f7ff 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-top: 2rem;
        border: 2px solid #667eea;
    }
    .day-summary-title {
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.7rem;
        font-size: 1.1rem;
    }
    .day-summary-content {
        color: #2c3e50;
        line-height: 1.8;
    }
    .budget-breakdown {
        background: linear-gradient(135deg, #f0f7ff 0%, #fff 100%);
        padding: 2rem;
        border-radius: 12px;
        border: 2px solid #667eea;
        margin: 1.5rem 0;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
    .budget-breakdown h3 {
        margin-top: 0;
        color: #667eea;
        font-size: 1.5rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        text-align: center;
    }
    .meal-badge {
        display: inline-block;
        background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    .rating-stars {
        color: #f39c12;
        font-size: 1.1rem;
    }
    .cost-badge {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .cost-range {
        color: #666;
        font-size: 0.85rem;
        margin-left: 0.3rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1.5rem;
        background-color: #f5f7fa;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">✈️ Smart Travel Planner</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-Powered Personalized Itineraries with Smart Constraint Planning</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🎯 Trip Preferences")
    
    # Destination
    st.subheader("📍 Destination")
    try:
        from streamlit_searchbox import st_searchbox
        destination = st_searchbox(
            search_cities_wrapper,
            placeholder="Search cities...",
            key="destination_searchbox",
            clear_on_submit=False
        )
        if not os.getenv("GOOGLE_MAPS_API_KEY"):
            st.caption("⚠️ Set GOOGLE_MAPS_API_KEY for autocomplete")
    except:
        destination = st.text_input("Destination", placeholder="e.g., Pune, India", key="dest_fallback")
    
    # Dates
    st.subheader("📅 Travel Dates")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start", value=date.today() + timedelta(days=7), min_value=date.today(), key="start")
    with col2:
        end_date = st.date_input("End", value=date.today() + timedelta(days=11), min_value=start_date, key="end")
    
    num_days = (end_date - start_date).days + 1
    st.info(f"📆 **{num_days} days**")
    
    # Budget
    st.subheader("💰 Budget (Total Trip)")
    
    budget_mode = st.radio(
        "Budget selection",
        ["Quick Select", "Custom Amount"],
        key="budget_mode",
        horizontal=True
    )
    
    if budget_mode == "Quick Select":
        budget_range = st.selectbox(
            "Choose range",
            ["low", "medium", "high"],
            index=1,
            format_func=lambda x: {
                "low": "💵 Budget",
                "medium": "💳 Comfortable",
                "high": "💎 Premium"
            }[x],
            key="budget_range"
        )
        
        budget_per_day = {"low": 2500, "medium": 6000, "high": 12000}
        total_budget = budget_per_day[budget_range] * num_days
        custom_budget = None
                
    else:  # Custom Amount
        custom_budget = st.number_input(
            "Enter total budget (₹)",
            min_value=5000,
            max_value=500000,
            value=num_days * 6000,
            step=5000,
            key="custom_budget"
        )

        per_day = custom_budget / num_days

        if per_day < 3500:
            budget_range = "low"
            category = "💵 Budget"
        elif per_day < 8000:
            budget_range = "medium"
            category = "💳 Comfortable"
        else:
            budget_range = "high"
            category = "💎 Premium"

        total_budget = custom_budget
        st.info(f"**Category:** {category}")
        
    # Show breakdown
    with st.expander("📊 Budget Breakdown"):
        if budget_range == "low":
            alloc = {"accommodation": 24, "food": 28, "activities": 36, "transport": 12}
        elif budget_range == "medium":
            alloc = {"accommodation": 33, "food": 25, "activities": 30, "transport": 12}
        else:
            alloc = {"accommodation": 38, "food": 25, "activities": 27, "transport": 10}
        
        st.write(f"**Total**: ₹{total_budget:,} for {num_days} days")
        st.write(f"**Per Day**: ₹{total_budget/num_days:,.0f}")
        st.markdown("---")
        
        for cat, pct in alloc.items():
            amt = (total_budget * pct) / 100
            daily_amt = amt / num_days
            emoji = {"accommodation": "🏨", "food": "🍽️", "activities": "🎯", "transport": "🚗"}[cat]
            st.write(f"{emoji} **{cat.title()}**: ₹{amt:,.0f} ({pct}%)")
            st.caption(f"   ₹{daily_amt:,.0f}/day")
    
    # Interests
    st.subheader("🎨 Interests")
    interests = st.multiselect(
        "Select interests",
        ["culture", "food", "adventure", "nature", "shopping", "history", "nightlife", "relaxation"],
        default=["culture", "history", "food"],
        key="interests"
    )
    
    # Must-visit
    st.subheader("⭐ Must-Visit")
    must_visit_input = st.text_area(
        "Places (one per line)",
        placeholder="e.g., Shaniwar Wada\nAga Khan Palace",
        height=80,
        key="must_visit"
    )
    must_visit = [p.strip() for p in must_visit_input.split('\n') if p.strip()]
    
    # Pace
    st.subheader("⚡ Pace")
    pace = st.radio(
        "Daily pace",
        ["relaxed", "moderate", "packed"],
        index=1,
        format_func=lambda x: {
            "relaxed": "🧘 Relaxed (4 activities)",
            "moderate": "🚶 Moderate (5 activities)",
            "packed": "🏃 Packed (6 activities)"
        }[x],
        key="pace"
    )
    
    # Advanced
    with st.expander("🔧 Advanced Settings"):
        max_distance = st.slider("Max daily distance (km)", 10, 100, 40, 10, key="distance")
        optimize_for = st.selectbox("Optimize for", ["balanced", "time", "cost"], 0, format_func=str.capitalize, key="optimize")
    
    st.markdown("---")
    generate_btn = st.button("🚀 Generate Itinerary", type="primary", use_container_width=True)

# Generate
if generate_btn:
    if not destination:
        st.error("❌ Please enter a destination")
    elif not interests:
        st.error("❌ Please select at least one interest")
    else:
        preferences = {
            "destination": destination,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "interests": interests,
            "must_visit": must_visit,
            "dietary_restrictions": [],
            "max_daily_distance": float(max_distance),
            "pace": pace
        }
        
        # Add budget
        if budget_mode == "Quick Select":
            preferences["budget_range"] = budget_range
            preferences["custom_budget"] = None
        else:
            preferences["budget_range"] = None
            preferences["custom_budget"] = float(custom_budget)
        
        with st.spinner("🌍 Planning your perfect trip... This may take 30-60 seconds"):
            result = api.generate_itinerary(preferences, optimize_for)
        
        # Store in session state
        st.session_state['itinerary'] = result
        st.session_state['preferences'] = preferences
        st.session_state['saved_budget_mode'] = budget_mode
        st.session_state['saved_total_budget'] = total_budget
        st.session_state['saved_budget_range'] = budget_range
        st.session_state['saved_num_days'] = num_days

# Display
if 'itinerary' in st.session_state:
    result = st.session_state['itinerary']
    
    if result.get('status') == 'error':
        st.error(f"❌ {result.get('message')}")
    else:
        st.success("✅ Your personalized itinerary is ready!")
        
        # Summary metrics
        if result.get('summary'):
            summary = result['summary']
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🎯 Activities", summary.get('total_activities', 0))
            with col2:
                st.metric("💰 Total Cost", f"₹{summary.get('total_cost', 0):,.0f}")
            with col3:
                st.metric("📊 Budget Used", f"{summary.get('budget_used_percentage', 0)}%")
            with col4:
                st.metric("💵 Remaining", f"₹{summary.get('budget_remaining', 0):,.0f}")
        
        # Itinerary
        st.markdown("---")
        st.header("📅 Your Day-by-Day Itinerary")
        
        itinerary = result.get('itinerary', {})
        num_days_display = st.session_state.get('saved_num_days', len(itinerary))
        day_tabs = st.tabs([f"Day {i}" for i in range(1, num_days_display + 1)])
        
        for idx, tab in enumerate(day_tabs, 1):
            day_key = f"day_{idx}"
            
            with tab:
                if day_key in itinerary:
                    day_data = itinerary[day_key]
                    activities = day_data.get('activities', [])
                    day_summary = day_data.get('summary', {})
                    
                    # Day header
                    # Count activities separately from meals
                    activity_count = len([a for a in activities if a.get('category') != 'restaurant'])
                    meal_count = len([a for a in activities if a.get('category') == 'restaurant'])

                    # Day header
                    st.markdown(f"""
                    <div class="day-header">
                        <h2>Day {idx} - {day_data.get('date')}</h2>
                        <p>
                            {activity_count} activities + {meal_count} meals • ₹{day_summary.get('total_cost', 0):,.0f} • 
                            {day_summary.get('start_time', '')} - {day_summary.get('end_time', '')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Activities
                for activity in activities:
                    # Get insights
                    insights = activity.get('rag_insights', {})
                    general_tip = insights.get('general_tip', '')
                    
                    # Clean tips
                    clean_tips = []
                    if general_tip:
                        general_tip = general_tip.replace('**', '').replace('*', '')
                        lines = [l.strip().lstrip('•-–—*').strip() for l in general_tip.split('\n')]
                        
                        for line in lines:
                            skip = ['best practices', 'common mistakes', 'duration:', 'for restaurant', 'for museum']
                            if len(line) > 15 and line[0].isupper() and not any(s in line.lower() for s in skip):
                                clean_tips.append(line)
                    
                    if not clean_tips:
                        clean_tips = ['Perfect spot to experience local culture and atmosphere']
                    clean_tips = clean_tips[:3]
                    
                    # Meal badge
                    meal_badge = ""
                    if activity.get('category') == 'restaurant':
                        hour = int(activity['start_time'].split(':')[0])
                        if hour < 11:
                            meal_badge = ' <span class="meal-badge">🍳 Breakfast</span>'
                        elif hour < 17:
                            meal_badge = ' <span class="meal-badge">🍽️ Lunch</span>'
                        else:
                            meal_badge = ' <span class="meal-badge">🌙 Dinner</span>'
                    
                    # Category
                    categories = {
                        'restaurant': 'Dining', 'museum': 'Museum', 'park': 'Nature & Parks',
                        'historical': 'Historical Site', 'religious_site': 'Cultural Site',
                        'shopping': 'Shopping', 'landmark': 'Landmark'
                    }
                    category_title = categories.get(activity.get('category'), 'Attraction')
                    
                    # Cost
                    cost = activity.get('cost', 0)
                    cost_display = '<span class="cost-badge">Free Entry</span>' if cost == 0 else f'<span class="cost-badge">₹{cost:,.0f}</span>'
                    
                    # Rating
                    rating = activity.get('rating', 0)
                    if rating:
                        stars = '⭐' * int(rating)
                        rating_display = f'<span class="rating-stars">{stars}</span> {rating:.1f}'
                    else:
                        rating_display = 'Not rated'
                    
                    # Travel
                    travel_mins = int(activity.get('travel_from_previous', {}).get('duration_minutes', 0))
                    travel_display = 'Starting point' if travel_mins == 0 else f'{travel_mins} min travel'
                    
                    # Tips HTML
                    tips_html = '<br>'.join([f'• {tip}' for tip in clean_tips])
                    
                    # Display card
                    st.markdown(f"""
                    <div class="activity-item">
                        <div class="activity-time">
                            🕐 {activity['start_time']} - {activity['end_time']} ({activity.get('duration_hours', 0):.1f}h)
                        </div>
                        <div class="activity-name">
                            {activity['activity_name']}{meal_badge}
                        </div>
                        <div class="activity-address">
                            <span>📍</span>
                            <span>{activity.get('address', 'Address not available')}</span>
                        </div>
                        <div class="activity-tips">
                            <div class="activity-tips-title">
                                <span>💡</span>
                                <span>Insider Tips for {category_title}</span>
                            </div>
                            <div class="activity-tips-content">
                                {tips_html}
                            </div>
                        </div>
                        <div class="activity-footer">
                            <div class="activity-footer-item">
                                <span>💵</span>
                                <span>{cost_display}</span>
                            </div>
                            <div class="activity-footer-item">
                                <span>{rating_display}</span>
                            </div>
                            <div class="activity-footer-item">
                                <span>🚶</span>
                                <span>{travel_display}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        
        # Download button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.download_button(
                "📥 Download Full Itinerary (JSON)",
                json.dumps(result, indent=2),
                f"itinerary_{destination.replace(' ', '_')}_{start_date}.json",
                "application/json",
                use_container_width=True
            )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; padding: 2rem 0;'>
    <p style='font-size: 0.9rem;'>
        <strong>Smart Travel Planner</strong> | Powered by AI & Constraint-Based Optimization
    </p>
    <p style='font-size: 0.8rem; margin-top: 0.5rem;'>
        Making travel planning intelligent, personalized, and effortless
    </p>
</div>
""", unsafe_allow_html=True)
"""
Smart Travel Planner - FINAL POLISHED VERSION
"""
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

# CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .activity-item {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #1E88E5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .activity-time {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .activity-name {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .day-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    .budget-breakdown {
        background-color: #f0f7ff;
        padding: 1.5rem;
        border-radius: 8px;
        border: 2px solid #1E88E5;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">✈️ Smart Travel Planner</p>', unsafe_allow_html=True)
st.markdown("**AI-Powered Travel Planning with Constraint Satisfaction**")

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
    
    # HYBRID BUDGET
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

        # Auto-detect category
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
            "relaxed": "🧘 Relaxed (3 activities)",
            "moderate": "🚶 Moderate (4 activities)",
            "packed": "🏃 Packed (5 activities)"
        }[x],
        key="pace"
    )
    
    # Advanced
    with st.expander("🔧 Advanced"):
        max_distance = st.slider("Max daily distance (km)", 10, 100, 40, 10, key="distance")
        optimize_for = st.selectbox("Optimize for", ["time", "cost", "balanced"], 0, format_func=str.capitalize, key="optimize")
    
    st.markdown("---")
    generate_btn = st.button("🚀 Generate Itinerary", type="primary", use_container_width=True)

# Generate
if generate_btn:
    if not destination:
        st.error("❌ Enter destination")
    elif not interests:
        st.error("❌ Select interests")
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
        
        with st.spinner("🌍 Planning your perfect trip... (30-60 seconds)"):
            result = api.generate_itinerary(
                preferences,
                optimize_for,
                budget_mode.lower().replace(" ", "_"),
                custom_budget
            )
        
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
        st.success("✅ Itinerary generated!")
        
        # Budget Breakdown Box (Custom Budget Only)
        if st.session_state.get('saved_budget_mode') == "Custom Amount":
            total = st.session_state.get('saved_total_budget', 0)
            category = st.session_state.get('saved_budget_range', 'medium')
            num_days_saved = st.session_state.get('saved_num_days', 5)
            
            st.markdown(f"""
            <div class="budget-breakdown">
                <h3 style="margin-top: 0; color: #1E88E5;">📊 Your Budget Breakdown</h3>
                <p><strong>Total Budget:</strong> ₹{total:,} ✅</p>
                <p><strong>Duration:</strong> {num_days_saved} days</p>
                <p><strong>Category:</strong> {'💳 Comfortable' if category == 'medium' else ('💵 Budget' if category == 'low' else '💎 Premium')}</p>
                <hr style="margin: 1rem 0;">
                <p><strong>Daily Allocation:</strong></p>
            """, unsafe_allow_html=True)
            
            if category == "low":
                alloc = {"🏨 Accommodation": 24, "🍽️ Food": 28, "🎯 Activities": 36, "🚗 Transport": 12}
            elif category == "medium":
                alloc = {"🏨 Accommodation": 33, "🍽️ Food": 25, "🎯 Activities": 30, "🚗 Transport": 12}
            else:
                alloc = {"🏨 Accommodation": 38, "🍽️ Food": 25, "🎯 Activities": 27, "🚗 Transport": 10}
            
            for cat, pct in alloc.items():
                amt = (total * pct) / 100
                daily = amt / num_days_saved
                st.markdown(f"""
                <p style="margin: 0.3rem 0; padding-left: 1rem;">
                    ├─ {cat}: ₹{daily:,.0f}/day ({pct}%) = ₹{amt:,.0f} total
                </p>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <p style="margin-top: 1rem; color: green; font-weight: bold;">
                    ✅ All ₹{total:,} optimally allocated!
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Summary
        if result.get('summary'):
            summary = result['summary']
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Activities", summary['total_activities'])
            with col2:
                st.metric("Total Cost", f"₹{summary['total_cost']:,.0f}")
            with col3:
                st.metric("Budget Used", f"{summary['budget_used_percentage']}%")
            with col4:
                st.metric("Remaining", f"₹{summary['budget_remaining']:,.0f}")
        
        # Itinerary
        st.markdown("---")
        st.header("📅 Your Itinerary")
        
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
                    st.markdown(f"""
                    <div class="day-header">
                        <h2 style="margin: 0;">Day {idx} - {day_data.get('date')}</h2>
                        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                            {len(activities)} activities • ₹{day_summary.get('total_cost', 0):,.0f} • 
                            {day_summary.get('start_time', '')} - {day_summary.get('end_time', '')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Activities - CLEAN FORMAT
                    for activity in activities:
                        insights = activity.get('rag_insights', {})
                        description = insights.get('general_tip', '')
                        
                        # Extract clean bullet points
                        bullet_points = []
                        if description:
                            # Clean the description
                            description = description.replace('**', '').replace('*', '')
                            
                            # Split by newlines and process
                            lines = description.split('\n')
                            for line in lines:
                                line = line.strip()
                                # Remove bullet symbols
                                line = line.lstrip('•-–—*').strip()
                                
                                # Skip headers and unwanted text
                                skip_phrases = [
                                    'best practices:', 'common mistakes:', 'typical duration:', 
                                    'for restaurant', 'for museum', 'for location', 'to avoid:',
                                    'best practices', 'common mistakes', 'duration:'
                                ]
                                
                                if any(skip.lower() in line.lower() for skip in skip_phrases):
                                    continue
                                
                                # Keep only meaningful tips (sentence-like)
                                if len(line) > 10 and line[0].isupper():
                                    bullet_points.append(line)
                        
                        # Default if no tips found
                        if not bullet_points:
                            bullet_points = ['Enjoy your visit to this wonderful location']
                        
                        # Limit to 4 tips
                        bullet_points = bullet_points[:4]
                        
                        # Determine meal label for restaurants
                        category_label = ""
                        if activity.get('category') == 'restaurant':
                            start_hour = int(activity['start_time'].split(':')[0])
                            if start_hour < 11:
                                category_label = " "
                            elif start_hour < 16:
                                category_label = " "
                            else:
                                category_label = " "
                        
                        # Category for "Best Practices for X"
                        if activity.get('category') == 'restaurant':
                            practices_category = "Restaurant"
                        elif activity.get('category') == 'museum':
                            practices_category = "Museum"
                        else:
                            practices_category = activity.get('category', 'Location').title()
                        
                        # Build tips HTML
                        tips_html = ""
                        for tip in bullet_points:
                            tips_html += f"• {tip}<br>"
                        
                        # Cost display
                        actual_cost = activity['cost']
                        if actual_cost == 0:
                            cost_display = "Free"
                        elif actual_cost < 100:
                            cost_display = "₹50-100"
                        elif actual_cost < 300:
                            cost_display = "₹100-300"
                        elif actual_cost < 600:
                            cost_display = "₹300-600"
                        elif actual_cost < 1000:
                            cost_display = "₹600-1,000"
                        elif actual_cost < 2000:
                            cost_display = "₹1,000-2,000"
                        else:
                            cost_display = "₹2,000+"
                        
                        # Display activity
                        st.markdown(f"""
                        <div class="activity-item">
                            <div style="font-size: 1.1rem; font-weight: 600; color: #2c3e50; margin-bottom: 0.3rem;">
                                {activity['start_time']} - {activity['end_time']}
                            </div>
                            <div style="font-size: 1.3rem; font-weight: 600; color: #2c3e50; margin-bottom: 0.5rem;">
                                {activity['activity_name']}{category_label}
                            </div>
                            <div style="color: #666; font-size: 0.95rem; margin-bottom: 0.8rem;">
                                📍 {activity.get('address', 'Address not available')}
                            </div>
                            <div style="margin-bottom: 0.8rem;">
                                <div style="color: #1E88E5; font-weight: 600; margin-bottom: 0.4rem;">
                                    💡 Best Practices for {practices_category}
                                </div>
                                <div style="color: #555; line-height: 1.6;">
                                    {tips_html}
                                </div>
                            </div>
                            <div style="font-size: 0.95rem; color: #666;">
                                <strong>Avg Cost:</strong> {cost_display} &nbsp;&nbsp;&nbsp; <strong>Rating:</strong> {activity.get('rating', 'N/A')}★
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Daily summary
                    activity_cost = sum(a['cost'] for a in activities if a.get('category') != 'restaurant')
                    food_cost = sum(a['cost'] for a in activities if a.get('category') == 'restaurant')
                    activity_count = len([a for a in activities if a.get('category') != 'restaurant'])
                    meal_count = len([a for a in activities if a.get('category') == 'restaurant'])
                    
                    st.markdown(f"""
                    <div style="background-color: #e8f4f8; padding: 1rem; border-radius: 8px; margin-top: 1.5rem;">
                        <p style="margin: 0; font-weight: bold; color: #1E88E5;">Daily Summary:</p>
                        <p style="margin: 0.5rem 0 0 0;">
                            <strong>Activities:</strong> ₹{activity_cost:,.0f} ({activity_count} places) | 
                            <strong>Food:</strong> ₹{food_cost:,.0f} ({meal_count} meals) | 
                            <strong>Total:</strong> ₹{day_summary.get('total_cost', 0):,.0f}
                        </p>
                        <p style="margin: 0.3rem 0 0 0; color: #0066cc;">
                            🌙 End your day and rest at your accommodation.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Tips
        if result.get('travel_tips'):
            st.markdown("---")
            st.header("💡 Travel Tips")
            tips_col1, tips_col2 = st.columns(2)
            for idx, tip in enumerate(result['travel_tips']):
                with tips_col1 if idx % 2 == 0 else tips_col2:
                    st.info(f"**{tip.get('category', 'General').title()}:** {tip.get('tip', '')}")
        
        # Download
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.download_button(
                "📥 Download Itinerary",
                json.dumps(result, indent=2),
                f"itinerary_{destination.replace(' ', '_')}_{start_date}.json",
                "application/json",
                use_container_width=True
            )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Smart Travel Planner | Constraint-Based Planning System</p>
</div>
""", unsafe_allow_html=True)
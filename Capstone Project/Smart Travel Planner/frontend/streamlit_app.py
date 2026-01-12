import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.title("Smart Travel Planner")

city = st.text_input("City", "Pune")
days = st.number_input("Number of days", 1, 7, 2)
budget = st.number_input("Total budget", 500, 10000, 5000)

if st.button("Generate Plan"):
    response = requests.post(
        f"{BACKEND_URL}/generate-itinerary",
        params={
            "city": city,
            "days": days,
            "budget": budget
        }
    )

    result = response.json()

    if not result["is_feasible"]:
        st.error("Plan not feasible")
        st.json(result)
    else:
        st.success("Feasible plan generated")

        itinerary = result["itinerary"]
        constraints = result["constraints"]

        st.subheader("Day-wise Plan")
        for day in itinerary["plans"]:
            st.markdown(f"### Day {day['day']}")
            for poi in day["pois"]:
                st.write(f"- {poi['name']} ({poi['category']})")

        if st.button("Explain this plan"):
            explain_resp = requests.post(
                f"{BACKEND_URL}/explain-itinerary",
                json={
                    "itinerary": itinerary,
                    "constraints": constraints
                }
            )
            explanation = explain_resp.json()["explanation"]

            st.subheader("Why this plan?")
            st.write(explanation)

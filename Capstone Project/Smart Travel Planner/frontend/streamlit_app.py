import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.title("Smart Travel Planner (Day 2)")

city = st.text_input("Enter city")

if st.button("Fetch POIs"):
    response = requests.get(f"{BACKEND_URL}/pois", params={"city": city})
    pois = response.json()

    st.write(f"Found {len(pois)} places")
    for p in pois[:10]:
        st.write(p["name"], "-", p["category"])

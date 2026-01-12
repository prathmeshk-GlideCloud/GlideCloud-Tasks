# Smart Travel Planner (Constraint-Based Planning)

## Overview
This project implements a **Smart Travel Planner** using a **deterministic, constraint-based planning engine**, with an **AI-assisted explanation layer**.

The system strictly separates:
- **Planning (deterministic, rule-based)**
- **Explanation (LLM-assisted, read-only)**

AI is never used to generate or alter itineraries.

---

## Key Features
- Constraint-based itinerary planning
- Budget, time, distance, and must-visit constraints
- Soft constraint optimization (interests, diversity)
- Local LLM (Ollama) for itinerary explanation
- Streamlit-based frontend
- FastAPI backend

---

## Architecture (High Level)

User Input  
→ Constraint Validation  
→ Deterministic Planning Engine  
→ Optimized Itinerary  
→ RAG-based Explanation (LLM, read-only)  
→ UI Output  

The LLM **never influences planning decisions**.

---

## Tech Stack

| Layer | Technology |
|-----|------------|
Frontend | Streamlit |
Backend API | FastAPI |
Planning Engine | Python (custom logic) |
Maps & POIs | Google Maps Places API |
LLM (Explanation Only) | Ollama (Local LLaMA) |
Testing | Pytest |

---

## Why Ollama?
- Free and offline
- No API keys or billing
- Used **only for explanation**
- Architecture supports easy replacement with cloud LLMs later

---

## Setup Instructions

### 1. Clone Repo
```bash
git clone <repo-url>
cd Smart-Travel-Planner
2. Create Virtual Environment
bash
Copy code
python -m venv venv
venv\Scripts\activate
3. Install Dependencies
bash
Copy code
pip install -r backend/requirements.txt
4. Setup Environment Variables
Create backend/.env:

env
Copy code
GOOGLE_MAPS_API_KEY=your_google_maps_key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b
5. Run Ollama
bash
Copy code
ollama pull llama3:8b
ollama run llama3:8b
6. Run Backend
bash
Copy code
cd backend
uvicorn app.main:app --reload
7. Run Frontend
bash
Copy code
cd frontend
streamlit run streamlit_app.py
Learning Outcomes
Constraint-based planning

Deterministic system design

Proper use of AI as an auxiliary component

Clean architecture separation

Production-aware design choices


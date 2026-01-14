# ✈️ Smart Travel Planner

An AI-powered travel itinerary planner that uses constraint-based optimization, Google Maps integration, and RAG (Retrieval-Augmented Generation) to create personalized, budget-optimized travel plans.
---

## 🌟 Features

### Core Capabilities
- **🤖 AI-Powered Planning** - Intelligent itinerary generation using constraint satisfaction algorithms
- **💰 Hybrid Budget System** - Choose quick ranges (Budget/Comfortable/Premium) or enter custom amounts
- **📍 Google Maps Integration** - Real-time place data, ratings, and locations
- **🧠 RAG System** - Travel tips and best practices from curated knowledge base
- **⭐ Must-Visit Guarantee** - Ensures your must-see places are included
- **🍽️ Smart Meal Scheduling** - Meals scheduled at proper times (8 AM, 1 PM, 8 PM)
- **🎯 Interest-Based Matching** - Activities tailored to your preferences
- **⏰ Time Optimization** - Operating hours: 8 AM - 10 PM daily

### Budget Features
- **Indian Rupee (₹) Support** - Optimized for Indian travel budgets
- **Smart Cost Estimation** - Realistic pricing based on place types
- **Percentage Allocation** - Automatic distribution across accommodation, food, activities, transport
- **Real-time Budget Tracking** - See remaining budget and utilization

### User Experience
- **🔍 City Autocomplete** - Search cities with Google Places API
- **📅 Multi-Day Planning** - Support for trips from 1-30 days
- **📊 Visual Breakdowns** - Interactive budget and activity summaries
- **📥 Export Options** - Download itineraries as JSON
- **🗺️ Clean Display** - Professional, easy-to-read itinerary format

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                      │
│  (User Interface, Budget Selection, Display)                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Itinerary Builder Service                  │   │
│  │  (Orchestrates all components)                       │   │
│  └──┬────────────┬─────────────┬────────────────────────┘   │
│     │            │             │                             │
│  ┌──▼─────┐  ┌──▼──────┐  ┌──▼──────────┐                  │
│  │Google  │  │  RAG    │  │ Constraint  │                  │
│  │Maps API│  │ System  │  │   Solver    │                  │
│  │        │  │(ChromaDB)│  │             │                  │
│  └────────┘  └─────────┘  └─────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Components

1. **Frontend (Streamlit)**
   - Interactive UI with real-time updates
   - Budget calculator with hybrid mode
   - Day-by-day itinerary tabs
   - Travel tips display

2. **Backend (FastAPI)**
   - RESTful API with async support
   - Pydantic validation
   - Error handling and logging
   - CORS middleware

3. **Google Maps Service**
   - Place search by interest
   - Must-visit location finding
   - Distance/time calculations
   - Real ratings and reviews

4. **RAG System (ChromaDB)**
   - 50+ universal travel tips
   - Budget-specific wisdom
   - Pace guidance
   - Activity best practices

5. **Constraint Solver**
   - Greedy scheduling algorithm
   - Hard constraints (budget, time, must-visit)
   - Soft constraints (distance, variety)
   - Meal time optimization

6. **Activity Scorer**
   - Multi-factor ranking (rating, interest match, budget, popularity)
   - Must-visit prioritization
   - Smart cost estimation

---

## 📋 Prerequisites

- Python 3.11+
- Google Maps API Key
- Windows/Linux/Mac OS

---

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/prathmeshk-GlideCloud/GlideCloud-Tasks/Capstone-Project.git
cd smart-travel-planner
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

Create `backend/.env`:
```env
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

Create `frontend/.env`:
```env
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

**🔑 Get Google Maps API Key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable APIs: Places API, Distance Matrix API, Geocoding API
4. Create credentials (API Key)
5. Copy the API key to `.env` files

---

## ▶️ Running the Application

### Terminal 1: Start Backend
```bash
cd backend
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

uvicorn app.main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`

### Terminal 2: Start Frontend
```bash
cd frontend
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

streamlit run app.py
```

Frontend will be available at: `http://localhost:8501`

---

## 📖 Usage Guide

### Quick Start

1. **Open the app** at `http://localhost:8501`

2. **Enter destination** (e.g., "Pune, India")

3. **Select dates** (Start and End date)

4. **Choose budget**:
   - **Quick Select**: Budget / Comfortable / Premium 
   - **Custom Amount**: Enter exact budget (e.g., ₹35,000)

5. **Select interests** (culture, food, history, etc.)

6. **Add must-visit places** (optional):
```
   Shaniwar Wada
   Aga Khan Palace
```

7. **Choose pace**:
   - Relaxed: 3 activities/day
   - Moderate: 4 activities/day
   - Packed: 5 activities/day

8. **Click "Generate Itinerary"**

### Example Input
```
Destination: Pune, India
Dates: Jan 21 - Jan 25, 2026 (5 days)
Budget: Custom ₹35,000
Interests: Culture, History, Food
Must-Visit: Shaniwar Wada, Aga Khan Palace
Pace: Moderate
```

### Example Output
```
Day 1 - 2026-01-21
5 activities • ₹6,840 • 08:00 - 20:15

08:00 - 10:15
Shaniwar Wada
📍 Bajirao Road, Kasba Peth, Pune, Maharashtra

💡 Best Practices:
- Visit early morning to avoid crowds
- Hire a guide for complete history
- Photography allowed in most areas

Avg Cost: ₹100-300 | Rating: 4.4★

13:00 - 14:15
Vohuman Cafe (Lunch)
📍 FC Road, Pune, Maharashtra

💡 Best Practices:
- Try their famous berry pulao
- Arrive before 1 PM to avoid rush
- Cash only, no cards accepted

Avg Cost: ₹300-600 | Rating: 4.6★
```
## 📁 Project Structure
```
smart-travel-planner/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── constraints.py       # Constraint definitions
│   │   │   └── scoring.py           # Activity scoring
│   │   ├── models/
│   │   │   ├── place.py             # Place data models
│   │   │   └── user_input.py        # Request/response models
│   │   ├── routers/
│   │   │   ├── health.py            # Health check endpoint
│   │   │   ├── rag.py               # RAG endpoints
│   │   │   └── planner.py           # Main planner endpoint
│   │   ├── services/
│   │   │   ├── google_maps.py       # Google Maps integration
│   │   │   ├── rag_service.py       # RAG system
│   │   │   ├── constraint_solver.py # Constraint solver
│   │   │   └── itinerary_builder.py # Main orchestrator
│   │   ├── utils/
│   │   │   └── budget_helper.py     # Budget calculations
│   │   ├── config.py                # Configuration
│   │   └── main.py                  # FastAPI app
│   ├── data/
│   │   ├── chromadb/                # Vector database
│   │   └── tourism_content/
│   │       └── universal_travel_tips.json
│   ├── requirements.txt
│   ├── .env
│   └── test_backend_complete.py
│
├── frontend/
│   ├── utils/
│   │   ├── api_client.py            # Backend API client
│   │   └── city_autocomplete.py     # City search
│   ├── app.py                       # Main Streamlit app
│   ├── requirements.txt
│   └── .env
│
└── README.md
```

---

## 🔧 Troubleshooting

### Common Issues

**1. "Request timed out"**
```
Solution: Reduce search radius or limit places in itinerary_builder.py
```

**2. "Google Maps API quota exceeded"**
```
Solution: Enable billing in Google Cloud Console or reduce API calls
```

**3. "No places found for destination"**
```
Solution: Check destination spelling, try adding country (e.g., "Pune, India")
```

**4. "ChromaDB errors"**
```
Solution: Delete data/chromadb folder and restart backend
```

**5. "Import errors"**
```bash
Solution: Ensure virtual environment is activated
pip install -r requirements.txt
```

---

## 🛣️ Future Roadmap

- [ ] **Multi-language support** (Hindi, Spanish, French)
- [ ] **Real-time collaboration** (Share itineraries)
- [ ] **Weather integration** (Weather-based recommendations)
- [ ] **Hotel booking integration** (Direct booking links)
- [ ] **Mobile app** (iOS/Android)
- [ ] **Flight integration** (Flight search and booking)
- [ ] **Social features** (Share on social media)
- [ ] **AI image generation** (Destination previews)
- [ ] **Offline mode** (Download itineraries)
- [ ] **Multi-city trips** (Complex routing)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 👥 Authors

- **Prathmesh Kapde** - *Initial work* - https://github.com/prathmeshk-GlideCloud

---

## 🙏 Acknowledgments

- **Google Maps Platform** - Location data and geocoding
- **ChromaDB** - Vector database for RAG system
- **Streamlit** - Frontend framework
- **FastAPI** - Backend framework

---

## 📧 Contact

For questions or support:
- Email: prathmesh.k@glideclouds.com
---
## ⭐ Star History

If you find this project useful, please consider giving it a star!

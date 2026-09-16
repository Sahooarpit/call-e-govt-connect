# Call-E Govt Connect 🎙️🏛️

An intelligent inbound AI voice agent and municipal dispatch platform designed to revolutionize how citizens report neighborhood issues (potholes, broken streetlights, water leaks, traffic hazards, etc.). Powered by Call-E, FastMCP, and FastAPI.

---

## 🌟 Key Capabilities

- 📞 **Zero-Friction Voice Hotline:** Citizens call a municipal hotline and speak naturally to report issues without downloading clunky apps.
- 🗺️ **Real-Time Address Validation via MCP:** During the call, the AI invokes the Google Maps Geocoding MCP tool to confirm the exact street name and municipality.
- 🧠 **AI Call Summarization:** Summarizes citizen complaints into structured, actionable incident dossiers with category, urgency, and transcript highlights.
- 🏙️ **Dynamic City Endpoints & Web Dashboards:** Dynamic API endpoints and dedicated web views for every municipality (e.g. `/city/Springfield`, `/city/Metropolis`, `/city/Gotham`).
- 📊 **Interactive Municipal Dashboard:** Real-time analytics, issue categorization charts, urgency indicators, instant ticket status transitions, and inbound call simulation.

---

## 🏛️ Endpoints Architecture

### 🌐 Frontend Web Dashboards
| Endpoint | Description |
| :--- | :--- |
| `GET /` or `GET /dashboard` | Master Multi-City Municipal Operations Dashboard |
| `GET /city/{city_name}` | Dynamic Web Dashboard scoped specifically to `{city_name}` |

### 🏙️ Dynamic City API Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/cities` | List of all registered cities with open, emergency, and resolved counts |
| `GET` | `/api/cities/{city_name}` | Comprehensive city dossier (metrics, status & severity distributions, top issues) |
| `GET` | `/api/cities/{city_name}/incidents` | Dynamic list of incident reports & citizen summaries for a specific city |
| `GET` | `/api/cities/{city_name}/summary` | Aggregated citizen voice intelligence and primary concerns synthesis |

### ⚡ Incidents & Dispatch Management API
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/webhook/call-e` | Webhook ingestion endpoint receiving Call-E structured reports & voice transcripts |
| `GET` | `/api/incidents` | Global list of all incidents with filtering by city, status, severity, & search |
| `GET` | `/api/incidents/{id}` | Retrieve specific incident details |
| `PATCH` | `/api/incidents/{id}/status` | Update ticket status (`Open`, `In Progress`, `Resolved`) |
| `GET` | `/api/stats/overview` | System-wide statistics for analytics charts & KPIs |
| `POST` | `/api/incidents/seed` | Seed demo citizen voice reports across multiple cities |

---

## 🚀 Setup & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```ini
DATABASE_URL=sqlite:///./city_incidents.db
CALLE_API_KEY=your_calle_api_key_here
CALLE_PHONE_NUMBER=your_calle_purchased_number
GOOGLE_MAPS_API_KEY=your_google_maps_geocoding_api_key
```

### 3. Run the Server
Launch the FastAPI backend and dashboard:
```bash
uvicorn main:app --port 8000 --reload
```

Open your browser at:
- **Global Dashboard:** `http://localhost:8000/`
- **Dynamic City Views:** `http://localhost:8000/city/Springfield`, `http://localhost:8000/city/Metropolis`, `http://localhost:8000/city/Gotham`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`

---

## 🧪 Testing & Simulation

1. Click **"Seed Data"** or send `POST /api/incidents/seed` to populate sample citizen voice calls.
2. Click **"Simulate Call"** in the UI to emulate an inbound Call-E voice report webhook in real time.
3. Switch between municipalities using the top selector or navigate to `/city/{city_name}` to see the dynamic scoped feed.

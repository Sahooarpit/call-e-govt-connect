import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, Depends, Request, Query, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from database import engine, Base, get_db
from models import IncidentModel
from schemas import (
    IncidentResponse,
    IncidentCreate,
    IncidentStatusUpdate,
    CityItem,
    CityStatsResponse,
    CitySummaryResponse,
    OverviewStatsResponse,
)

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Call-E Govt Connect - Municipal Incident API & Dashboard",
    description="Citizen voice report ingestion, dynamic city endpoints, and AI summarization dashboard.",
    version="1.0.0",
)

# Enable CORS for open dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
INDEX_HTML_PATH = os.path.join(TEMPLATES_DIR, "index.html")


# ==========================================
# 🌐 FRONTEND DASHBOARD ROUTES
# ==========================================

@app.get("/", response_class=HTMLResponse, tags=["Frontend Dashboard"])
async def serve_dashboard():
    """Serve the master municipal operations dashboard."""
    if os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)
    return HTMLResponse("<h1>Call-E Govt Connect Dashboard</h1><p>Template file not found.</p>")


@app.get("/dashboard", response_class=HTMLResponse, tags=["Frontend Dashboard"])
async def serve_dashboard_alias():
    """Alias route for the dashboard."""
    return await serve_dashboard()


@app.get("/city/{city_name}", response_class=HTMLResponse, tags=["Frontend Dashboard"])
@app.get("/dashboard/{city_name}", response_class=HTMLResponse, tags=["Frontend Dashboard"])
async def serve_city_dashboard(city_name: str):
    """
    Dynamic web dashboard endpoint dedicated to a specific city.
    Renders the dashboard scoped directly to {city_name}.
    """
    if os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)
    return HTMLResponse(f"<h1>{city_name} Dashboard</h1>")


# ==========================================
# 📞 INGESTION WEBHOOK (Call-E AI Dispatcher)
# ==========================================

@app.post("/webhook/call-e", status_code=201, tags=["Call-E Webhook"])
async def receive_call_e_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receives structured end-of-call webhooks and transcripts from Call-E voice agent.
    Extracts location, municipality, problem type, severity, and AI-generated call summary.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Call-E structured extraction format
    data = payload.get("structured_result", {})
    city = data.get("city") or payload.get("city") or "Unknown"
    location = data.get("location") or payload.get("location") or "Unspecified Location"
    issue_type = data.get("issue_type") or payload.get("issue_type") or "General Incident"
    severity = data.get("severity") or payload.get("severity") or "Normal"
    
    # Extract caller summary
    summary = payload.get("summary") or payload.get("transcript_summary") or data.get("summary") or "Voice report received from citizen."

    # Normalize casing
    city_formatted = city.strip().title()
    issue_formatted = issue_type.strip().title()
    severity_formatted = severity.strip().capitalize()

    incident = IncidentModel(
        city=city_formatted,
        location=location.strip(),
        issue_type=issue_formatted,
        severity=severity_formatted,
        status="Open",
        call_summary=summary.strip(),
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return {
        "status": "success",
        "message": f"Incident report logged for {city_formatted}",
        "incident_id": incident.id,
        "data": incident.to_dict(),
    }


# ==========================================
# 🏙️ DYNAMIC CITY-SPECIFIC ENDPOINTS
# ==========================================

@app.get("/api/cities", response_model=List[CityItem], tags=["Dynamic City Endpoints"])
def get_all_cities(db: Session = Depends(get_db)):
    """
    Returns a dynamic list of all registered municipalities along with
    their current open, in-progress, resolved, and emergency ticket counts.
    """
    cities = db.query(IncidentModel.city).distinct().all()
    city_names = sorted([c[0] for c in cities if c[0]])

    results = []
    for city_name in city_names:
        total = db.query(IncidentModel).filter(IncidentModel.city.ilike(city_name)).count()
        open_count = db.query(IncidentModel).filter(
            IncidentModel.city.ilike(city_name),
            IncidentModel.status.ilike("Open")
        ).count()
        in_progress = db.query(IncidentModel).filter(
            IncidentModel.city.ilike(city_name),
            IncidentModel.status.ilike("In Progress")
        ).count()
        resolved = db.query(IncidentModel).filter(
            IncidentModel.city.ilike(city_name),
            IncidentModel.status.ilike("Resolved")
        ).count()
        emergency = db.query(IncidentModel).filter(
            IncidentModel.city.ilike(city_name),
            or_(IncidentModel.severity.ilike("Emergency"), IncidentModel.severity.ilike("High"))
        ).count()

        results.append(CityItem(
            city=city_name,
            total_incidents=total,
            open_incidents=open_count,
            in_progress_incidents=in_progress,
            resolved_incidents=resolved,
            emergency_incidents=emergency,
        ))

    return results


@app.get("/api/cities/{city_name}", response_model=CityStatsResponse, tags=["Dynamic City Endpoints"])
def get_city_details(city_name: str, db: Session = Depends(get_db)):
    """
    Dynamic endpoint for a specific city.
    Returns comprehensive analytics, breakdown by status, breakdown by severity,
    top issue categories, and recent citizen voice summaries for that city.
    """
    normalized_city = city_name.strip()
    incidents_query = db.query(IncidentModel).filter(IncidentModel.city.ilike(normalized_city))
    
    total = incidents_query.count()
    if total == 0:
        # Check if city exists case-insensitively or return empty dossier
        pass

    # Status counts
    open_count = incidents_query.filter(IncidentModel.status.ilike("Open")).count()
    in_progress_count = incidents_query.filter(IncidentModel.status.ilike("In Progress")).count()
    resolved_count = incidents_query.filter(IncidentModel.status.ilike("Resolved")).count()

    # Severity counts
    emergency_count = incidents_query.filter(IncidentModel.severity.ilike("Emergency")).count()
    high_count = incidents_query.filter(IncidentModel.severity.ilike("High")).count()
    medium_count = incidents_query.filter(or_(IncidentModel.severity.ilike("Medium"), IncidentModel.severity.ilike("Normal"))).count()
    low_count = incidents_query.filter(IncidentModel.severity.ilike("Low")).count()

    # Top issue categories
    category_counts = (
        db.query(IncidentModel.issue_type, func.count(IncidentModel.id).label("count"))
        .filter(IncidentModel.city.ilike(normalized_city))
        .group_by(IncidentModel.issue_type)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )
    top_issues = [{"issue_type": c[0], "count": c[1]} for c in category_counts]

    # Recent summaries
    recent = (
        db.query(IncidentModel)
        .filter(IncidentModel.city.ilike(normalized_city))
        .order_by(IncidentModel.id.desc())
        .limit(10)
        .all()
    )

    return CityStatsResponse(
        city=normalized_city.title(),
        total_incidents=total,
        status_counts={
            "Open": open_count,
            "In Progress": in_progress_count,
            "Resolved": resolved_count,
        },
        severity_counts={
            "Emergency": emergency_count,
            "High": high_count,
            "Medium": medium_count,
            "Low": low_count,
        },
        top_issues=top_issues,
        recent_summaries=recent,
    )


@app.get("/api/cities/{city_name}/incidents", response_model=List[IncidentResponse], tags=["Dynamic City Endpoints"])
def get_city_incidents(
    city_name: str,
    status: Optional[str] = Query(None, description="Filter by status: Open, In Progress, Resolved"),
    severity: Optional[str] = Query(None, description="Filter by severity: Emergency, High, Medium, Low"),
    search: Optional[str] = Query(None, description="Search keyword across summaries, locations, issues"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Dynamic endpoint returning all incidents and caller summaries for a specific city.
    Supports filtering by status, severity, keyword search, and pagination.
    """
    query = db.query(IncidentModel).filter(IncidentModel.city.ilike(city_name.strip()))

    if status:
        query = query.filter(IncidentModel.status.ilike(status.strip()))
    if severity:
        query = query.filter(IncidentModel.severity.ilike(severity.strip()))
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                IncidentModel.call_summary.ilike(search_term),
                IncidentModel.location.ilike(search_term),
                IncidentModel.issue_type.ilike(search_term),
            )
        )

    return query.order_by(IncidentModel.id.desc()).offset(offset).limit(limit).all()


@app.get("/api/cities/{city_name}/summary", response_model=CitySummaryResponse, tags=["Dynamic City Endpoints"])
def get_city_summarized_intelligence(city_name: str, db: Session = Depends(get_db)):
    """
    Dynamic voice intelligence endpoint providing aggregated summary notes
    and citizen feedback synthesis for a specific city.
    """
    normalized_city = city_name.strip()
    incidents = (
        db.query(IncidentModel)
        .filter(IncidentModel.city.ilike(normalized_city))
        .order_by(IncidentModel.id.desc())
        .limit(20)
        .all()
    )

    total_calls = db.query(IncidentModel).filter(IncidentModel.city.ilike(normalized_city)).count()
    open_count = db.query(IncidentModel).filter(
        IncidentModel.city.ilike(normalized_city),
        IncidentModel.status.ilike("Open")
    ).count()

    emergency_count = db.query(IncidentModel).filter(
        IncidentModel.city.ilike(normalized_city),
        or_(IncidentModel.severity.ilike("Emergency"), IncidentModel.severity.ilike("High"))
    ).count()

    urgency_level = "High" if emergency_count > 0 else ("Moderate" if open_count > 2 else "Low")

    # Category concerns
    category_counts = (
        db.query(IncidentModel.issue_type)
        .filter(IncidentModel.city.ilike(normalized_city))
        .group_by(IncidentModel.issue_type)
        .order_by(desc(func.count(IncidentModel.id)))
        .limit(3)
        .all()
    )
    primary_concerns = [c[0] for c in category_counts if c[0]]

    recent_summaries = [
        {
            "id": inc.id,
            "issue_type": inc.issue_type,
            "location": inc.location,
            "severity": inc.severity,
            "status": inc.status,
            "call_summary": inc.call_summary,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
        }
        for inc in incidents
        if inc.call_summary
    ]

    return CitySummaryResponse(
        city=normalized_city.title(),
        total_calls=total_calls,
        open_issues=open_count,
        urgency_level=urgency_level,
        primary_concerns=primary_concerns,
        recent_call_summaries=recent_summaries,
    )


# ==========================================
# 📊 GLOBAL INCIDENTS & ANALYTICS API
# ==========================================

@app.get("/api/stats/overview", response_model=OverviewStatsResponse, tags=["Analytics & Overview"])
def get_global_overview_stats(db: Session = Depends(get_db)):
    """
    Returns system-wide aggregated metrics across all serviced cities.
    """
    total = db.query(IncidentModel).count()
    open_count = db.query(IncidentModel).filter(IncidentModel.status.ilike("Open")).count()
    in_progress_count = db.query(IncidentModel).filter(IncidentModel.status.ilike("In Progress")).count()
    resolved_count = db.query(IncidentModel).filter(IncidentModel.status.ilike("Resolved")).count()
    emergency_count = db.query(IncidentModel).filter(
        or_(IncidentModel.severity.ilike("Emergency"), IncidentModel.severity.ilike("High"))
    ).count()

    # Severity distribution
    sev_counts = {
        "Emergency": db.query(IncidentModel).filter(IncidentModel.severity.ilike("Emergency")).count(),
        "High": db.query(IncidentModel).filter(IncidentModel.severity.ilike("High")).count(),
        "Medium": db.query(IncidentModel).filter(or_(IncidentModel.severity.ilike("Medium"), IncidentModel.severity.ilike("Normal"))).count(),
        "Low": db.query(IncidentModel).filter(IncidentModel.severity.ilike("Low")).count(),
    }

    # Top categories across all cities
    cat_counts = (
        db.query(IncidentModel.issue_type, func.count(IncidentModel.id).label("count"))
        .group_by(IncidentModel.issue_type)
        .order_by(desc("count"))
        .limit(6)
        .all()
    )
    category_breakdown = [{"issue_type": c[0], "count": c[1]} for c in cat_counts]

    # Cities list
    cities = get_all_cities(db)

    return OverviewStatsResponse(
        total_incidents=total,
        total_cities=len(cities),
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        emergency_count=emergency_count,
        severity_breakdown=sev_counts,
        category_breakdown=category_breakdown,
        cities=cities,
    )


@app.get("/api/incidents", response_model=List[IncidentResponse], tags=["Incidents"])
def get_incidents(
    city: Optional[str] = Query(None, description="Filter incidents by specific city name"),
    status: Optional[str] = Query(None, description="Filter by status (Open, In Progress, Resolved)"),
    severity: Optional[str] = Query(None, description="Filter by severity (Emergency, High, Medium, Low)"),
    search: Optional[str] = Query(None, description="Search transcripts or locations"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve all incident reports, with dynamic filtering by city, status, severity, and search term."""
    query = db.query(IncidentModel)

    if city and city.strip():
        query = query.filter(IncidentModel.city.ilike(city.strip()))
    if status and status.strip():
        query = query.filter(IncidentModel.status.ilike(status.strip()))
    if severity and severity.strip():
        query = query.filter(IncidentModel.severity.ilike(severity.strip()))
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                IncidentModel.call_summary.ilike(term),
                IncidentModel.location.ilike(term),
                IncidentModel.issue_type.ilike(term),
                IncidentModel.city.ilike(term),
            )
        )

    return query.order_by(IncidentModel.id.desc()).offset(offset).limit(limit).all()


@app.get("/api/incidents/{incident_id}", response_model=IncidentResponse, tags=["Incidents"])
def get_incident_by_id(incident_id: int, db: Session = Depends(get_db)):
    """Retrieve a single incident by its ID."""
    incident = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident #{incident_id} not found")
    return incident


@app.patch("/api/incidents/{incident_id}/status", response_model=IncidentResponse, tags=["Incidents"])
def update_incident_status(incident_id: int, payload: IncidentStatusUpdate, db: Session = Depends(get_db)):
    """
    Update the resolution status of an incident ticket (Open, In Progress, Resolved).
    """
    incident = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident #{incident_id} not found")

    valid_statuses = ["Open", "In Progress", "Resolved"]
    normalized_status = payload.status.strip().title()
    if normalized_status not in valid_statuses:
        # Accept variations like in progress
        if payload.status.strip().lower() == "in progress":
            normalized_status = "In Progress"
        elif payload.status.strip().lower() == "open":
            normalized_status = "Open"
        elif payload.status.strip().lower() == "resolved":
            normalized_status = "Resolved"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{payload.status}'. Must be one of: {', '.join(valid_statuses)}",
            )

    incident.status = normalized_status
    db.commit()
    db.refresh(incident)
    return incident


@app.post("/api/incidents", response_model=IncidentResponse, status_code=201, tags=["Incidents"])
def create_incident_manual(payload: IncidentCreate, db: Session = Depends(get_db)):
    """Direct incident creation endpoint."""
    incident = IncidentModel(
        city=payload.city.strip().title(),
        location=payload.location.strip(),
        issue_type=payload.issue_type.strip().title(),
        severity=payload.severity.strip().capitalize(),
        status=payload.status.strip().title() if payload.status else "Open",
        call_summary=payload.call_summary.strip() if payload.call_summary else None,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


# ==========================================
# 🌱 SAMPLE DATA SEEDING (Demo & Testing)
# ==========================================

@app.post("/api/incidents/seed", status_code=201, tags=["Seed Data"])
def seed_sample_incidents(db: Session = Depends(get_db)):
    """
    Seeds the database with realistic citizen voice reports and AI summaries
    across multiple cities (Springfield, Metropolis, Gotham, Seattle, Austin).
    """
    sample_reports = [
        {
            "city": "Springfield",
            "location": "742 Evergreen Terrace",
            "issue_type": "Pothole",
            "severity": "High",
            "status": "In Progress",
            "call_summary": "Caller reported a deep 2-foot pothole on the eastbound lane near the driveway. Stated two cars blew tires this morning and it poses immediate damage risk to traffic.",
        },
        {
            "city": "Springfield",
            "location": "120 Main Street & 4th Ave",
            "issue_type": "Traffic Signal",
            "severity": "Emergency",
            "status": "Open",
            "call_summary": "Citizen called in panic stating the traffic light at Main and 4th is completely dead in all directions, creating a dangerous intersection standoff with near-miss collisions.",
        },
        {
            "city": "Springfield",
            "location": "45 Elm Boulevard",
            "issue_type": "Streetlight",
            "severity": "Low",
            "status": "Resolved",
            "call_summary": "Resident reported flickering streetlight in front of house. Crew attended and replaced faulty LED ballast.",
        },
        {
            "city": "Metropolis",
            "location": "100 Lex Street",
            "issue_type": "Water Main Break",
            "severity": "Emergency",
            "status": "Open",
            "call_summary": "High-pressure water main rupture spilling onto roadway and threatening basement utility rooms of adjacent commercial buildings. Water depth approximately 6 inches on road.",
        },
        {
            "city": "Metropolis",
            "location": "500 Daily Planet Plaza",
            "issue_type": "Fallen Tree Branch",
            "severity": "Medium",
            "status": "In Progress",
            "call_summary": "Caller reports heavy storm branch fell onto the pedestrian walkway blocking access to the transit entrance. No injuries reported.",
        },
        {
            "city": "Metropolis",
            "location": "88 Centennial Park West",
            "issue_type": "Illegal Dumping",
            "severity": "Low",
            "status": "Open",
            "call_summary": "Citizen reported construction debris and discarded tires left behind near the park boundary.",
        },
        {
            "city": "Gotham",
            "location": "224 Crime Alley",
            "issue_type": "Streetlight",
            "severity": "High",
            "status": "Open",
            "call_summary": "Citizen called stating five consecutive streetlights are out along Crime Alley, creating complete darkness and safety concerns for pedestrians walking home from the subway.",
        },
        {
            "city": "Gotham",
            "location": "1000 Wayne Tower Way",
            "issue_type": "Manhole Cover",
            "severity": "Emergency",
            "status": "In Progress",
            "call_summary": "Caller stated a heavy sewer manhole cover has shifted completely off its rim in the center driving lane. Deep open drop poses fatal crash hazard.",
        },
        {
            "city": "Seattle",
            "location": "400 Pine Street",
            "issue_type": "Storm Drain Clog",
            "severity": "High",
            "status": "Open",
            "call_summary": "Heavy rainfall causing localized flooding at the curb ramp because the storm drain grate is completely choked with autumn leaves and silt.",
        },
        {
            "city": "Austin",
            "location": "1100 Congress Avenue",
            "issue_type": "Pothole",
            "severity": "Medium",
            "status": "Resolved",
            "call_summary": "Caller reported asphalt crumbling near the crosswalk. Road maintenance team patched the area with cold-mix asphalt.",
        },
        {
            "city": "Austin",
            "location": "600 East 6th Street",
            "issue_type": "Broken Glass / Sanitation",
            "severity": "Medium",
            "status": "Open",
            "call_summary": "Citizen reported extensive shattered glass across bicycle lane following weekend events. Street sweeper dispatch requested.",
        },
    ]

    added = []
    for item in sample_reports:
        incident = IncidentModel(**item)
        db.add(incident)
        added.append(incident)

    db.commit()
    for inc in added:
        db.refresh(inc)

    return {
        "status": "success",
        "message": f"Successfully seeded {len(added)} realistic citizen reports across {len(set(r['city'] for r in sample_reports))} cities.",
        "count": len(added),
    }

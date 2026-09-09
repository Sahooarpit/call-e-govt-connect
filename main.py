from fastapi import FastAPI, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database import engine, Base, get_db
from models import IncidentModel

Base.metadata.create_all(bind=engine)

app = FastAPI(title="City Incident Management API")


class IncidentResponse(BaseModel):
    id: int
    city: str
    location: str
    issue_type: str
    severity: str
    status: str
    call_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- INGESTION WEBHOOK ---
@app.post("/webhook/call-e", status_code=201)
async def receive_call_e_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    data = payload.get("structured_result", {})

    incident = IncidentModel(
        city=data.get("city", "Unknown").title(),
        location=data.get("location", "Unspecified"),
        issue_type=data.get("issue_type", "General").capitalize(),
        severity=data.get("severity", "Normal").capitalize(),
        call_summary=payload.get("summary", "No transcript summary.")
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return {"status": "success", "incident_id": incident.id}


# --- CITY LOOKUP & FILTERING ENDPOINTS ---
@app.get("/api/cities", response_model=List[str])
def get_all_cities(db: Session = Depends(get_db)):
    """Returns a list of all unique cities with registered incidents."""
    cities = db.query(IncidentModel.city).distinct().all()
    return [c[0] for c in cities if c[0]]


@app.get("/api/incidents", response_model=List[IncidentResponse])
def get_incidents(
        city: Optional[str] = Query(None, description="Filter incidents by specific city name"),
        status: Optional[str] = Query(None, description="Filter by status (Open, In Progress, Resolved)"),
        db: Session = Depends(get_db)
):
    """Retrieve incidents, optionally filtered by city or status."""
    query = db.query(IncidentModel)

    if city:
        query = query.filter(IncidentModel.city.ilike(city.strip()))
    if status:
        query = query.filter(IncidentModel.status.ilike(status.strip()))

    return query.order_by(IncidentModel.id.desc()).all()
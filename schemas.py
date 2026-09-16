from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Standardized Incident Response
class IncidentResponse(BaseModel):
    id: int
    city: str
    location: str
    issue_type: str
    severity: str
    status: str
    call_summary: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Input Schema for Direct Incident Creation
class IncidentCreate(BaseModel):
    city: str = Field(..., example="Springfield")
    location: str = Field(..., example="742 Evergreen Terrace")
    issue_type: str = Field(..., example="Pothole")
    severity: str = Field(default="Normal", example="High")
    call_summary: Optional[str] = Field(default=None, example="Citizen reported a 2-foot pothole causing tire damage.")
    status: Optional[str] = Field(default="Open", example="Open")


# Status Update Schema
class IncidentStatusUpdate(BaseModel):
    status: str = Field(..., example="In Progress")


# City Summary Item in City Listing
class CityItem(BaseModel):
    city: str
    total_incidents: int
    open_incidents: int
    in_progress_incidents: int
    resolved_incidents: int
    emergency_incidents: int


# Detailed City Analytics & Stats Response
class CityStatsResponse(BaseModel):
    city: str
    total_incidents: int
    status_counts: Dict[str, int]
    severity_counts: Dict[str, int]
    top_issues: List[Dict[str, Any]]
    recent_summaries: List[IncidentResponse]


# Aggregated City Voice Intelligence Summary
class CitySummaryResponse(BaseModel):
    city: str
    total_calls: int
    open_issues: int
    urgency_level: str
    primary_concerns: List[str]
    recent_call_summaries: List[Dict[str, Any]]


# System-wide Overview Stats Response
class OverviewStatsResponse(BaseModel):
    total_incidents: int
    total_cities: int
    open_count: int
    in_progress_count: int
    resolved_count: int
    emergency_count: int
    severity_breakdown: Dict[str, int]
    category_breakdown: List[Dict[str, Any]]
    cities: List[CityItem]

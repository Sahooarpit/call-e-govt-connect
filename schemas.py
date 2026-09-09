from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Used for standardizing API responses
class IncidentResponse(BaseModel):
    id: int
    issue_type: str
    location: str
    severity: str
    call_summary: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

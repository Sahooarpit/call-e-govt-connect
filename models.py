from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class IncidentModel(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True, nullable=False)  # e.g., "Springfield"
    location = Column(String, index=True, nullable=False)  # e.g., "742 Evergreen Terrace"
    issue_type = Column(String, index=True, nullable=False)  # e.g., "Pothole", "Streetlight"
    severity = Column(String, default="Normal")  # Low, Medium, High, Emergency
    status = Column(String, default="Open")  # Open, In Progress, Resolved
    call_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "city": self.city,
            "location": self.location,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "status": self.status,
            "call_summary": self.call_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

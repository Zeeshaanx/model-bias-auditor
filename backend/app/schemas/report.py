from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ReportFormat


class ReportCreate(BaseModel):
    audit_id: str
    format: ReportFormat = ReportFormat.JSON


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    audit_id: str
    format: str
    content: str
    created_at: datetime

from typing import Any

from pydantic import BaseModel


class DashboardMetrics(BaseModel):
    targets: int
    audits: int
    audits_running: int
    findings: int
    critical_findings: int
    low_signal_findings: int = 0
    highest_disparity: float
    findings_by_attribute: list[dict[str, Any]]
    findings_by_severity: dict[str, int]
    recent_audits: list[dict[str, Any]]

"""Pydantic models for cloud security posture findings."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class Severity(str, Enum):
    """Severity levels for findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplianceIssue(BaseModel):
    """Single compliance mapping for a finding."""

    framework: str = Field(..., description="Compliance framework name (e.g., CIS)")
    control_id: str = Field(..., description="Control identifier")
    description: str = Field(..., description="Control description")


class CloudFinding(BaseModel):
    """Cloud posture finding."""

    finding_id: str
    provider: CloudProvider
    severity: Severity
    title: str
    description: str
    resource_id: str
    resource_type: str
    region: str | None = None
    recommendation: str | None = None
    compliance_issues: list[ComplianceIssue] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ScanReport(BaseModel):
    """Normalized report for a cloud provider scan."""

    provider: CloudProvider
    started_at: datetime
    completed_at: datetime
    findings: list[CloudFinding] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    @property
    def finding_count(self) -> int:
        """Total number of findings."""
        return len(self.findings)

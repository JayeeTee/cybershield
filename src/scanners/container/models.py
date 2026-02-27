"""Pydantic models for container security scanning."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ContainerSeverity(str, Enum):
    """Severity levels for container findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(str, Enum):
    """Container finding categories."""

    IMAGE = "image"
    RUNTIME = "runtime"
    KUBERNETES = "kubernetes"


class ScannerBackend(str, Enum):
    """Supported vulnerability scanning backends."""

    TRIVY = "trivy"
    GRYPE = "grype"
    CUSTOM = "custom"


class ComplianceIssue(BaseModel):
    """Single compliance mapping for a finding."""

    framework: str = Field(..., description="Compliance framework name")
    control_id: str = Field(..., description="Control identifier")
    description: str = Field(..., description="Control description")


class CVEMetadata(BaseModel):
    """CVE metadata from local/remote vulnerability intelligence."""

    cve_id: str
    cvss_score: float | None = None
    severity: ContainerSeverity | None = None
    description: str | None = None
    references: list[str] = Field(default_factory=list)
    remediation: str | None = None


class ContainerFinding(BaseModel):
    """Unified container finding model."""

    finding_id: str
    category: FindingCategory
    severity: ContainerSeverity
    title: str
    description: str
    resource_id: str
    resource_type: str
    scanner: ScannerBackend | None = None
    cve_id: str | None = None
    package_name: str | None = None
    installed_version: str | None = None
    fixed_version: str | None = None
    cvss_score: float | None = None
    recommendation: str | None = None
    compliance_issues: list[ComplianceIssue] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContainerScanReport(BaseModel):
    """Normalized report for container scans."""

    scanner_name: str
    target: str
    started_at: datetime
    completed_at: datetime
    findings: list[ContainerFinding] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def finding_count(self) -> int:
        """Total number of findings."""
        return len(self.findings)

    @property
    def vulnerability_count(self) -> int:
        """Total findings tied to a CVE."""
        return sum(1 for finding in self.findings if finding.cve_id)

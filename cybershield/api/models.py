"""API models for CyberShield FastAPI endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ScanType(str, Enum):
    """Supported scan families."""

    CLOUD = "cloud"
    SECRETS = "secrets"
    CONTAINER = "container"
    NETWORK = "network"


class ScanStatus(str, Enum):
    """Execution status for asynchronous scans."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    """Severity levels for security findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CloudScanRequest(BaseModel):
    provider: str = Field(..., description="Cloud provider: aws|azure|gcp")
    account_id: str = Field(..., min_length=3, max_length=128)
    regions: list[str] = Field(default_factory=list)
    include_compliance: bool = True


class SecretScanRequest(BaseModel):
    repository_url: str = Field(..., min_length=4, max_length=500)
    branch: str = Field(default="main", min_length=1, max_length=255)
    include_history: bool = False


class ContainerScanRequest(BaseModel):
    image: str = Field(..., min_length=3, max_length=255)
    tag: str = Field(default="latest", min_length=1, max_length=128)
    runtime_checks: bool = False


class NetworkScanRequest(BaseModel):
    source: str = Field(..., description="network interface or pcap source")
    duration_seconds: int = Field(default=60, ge=5, le=3600)
    detect_anomalies: bool = True


class ScanAcceptedResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    scan_type: ScanType
    submitted_at: datetime


class ScanFinding(BaseModel):
    finding_id: str
    scan_id: str
    scan_type: ScanType
    title: str
    description: str
    severity: Severity
    resource: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScanResultResponse(BaseModel):
    scan_id: str
    scan_type: ScanType
    status: ScanStatus
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    progress: int = Field(default=0, ge=0, le=100)
    summary: dict[str, Any] = Field(default_factory=dict)
    findings: list[ScanFinding] = Field(default_factory=list)
    error: str | None = None


class IOCReputationResponse(BaseModel):
    indicator: str
    score: int = Field(..., ge=0, le=100, description="Higher is more malicious")
    confidence: int = Field(..., ge=0, le=100)
    malicious: bool
    sources: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    first_seen: datetime
    last_seen: datetime


class CVEDetailsResponse(BaseModel):
    cve_id: str
    cvss_score: float = Field(..., ge=0.0, le=10.0)
    severity: Severity
    summary: str
    affected_products: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    published_at: datetime
    updated_at: datetime

    @field_validator("cve_id")
    @classmethod
    def validate_cve(cls, value: str) -> str:
        upper = value.upper()
        if not upper.startswith("CVE-"):
            raise ValueError("cve_id must start with CVE-")
        return upper


class ThreatFeedItem(BaseModel):
    title: str
    category: str
    severity: Severity
    source: str
    indicator: str
    observed_at: datetime


class ThreatFeedResponse(BaseModel):
    items: list[ThreatFeedItem]
    generated_at: datetime
    total: int


class DashboardSummaryResponse(BaseModel):
    generated_at: datetime
    total_scans: int
    completed_scans: int
    failed_scans: int
    open_findings: int
    high_risk_findings: int
    overall_risk_score: int = Field(..., ge=0, le=100)


class FindingsListResponse(BaseModel):
    findings: list[ScanFinding]
    total: int


class DashboardMetricsResponse(BaseModel):
    generated_at: datetime
    findings_by_severity: dict[str, int]
    scans_by_type: dict[str, int]
    success_rate_percent: float
    mean_time_to_complete_seconds: float


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class TokenRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=3, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


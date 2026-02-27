"""Pydantic models for threat intelligence aggregation and correlation."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class IntelligenceError(Exception):
    """Base exception for intelligence module errors."""


class FeedClientError(IntelligenceError):
    """Raised when a feed client fails to fetch or parse data."""


class MissingAPIKeyError(IntelligenceError):
    """Raised when a feed operation requires an API key that is missing."""


class RateLimitError(IntelligenceError):
    """Raised when a client call exceeds configured rate limits."""


class IndicatorType(str, Enum):
    """Supported IOC indicator types."""

    IP = "ip"
    DOMAIN = "domain"
    HASH = "hash"


class Indicator(BaseModel):
    """Normalized indicator object used across feeds."""

    value: str
    type: IndicatorType
    source: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reputation_score: int = Field(default=0, ge=0, le=100)
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ThreatActorProfile(BaseModel):
    """Threat actor profile details."""

    name: str
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    motivation: list[str] = Field(default_factory=list)
    techniques: list[str] = Field(default_factory=list)
    known_targets: list[str] = Field(default_factory=list)
    source: str


class AttackTechnique(BaseModel):
    """MITRE ATT&CK technique mapping."""

    technique_id: str
    name: str
    tactic: str | None = None
    description: str | None = None
    source: str = "mitre"
    metadata: dict[str, Any] = Field(default_factory=dict)


class VulnerabilityRecord(BaseModel):
    """Normalized CVE vulnerability record."""

    cve_id: str
    summary: str | None = None
    cvss_score: float | None = None
    severity: str | None = None
    published: datetime | None = None
    modified: datetime | None = None
    references: list[str] = Field(default_factory=list)
    source: str = "cve"


class FeedResult(BaseModel):
    """Single feed response normalized to a common model."""

    source: str
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    indicators: list[Indicator] = Field(default_factory=list)
    threat_actors: list[ThreatActorProfile] = Field(default_factory=list)
    techniques: list[AttackTechnique] = Field(default_factory=list)
    vulnerabilities: list[VulnerabilityRecord] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class CorrelatedThreat(BaseModel):
    """Cross-feed correlated threat output."""

    indicator: Indicator
    sources: list[str] = Field(default_factory=list)
    linked_techniques: list[AttackTechnique] = Field(default_factory=list)
    linked_vulnerabilities: list[VulnerabilityRecord] = Field(default_factory=list)
    linked_actors: list[ThreatActorProfile] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    decay_factor: float = Field(default=1.0, ge=0.0, le=1.0)
    threat_score: int = Field(default=0, ge=0, le=100)


class IntelligenceReport(BaseModel):
    """End-to-end threat intelligence report."""

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_results: list[FeedResult] = Field(default_factory=list)
    correlated_threats: list[CorrelatedThreat] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class IntelligenceConfig(BaseSettings):
    """Configuration and API key management for feed clients."""

    model_config = SettingsConfigDict(env_prefix="CYBERSHIELD_", extra="ignore")

    abuseipdb_api_key: str | None = None
    virustotal_api_key: str | None = None
    alienvault_otx_api_key: str | None = None

    mitre_attack_url: str = (
        "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
    )
    cve_api_url: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    request_timeout_seconds: int = 15
    cache_ttl_seconds: int = 300
    rate_limit_per_minute: int = 60
    stale_decay_days: int = 30

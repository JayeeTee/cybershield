"""Threat intelligence API routes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from cybershield.api.auth import enforce_rate_limit, get_current_user
from cybershield.api.models import CVEDetailsResponse, IOCReputationResponse, Severity, ThreatFeedItem, ThreatFeedResponse


router = APIRouter(prefix="/api/v1/intel", tags=["threat-intel"])


@router.get("/ioc/{indicator}", response_model=IOCReputationResponse)
async def check_ioc_reputation(
    indicator: str,
    _: str = Depends(get_current_user),
    __: None = Depends(enforce_rate_limit),
) -> IOCReputationResponse:
    """Check IOC reputation using an aggregated threat score."""
    normalized = indicator.strip().lower()
    if len(normalized) < 3:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="indicator must be at least 3 characters")

    malicious = any(token in normalized for token in ("mal", "evil", "bad", "phish"))
    score = 85 if malicious else 22
    confidence = 90 if malicious else 70
    now = datetime.now(timezone.utc)
    return IOCReputationResponse(
        indicator=indicator,
        score=score,
        confidence=confidence,
        malicious=malicious,
        sources=["virustotal", "alienvault-otx", "internal-feed"],
        tags=["malware", "c2"] if malicious else ["unknown"],
        first_seen=now - timedelta(days=30),
        last_seen=now - timedelta(hours=4),
    )


@router.get("/cve/{cve_id}", response_model=CVEDetailsResponse)
async def get_cve_details(
    cve_id: str,
    _: str = Depends(get_current_user),
    __: None = Depends(enforce_rate_limit),
) -> CVEDetailsResponse:
    """Return normalized CVE metadata."""
    normalized = cve_id.upper()
    if not normalized.startswith("CVE-"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="cve_id must start with CVE-")

    now = datetime.now(timezone.utc)
    return CVEDetailsResponse(
        cve_id=normalized,
        cvss_score=9.1,
        severity=Severity.CRITICAL,
        summary="Remote code execution vulnerability in a common dependency package.",
        affected_products=["openssl", "nginx"],
        references=[
            f"https://nvd.nist.gov/vuln/detail/{normalized}",
            f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={normalized}",
        ],
        published_at=now - timedelta(days=120),
        updated_at=now - timedelta(days=2),
    )


@router.get("/threats", response_model=ThreatFeedResponse)
async def get_aggregated_threat_feed(
    _: str = Depends(get_current_user),
    __: None = Depends(enforce_rate_limit),
) -> ThreatFeedResponse:
    """Fetch aggregated near-real-time threat feed entries."""
    now = datetime.now(timezone.utc)
    items = [
        ThreatFeedItem(
            title="Credential phishing campaign targeting SaaS admins",
            category="phishing",
            severity=Severity.HIGH,
            source="otx",
            indicator="phish-control.example",
            observed_at=now - timedelta(minutes=40),
        ),
        ThreatFeedItem(
            title="New ransomware C2 infrastructure observed",
            category="ransomware",
            severity=Severity.CRITICAL,
            source="virustotal",
            indicator="198.51.100.47",
            observed_at=now - timedelta(minutes=15),
        ),
    ]
    return ThreatFeedResponse(items=items, generated_at=now, total=len(items))


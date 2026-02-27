"""Tests for threat intelligence aggregation module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.intelligence.aggregator import ThreatIntelligenceAggregator
from src.intelligence.correlator import ThreatCorrelator
from src.intelligence.feeds.cve import CVEClient
from src.intelligence.models import (
    AttackTechnique,
    FeedResult,
    Indicator,
    IndicatorType,
    IntelligenceConfig,
    MissingAPIKeyError,
    RateLimitError,
    ThreatActorProfile,
    VulnerabilityRecord,
)


class FakeMITREClient:
    def map_indicator_to_techniques(self, indicator: Indicator):
        return [
            AttackTechnique(
                technique_id="T1071",
                name="Application Layer Protocol",
                tactic="command-and-control",
            )
        ]

    def lookup_actor(self, name: str):
        return ThreatActorProfile(
            name=name,
            aliases=["Fancy Bear"],
            description="Known intrusion set",
            techniques=["T1071"],
            source="mitre",
        )


class FakeCVEClient:
    def lookup(self, cve_id: str):
        return VulnerabilityRecord(cve_id=cve_id, summary="Test vuln", cvss_score=8.8, severity="HIGH")


class FakeAbuseIPDBClient:
    def check_ip(self, ip: str):
        now = datetime.now(timezone.utc)
        return Indicator(
            value=ip,
            type=IndicatorType.IP,
            source="abuseipdb",
            confidence=0.8,
            reputation_score=85,
            first_seen=now - timedelta(days=2),
            last_seen=now - timedelta(days=1),
            metadata={
                "mitre_techniques": ["T1071"],
                "cve_ids": ["CVE-2024-1234"],
                "threat_actors": ["APT28"],
            },
        )


class FakeVirusTotalClient:
    def check_indicator(self, value: str, indicator_type: IndicatorType):
        now = datetime.now(timezone.utc)
        return Indicator(
            value=value,
            type=indicator_type,
            source="virustotal",
            confidence=0.7,
            reputation_score=70,
            first_seen=now - timedelta(days=3),
            last_seen=now,
            metadata={"mitre_techniques": ["T1071"], "cve_ids": ["CVE-2024-1234"]},
        )


class FakeOTXClient:
    def check_indicator(self, value: str, indicator_type: IndicatorType):
        now = datetime.now(timezone.utc)
        return Indicator(
            value=value,
            type=indicator_type,
            source="alienvault_otx",
            confidence=0.6,
            reputation_score=60,
            first_seen=now - timedelta(days=4),
            last_seen=now,
            metadata={"threat_actors": ["APT28"]},
        )


def test_aggregator_collects_and_correlates_across_feeds():
    config = IntelligenceConfig(
        abuseipdb_api_key="abuse-key",
        virustotal_api_key="vt-key",
        alienvault_otx_api_key="otx-key",
    )
    aggregator = ThreatIntelligenceAggregator(
        config=config,
        mitre_client=FakeMITREClient(),
        cve_client=FakeCVEClient(),
        abuseipdb_client=FakeAbuseIPDBClient(),
        virustotal_client=FakeVirusTotalClient(),
        otx_client=FakeOTXClient(),
    )

    indicator = Indicator(value="1.2.3.4", type=IndicatorType.IP, source="input")
    custom_feed = FeedResult(
        source="custom",
        indicators=[
            Indicator(
                value="1.2.3.4",
                type=IndicatorType.IP,
                source="custom",
                confidence=0.9,
                reputation_score=65,
            )
        ],
    )

    report = aggregator.aggregate(
        [indicator],
        cve_ids=["CVE-2024-1234"],
        actor_names=["APT28"],
        custom_ioc_feeds=[custom_feed],
    )

    assert len(report.raw_results) == 7
    assert report.errors == []
    assert len(report.correlated_threats) >= 1

    correlated = report.correlated_threats[0]
    assert correlated.indicator.value == "1.2.3.4"
    assert set(correlated.sources) >= {"abuseipdb", "virustotal", "alienvault_otx", "custom"}
    assert {v.cve_id for v in correlated.linked_vulnerabilities} == {"CVE-2024-1234"}
    assert {t.technique_id for t in correlated.linked_techniques} == {"T1071"}
    assert {a.name for a in correlated.linked_actors} == {"APT28"}
    assert correlated.threat_score > 0


def test_correlator_deduplicates_and_applies_time_decay():
    config = IntelligenceConfig(stale_decay_days=10)
    correlator = ThreatCorrelator(config)
    now = datetime.now(timezone.utc)
    old_seen = now - timedelta(days=30)

    result_a = FeedResult(
        source="feed_a",
        indicators=[
            Indicator(
                value="bad.example",
                type=IndicatorType.DOMAIN,
                source="feed_a",
                confidence=0.9,
                reputation_score=90,
                first_seen=old_seen,
                last_seen=old_seen,
            )
        ],
    )
    result_b = FeedResult(
        source="feed_b",
        indicators=[
            Indicator(
                value="BAD.EXAMPLE",
                type=IndicatorType.DOMAIN,
                source="feed_b",
                confidence=0.8,
                reputation_score=80,
                first_seen=old_seen,
                last_seen=old_seen,
            )
        ],
    )

    correlated = correlator.correlate([result_a, result_b], now=now)

    assert len(correlated) == 1
    threat = correlated[0]
    assert threat.indicator.value == "bad.example"
    assert set(threat.sources) == {"feed_a", "feed_b"}
    assert threat.decay_factor < 0.1
    assert threat.confidence_score < 0.2
    assert threat.threat_score < 40


def test_cve_client_cache_and_rate_limit():
    call_count = {"value": 0}

    def provider(params):
        call_count["value"] += 1
        cve_id = params.get("cveId")
        return {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": cve_id,
                        "descriptions": [{"lang": "en", "value": "Sample"}],
                        "metrics": {
                            "cvssMetricV31": [
                                {
                                    "cvssData": {"baseScore": 9.0, "baseSeverity": "CRITICAL"},
                                }
                            ]
                        },
                        "references": [{"url": "https://example.com"}],
                    }
                }
            ]
        }

    config = IntelligenceConfig(rate_limit_per_minute=1, cache_ttl_seconds=600)
    client = CVEClient(config, response_provider=provider)

    first = client.lookup("CVE-2024-0001")
    second = client.lookup("CVE-2024-0001")

    assert first is not None
    assert second is not None
    assert call_count["value"] == 1

    with pytest.raises(RateLimitError) as exc_info:
        client.lookup("CVE-2024-0002")
    assert "Rate limit exceeded" in str(exc_info.value)


def test_aggregator_collects_feed_errors_without_crashing():
    class FailingAbuse:
        def check_ip(self, ip):
            raise MissingAPIKeyError("missing abuse key")

    class FailingVT:
        def check_indicator(self, value, indicator_type):
            raise MissingAPIKeyError("missing vt key")

    class FailingOTX:
        def check_indicator(self, value, indicator_type):
            raise MissingAPIKeyError("missing otx key")

    class EmptyMITRE:
        def map_indicator_to_techniques(self, indicator):
            return []

        def lookup_actor(self, name):
            return None

    config = IntelligenceConfig()
    aggregator = ThreatIntelligenceAggregator(
        config=config,
        mitre_client=EmptyMITRE(),
        cve_client=FakeCVEClient(),
        abuseipdb_client=FailingAbuse(),
        virustotal_client=FailingVT(),
        otx_client=FailingOTX(),
    )

    report = aggregator.aggregate([Indicator(value="5.6.7.8", type=IndicatorType.IP, source="input")])

    assert len(report.errors) == 3
    assert any("missing abuse key" in err for err in report.errors)
    assert any("missing vt key" in err for err in report.errors)
    assert any("missing otx key" in err for err in report.errors)

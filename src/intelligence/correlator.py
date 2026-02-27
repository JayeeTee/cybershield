"""Cross-feed correlation, deduplication, and scoring engine."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from .models import (
    AttackTechnique,
    CorrelatedThreat,
    FeedResult,
    Indicator,
    IntelligenceConfig,
    ThreatActorProfile,
    VulnerabilityRecord,
)


def _normalize_indicator_key(indicator: Indicator) -> str:
    value = indicator.value.lower() if indicator.type.value in {"domain", "hash"} else indicator.value
    return f"{indicator.type.value}:{value}"


class ThreatCorrelator:
    """Correlates and scores threat data across feed outputs."""

    def __init__(self, config: IntelligenceConfig) -> None:
        self.config = config

    def correlate(self, feed_results: list[FeedResult], now: datetime | None = None) -> list[CorrelatedThreat]:
        current_time = now or datetime.now(timezone.utc)
        grouped: dict[str, list[tuple[str, Indicator]]] = {}

        for result in feed_results:
            for indicator in result.indicators:
                key = _normalize_indicator_key(indicator)
                grouped.setdefault(key, []).append((result.source, indicator))

        correlated: list[CorrelatedThreat] = []
        for key, entries in grouped.items():
            sources = sorted({source for source, _ in entries})
            representative = self._merge_indicators([indicator for _, indicator in entries])
            linked_techniques = self._collect_techniques(feed_results, representative)
            linked_vulns = self._collect_vulnerabilities(feed_results, representative)
            linked_actors = self._collect_actors(feed_results, representative)

            decay_factor = self._compute_decay(representative.last_seen, current_time)
            confidence = self._confidence_score(entries, decay_factor)
            threat_score = self._threat_score(representative, confidence)

            correlated.append(
                CorrelatedThreat(
                    indicator=representative,
                    sources=sources,
                    linked_techniques=linked_techniques,
                    linked_vulnerabilities=linked_vulns,
                    linked_actors=linked_actors,
                    confidence_score=confidence,
                    decay_factor=decay_factor,
                    threat_score=threat_score,
                )
            )

        correlated.sort(key=lambda item: item.threat_score, reverse=True)
        return correlated

    def _merge_indicators(self, indicators: list[Indicator]) -> Indicator:
        base = indicators[0].model_copy(deep=True)
        base.first_seen = min(i.first_seen for i in indicators)
        base.last_seen = max(i.last_seen for i in indicators)
        base.reputation_score = max(i.reputation_score for i in indicators)
        base.confidence = min(1.0, sum(i.confidence for i in indicators) / len(indicators))
        tags = set()
        merged_metadata = dict(base.metadata)
        for indicator in indicators:
            tags.update(indicator.tags)
            merged_metadata.update(indicator.metadata)
        base.tags = sorted(tags)
        base.metadata = merged_metadata
        return base

    def _collect_techniques(self, results: list[FeedResult], indicator: Indicator) -> list[AttackTechnique]:
        wanted_ids = set(indicator.metadata.get("mitre_techniques", []))
        techniques: dict[str, AttackTechnique] = {}
        for result in results:
            for technique in result.techniques:
                if wanted_ids and technique.technique_id not in wanted_ids:
                    continue
                techniques[technique.technique_id] = technique
        return list(techniques.values())

    def _collect_vulnerabilities(self, results: list[FeedResult], indicator: Indicator) -> list[VulnerabilityRecord]:
        wanted_cves = set(indicator.metadata.get("cve_ids", []))
        vulnerabilities: dict[str, VulnerabilityRecord] = {}
        for result in results:
            for vuln in result.vulnerabilities:
                if wanted_cves and vuln.cve_id not in wanted_cves:
                    continue
                vulnerabilities[vuln.cve_id] = vuln
        return list(vulnerabilities.values())

    def _collect_actors(self, results: list[FeedResult], indicator: Indicator) -> list[ThreatActorProfile]:
        wanted_actor_names = set(indicator.metadata.get("threat_actors", []))
        actors: dict[str, ThreatActorProfile] = {}
        for result in results:
            for actor in result.threat_actors:
                if wanted_actor_names and actor.name not in wanted_actor_names:
                    continue
                actors[actor.name] = actor
        return list(actors.values())

    def _compute_decay(self, last_seen: datetime, now: datetime) -> float:
        age_days = max(0.0, (now - last_seen).total_seconds() / 86400.0)
        decay_days = max(1, self.config.stale_decay_days)
        return math.exp(-age_days / decay_days)

    def _confidence_score(self, entries: list[tuple[str, Indicator]], decay_factor: float) -> float:
        indicators = [indicator for _, indicator in entries]
        avg_confidence = sum(item.confidence for item in indicators) / len(indicators)
        source_boost = min(0.3, 0.1 * (len({src for src, _ in entries}) - 1))
        return max(0.0, min(1.0, (avg_confidence + source_boost) * decay_factor))

    @staticmethod
    def _threat_score(indicator: Indicator, confidence: float) -> int:
        return int(max(0, min(100, (indicator.reputation_score * 0.6) + (confidence * 40))))

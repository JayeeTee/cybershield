"""Threat intelligence aggregation pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from .correlator import ThreatCorrelator
from .feeds.abuseipdb import AbuseIPDBClient
from .feeds.cve import CVEClient
from .feeds.mitre import MITREAttackClient
from .feeds.otx import AlienVaultOTXClient
from .feeds.virustotal import VirusTotalClient
from .models import (
    FeedResult,
    Indicator,
    IndicatorType,
    IntelligenceConfig,
    IntelligenceReport,
    IntelligenceError,
)


class ThreatIntelligenceAggregator:
    """Aggregates indicators from external feeds and correlates findings."""

    def __init__(
        self,
        config: IntelligenceConfig | None = None,
        *,
        mitre_client: MITREAttackClient | None = None,
        cve_client: CVEClient | None = None,
        abuseipdb_client: AbuseIPDBClient | None = None,
        virustotal_client: VirusTotalClient | None = None,
        otx_client: AlienVaultOTXClient | None = None,
        correlator: ThreatCorrelator | None = None,
    ) -> None:
        self.config = config or IntelligenceConfig()
        self.mitre_client = mitre_client or MITREAttackClient(self.config)
        self.cve_client = cve_client or CVEClient(self.config)
        self.abuseipdb_client = abuseipdb_client or AbuseIPDBClient(self.config)
        self.virustotal_client = virustotal_client or VirusTotalClient(self.config)
        self.otx_client = otx_client or AlienVaultOTXClient(self.config)
        self.correlator = correlator or ThreatCorrelator(self.config)

    def aggregate(
        self,
        indicators: Iterable[Indicator],
        *,
        cve_ids: Iterable[str] | None = None,
        actor_names: Iterable[str] | None = None,
        custom_ioc_feeds: Iterable[FeedResult] | None = None,
    ) -> IntelligenceReport:
        report = IntelligenceReport()
        indicator_list = list(indicators)

        if indicator_list:
            report.raw_results.extend(self._collect_reputation(indicator_list))
            report.raw_results.extend(self._collect_mitre_mappings(indicator_list))

        if cve_ids:
            report.raw_results.append(self._collect_cve_data(list(cve_ids)))

        if actor_names:
            report.raw_results.append(self._collect_actor_profiles(list(actor_names)))

        if custom_ioc_feeds:
            report.raw_results.extend(list(custom_ioc_feeds))

        for result in report.raw_results:
            report.errors.extend(result.errors)

        report.correlated_threats = self.correlator.correlate(report.raw_results)
        report.generated_at = datetime.now(timezone.utc)
        return report

    def _collect_reputation(self, indicators: list[Indicator]) -> list[FeedResult]:
        abuse_result = FeedResult(source="abuseipdb")
        vt_result = FeedResult(source="virustotal")
        otx_result = FeedResult(source="alienvault_otx")

        for indicator in indicators:
            if indicator.type == IndicatorType.IP:
                self._safe_collect(
                    abuse_result,
                    lambda ind=indicator: abuse_result.indicators.append(self.abuseipdb_client.check_ip(ind.value)),
                )
            self._safe_collect(
                vt_result,
                lambda ind=indicator: vt_result.indicators.append(
                    self.virustotal_client.check_indicator(ind.value, ind.type)
                ),
            )
            self._safe_collect(
                otx_result,
                lambda ind=indicator: otx_result.indicators.append(self.otx_client.check_indicator(ind.value, ind.type)),
            )

        return [abuse_result, vt_result, otx_result]

    def _collect_mitre_mappings(self, indicators: list[Indicator]) -> list[FeedResult]:
        mitre_result = FeedResult(source="mitre")
        for indicator in indicators:
            self._safe_collect(
                mitre_result,
                lambda ind=indicator: mitre_result.techniques.extend(self.mitre_client.map_indicator_to_techniques(ind)),
            )
        return [mitre_result]

    def _collect_cve_data(self, cve_ids: list[str]) -> FeedResult:
        cve_result = FeedResult(source="cve")
        for cve_id in cve_ids:
            self._safe_collect(
                cve_result,
                lambda cid=cve_id: self._append_if_not_none(cve_result, self.cve_client.lookup(cid)),
            )
        return cve_result

    def _collect_actor_profiles(self, actor_names: list[str]) -> FeedResult:
        actor_result = FeedResult(source="mitre_actors")
        for actor_name in actor_names:
            self._safe_collect(
                actor_result,
                lambda name=actor_name: self._append_actor_if_not_none(actor_result, self.mitre_client.lookup_actor(name)),
            )
        return actor_result

    @staticmethod
    def _append_if_not_none(result: FeedResult, vulnerability) -> None:
        if vulnerability is not None:
            result.vulnerabilities.append(vulnerability)

    @staticmethod
    def _append_actor_if_not_none(result: FeedResult, actor) -> None:
        if actor is not None:
            result.threat_actors.append(actor)

    @staticmethod
    def _safe_collect(result: FeedResult, op) -> None:
        try:
            op()
        except IntelligenceError as exc:
            result.errors.append(str(exc))
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"unexpected feed error: {exc}")

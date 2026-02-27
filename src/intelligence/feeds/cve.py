"""NVD CVE API integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import VulnerabilityRecord
from .base import BaseFeedClient


class CVEClient(BaseFeedClient):
    """Client for CVE lookups via NVD API v2."""

    source_name = "cve"

    def __init__(self, config, response_provider=None) -> None:
        super().__init__(config)
        self._response_provider = response_provider

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _query(self, params: dict[str, Any]) -> dict[str, Any]:
        if self._response_provider is not None:
            return self._response_provider(params)
        return self._request_json(url=self.config.cve_api_url, params=params)

    def lookup(self, cve_id: str) -> VulnerabilityRecord | None:
        key = f"cve:{cve_id.lower()}"

        def fetch() -> VulnerabilityRecord | None:
            payload = self._query({"cveId": cve_id})
            vulnerabilities = payload.get("vulnerabilities", [])
            if not vulnerabilities:
                return None
            return self._normalize(vulnerabilities[0].get("cve", {}))

        return self._cached(key, fetch)

    def search(self, keyword: str, limit: int = 10) -> list[VulnerabilityRecord]:
        key = f"cve:search:{keyword.lower()}:{limit}"

        def fetch() -> list[VulnerabilityRecord]:
            payload = self._query({"keywordSearch": keyword, "resultsPerPage": limit})
            vulnerabilities = payload.get("vulnerabilities", [])
            return [self._normalize(item.get("cve", {})) for item in vulnerabilities[:limit]]

        return self._cached(key, fetch)

    def _normalize(self, cve_data: dict[str, Any]) -> VulnerabilityRecord:
        cve_id = cve_data.get("id", "UNKNOWN")
        descriptions = cve_data.get("descriptions", [])
        summary = next((d.get("value") for d in descriptions if d.get("lang") == "en"), None)

        metrics = cve_data.get("metrics", {})
        cvss_score = None
        severity = None
        for metric_name in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            entries = metrics.get(metric_name)
            if not entries:
                continue
            first = entries[0]
            cvss_data = first.get("cvssData", {})
            cvss_score = cvss_data.get("baseScore")
            severity = cvss_data.get("baseSeverity") or first.get("baseSeverity")
            break

        references = [ref.get("url") for ref in cve_data.get("references", []) if ref.get("url")]

        return VulnerabilityRecord(
            cve_id=cve_id,
            summary=summary,
            cvss_score=cvss_score,
            severity=severity,
            published=self._parse_datetime(cve_data.get("published")),
            modified=self._parse_datetime(cve_data.get("lastModified")),
            references=references,
        )

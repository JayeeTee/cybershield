"""VirusTotal reputation feed integration."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

from ..models import Indicator, IndicatorType, MissingAPIKeyError
from .base import BaseFeedClient


class VirusTotalClient(BaseFeedClient):
    """Client for VirusTotal v3 API."""

    source_name = "virustotal"
    base_url = "https://www.virustotal.com/api/v3"

    def check_indicator(self, value: str, indicator_type: IndicatorType) -> Indicator:
        if not self.config.virustotal_api_key:
            raise MissingAPIKeyError("VirusTotal API key is missing")

        key = f"vt:{indicator_type.value}:{value}"

        def fetch() -> Indicator:
            path_map = {
                IndicatorType.IP: "ip_addresses",
                IndicatorType.DOMAIN: "domains",
                IndicatorType.HASH: "files",
            }
            endpoint = path_map[indicator_type]
            payload = self._request_json(
                url=f"{self.base_url}/{endpoint}/{quote(value, safe='')}",
                headers={"x-apikey": self.config.virustotal_api_key},
            )
            attrs = payload.get("data", {}).get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            malicious = int(stats.get("malicious", 0))
            suspicious = int(stats.get("suspicious", 0))
            total = max(1, sum(int(v) for v in stats.values()))
            score = int(((malicious + suspicious) / total) * 100)
            return Indicator(
                value=value,
                type=indicator_type,
                source=self.source_name,
                confidence=min(1.0, (malicious + suspicious) / total),
                reputation_score=score,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                tags=["virustotal"],
                metadata={
                    "analysis_stats": stats,
                    "reputation": attrs.get("reputation", 0),
                    "last_analysis_date": attrs.get("last_analysis_date"),
                },
            )

        return self._cached(key, fetch)

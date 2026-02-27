"""AbuseIPDB reputation feed integration."""

from __future__ import annotations

from datetime import datetime, timezone

from ..models import Indicator, IndicatorType, MissingAPIKeyError
from .base import BaseFeedClient


class AbuseIPDBClient(BaseFeedClient):
    """Client for AbuseIPDB indicator reputation checks."""

    source_name = "abuseipdb"
    base_url = "https://api.abuseipdb.com/api/v2/check"

    def check_ip(self, ip: str, max_age_days: int = 90) -> Indicator:
        if not self.config.abuseipdb_api_key:
            raise MissingAPIKeyError("AbuseIPDB API key is missing")

        key = f"abuseipdb:{ip}:{max_age_days}"

        def fetch() -> Indicator:
            payload = self._request_json(
                url=self.base_url,
                params={"ipAddress": ip, "maxAgeInDays": max_age_days, "verbose": ""},
                headers={"Key": self.config.abuseipdb_api_key, "Accept": "application/json"},
            )
            data = payload.get("data", {})
            score = int(data.get("abuseConfidenceScore", 0))
            usage_type = data.get("usageType")
            return Indicator(
                value=ip,
                type=IndicatorType.IP,
                source=self.source_name,
                confidence=min(1.0, score / 100.0),
                reputation_score=score,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                tags=[tag for tag in ["abuseipdb", usage_type] if tag],
                metadata={
                    "country_code": data.get("countryCode"),
                    "isp": data.get("isp"),
                    "total_reports": data.get("totalReports", 0),
                },
            )

        return self._cached(key, fetch)

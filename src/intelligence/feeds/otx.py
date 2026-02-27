"""AlienVault OTX integration."""

from __future__ import annotations

from datetime import datetime, timezone

from ..models import Indicator, IndicatorType, MissingAPIKeyError
from .base import BaseFeedClient


class AlienVaultOTXClient(BaseFeedClient):
    """Client for AlienVault OTX indicator checks."""

    source_name = "alienvault_otx"
    base_url = "https://otx.alienvault.com/api/v1/indicators"

    def check_indicator(self, value: str, indicator_type: IndicatorType) -> Indicator:
        if not self.config.alienvault_otx_api_key:
            raise MissingAPIKeyError("AlienVault OTX API key is missing")

        key = f"otx:{indicator_type.value}:{value}"

        def fetch() -> Indicator:
            type_map = {
                IndicatorType.IP: "IPv4",
                IndicatorType.DOMAIN: "domain",
                IndicatorType.HASH: "file",
            }
            otx_type = type_map[indicator_type]
            payload = self._request_json(
                url=f"{self.base_url}/{otx_type}/{value}/general",
                headers={"X-OTX-API-KEY": self.config.alienvault_otx_api_key},
            )
            pulse_info = payload.get("pulse_info", {})
            pulses = pulse_info.get("pulses", [])
            score = min(100, len(pulses) * 10)
            tags = set(["otx"])
            for pulse in pulses:
                for tag in pulse.get("tags", []):
                    tags.add(tag)
            return Indicator(
                value=value,
                type=indicator_type,
                source=self.source_name,
                confidence=min(1.0, score / 100.0),
                reputation_score=score,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                tags=sorted(tags),
                metadata={
                    "pulse_count": len(pulses),
                    "malware_families": payload.get("malware_families", []),
                    "countries": payload.get("country_code"),
                },
            )

        return self._cached(key, fetch)

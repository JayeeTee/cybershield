"""MITRE ATT&CK feed integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import AttackTechnique, FeedClientError, Indicator, ThreatActorProfile
from .base import BaseFeedClient


class MITREAttackClient(BaseFeedClient):
    """Client for MITRE ATT&CK enterprise dataset."""

    source_name = "mitre"

    def __init__(self, config, dataset_provider=None) -> None:
        super().__init__(config)
        self._dataset_provider = dataset_provider

    def _load_dataset(self) -> dict[str, Any]:
        def fetch() -> dict[str, Any]:
            if self._dataset_provider is not None:
                return self._dataset_provider()
            return self._request_json(url=self.config.mitre_attack_url)

        return self._cached("mitre:dataset", fetch)

    def search_techniques(self, query: str | None = None, limit: int = 25) -> list[AttackTechnique]:
        dataset = self._load_dataset()
        objects = dataset.get("objects", [])
        needle = (query or "").strip().lower()
        results: list[AttackTechnique] = []

        for obj in objects:
            if obj.get("type") != "attack-pattern" or obj.get("revoked"):
                continue
            name = obj.get("name", "")
            description = obj.get("description", "")
            if needle and needle not in name.lower() and needle not in description.lower():
                continue
            ext_refs = obj.get("external_references", [])
            technique_id = None
            for ref in ext_refs:
                if ref.get("source_name") == "mitre-attack":
                    technique_id = ref.get("external_id")
                    break
            if not technique_id:
                continue
            kill_chain = obj.get("kill_chain_phases", [])
            tactic = kill_chain[0]["phase_name"] if kill_chain else None
            results.append(
                AttackTechnique(
                    technique_id=technique_id,
                    name=name,
                    tactic=tactic,
                    description=description,
                    metadata={"mitre_id": obj.get("id")},
                )
            )
            if len(results) >= limit:
                break
        return results

    def map_indicator_to_techniques(self, indicator: Indicator, limit: int = 10) -> list[AttackTechnique]:
        search_query = indicator.value if indicator.type.value == "domain" else "command and control"
        return self.search_techniques(search_query, limit=limit)

    def lookup_actor(self, actor_name: str) -> ThreatActorProfile | None:
        dataset = self._load_dataset()
        objects = dataset.get("objects", [])
        needle = actor_name.strip().lower()

        for obj in objects:
            if obj.get("type") != "intrusion-set" or obj.get("revoked"):
                continue
            name = obj.get("name", "")
            aliases = obj.get("aliases", [])
            candidates = [name.lower(), *[alias.lower() for alias in aliases]]
            if needle not in candidates:
                continue
            modified = obj.get("modified")
            try:
                known_targets = [datetime.fromisoformat(modified.replace("Z", "+00:00")).date().isoformat()] if modified else []
            except ValueError as exc:
                raise FeedClientError(f"mitre actor parsing failed: {exc}") from exc
            return ThreatActorProfile(
                name=name,
                aliases=aliases,
                description=obj.get("description"),
                motivation=[],
                techniques=[],
                known_targets=known_targets,
                source="mitre",
            )
        return None

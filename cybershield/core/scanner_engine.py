"""Core scanner engine abstractions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class ScannerEngine:
    """Minimal scanner orchestrator used by tests and API integrations."""

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def health(self) -> dict[str, str]:
        return {"status": "ok"}

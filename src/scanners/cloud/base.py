"""Abstract base scanner for cloud providers."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Callable, TypeVar

from .models import CloudFinding, CloudProvider, ComplianceIssue, ScanReport, Severity

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CloudScannerBase(ABC):
    """Base class that standardizes scanning flow and error handling."""

    def __init__(self, provider: CloudProvider) -> None:
        self.provider = provider

    @abstractmethod
    def scan(self) -> ScanReport:
        """Run cloud provider security scan and return report."""

    def _new_report(self) -> ScanReport:
        now = datetime.now(timezone.utc)
        return ScanReport(provider=self.provider, started_at=now, completed_at=now)

    def _complete_report(self, report: ScanReport) -> ScanReport:
        report.completed_at = datetime.now(timezone.utc)
        return report

    def _run_check(self, report: ScanReport, name: str, check: Callable[[], list[CloudFinding]]) -> None:
        try:
            findings = check()
            report.findings.extend(findings)
            logger.debug("%s: check '%s' yielded %d findings", self.provider.value, name, len(findings))
        except Exception as exc:  # noqa: BLE001
            message = f"{self.provider.value}:{name} failed: {exc}"
            logger.exception(message)
            report.errors.append(message)

    def _make_finding(
        self,
        *,
        finding_id: str,
        severity: Severity,
        title: str,
        description: str,
        resource_id: str,
        resource_type: str,
        region: str | None = None,
        recommendation: str | None = None,
        compliance_issues: list[ComplianceIssue] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> CloudFinding:
        return CloudFinding(
            finding_id=finding_id,
            provider=self.provider,
            severity=severity,
            title=title,
            description=description,
            resource_id=resource_id,
            resource_type=resource_type,
            region=region,
            recommendation=recommendation,
            compliance_issues=compliance_issues or [],
            metadata=metadata or {},
        )

"""Container image vulnerability and posture scanner."""

from __future__ import annotations

import json
import logging
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable

from .models import (
    CVEMetadata,
    ComplianceIssue,
    ContainerFinding,
    ContainerScanReport,
    ContainerSeverity,
    FindingCategory,
    ScannerBackend,
)

logger = logging.getLogger(__name__)

try:
    import docker
except Exception:  # noqa: BLE001
    docker = None

CommandRunner = Callable[[list[str]], tuple[int, str, str]]


def _cis(control_id: str, description: str) -> ComplianceIssue:
    return ComplianceIssue(framework="CIS Docker Benchmark", control_id=control_id, description=description)


def _default_runner(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


class CVEDatabase:
    """Very small CVE enrichment layer with optional external provider."""

    def __init__(self, provider: Callable[[str], CVEMetadata | None] | None = None) -> None:
        self.provider = provider
        self._builtins: dict[str, CVEMetadata] = {
            "CVE-2021-44228": CVEMetadata(
                cve_id="CVE-2021-44228",
                cvss_score=10.0,
                severity=ContainerSeverity.CRITICAL,
                description="Log4j JNDI lookup remote code execution vulnerability.",
                references=["https://nvd.nist.gov/vuln/detail/CVE-2021-44228"],
                remediation="Upgrade log4j-core to 2.17.1 or newer.",
            ),
            "CVE-2023-38545": CVEMetadata(
                cve_id="CVE-2023-38545",
                cvss_score=9.8,
                severity=ContainerSeverity.CRITICAL,
                description="curl SOCKS5 heap buffer overflow vulnerability.",
                references=["https://nvd.nist.gov/vuln/detail/CVE-2023-38545"],
                remediation="Upgrade curl to a fixed release from your distribution.",
            ),
        }

    def lookup(self, cve_id: str) -> CVEMetadata | None:
        if self.provider:
            try:
                enriched = self.provider(cve_id)
                if enriched:
                    return enriched
            except Exception:  # noqa: BLE001
                logger.exception("external CVE provider failed for %s", cve_id)
        return self._builtins.get(cve_id)


class ImageScanner:
    """Scanner for image vulnerabilities, base image posture, and image layers."""

    def __init__(
        self,
        *,
        command_runner: CommandRunner | None = None,
        docker_client: Any | None = None,
        cve_database: CVEDatabase | None = None,
    ) -> None:
        self.command_runner = command_runner or _default_runner
        self.docker_client = docker_client
        self.cve_database = cve_database or CVEDatabase()

        if self.docker_client is None and docker is not None:
            try:
                self.docker_client = docker.from_env()
            except Exception:  # noqa: BLE001
                self.docker_client = None

    def scan(self, image_ref: str) -> ContainerScanReport:
        now = datetime.now(timezone.utc)
        report = ContainerScanReport(scanner_name="image-scanner", target=image_ref, started_at=now, completed_at=now)

        backend = ScannerBackend.CUSTOM
        findings: list[ContainerFinding] = []

        try:
            findings = self._scan_with_trivy(image_ref)
            if findings:
                backend = ScannerBackend.TRIVY
            else:
                findings = self._scan_with_grype(image_ref)
                if findings:
                    backend = ScannerBackend.GRYPE
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"vulnerability scan failed: {exc}")

        if not findings:
            findings = self._custom_vulnerability_scan(image_ref)
            backend = ScannerBackend.CUSTOM

        for finding in findings:
            finding.scanner = backend
        report.findings.extend(findings)

        try:
            report.findings.extend(self._assess_base_image(image_ref))
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"base image assessment failed: {exc}")

        try:
            report.findings.extend(self._analyze_layers(image_ref))
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"layer analysis failed: {exc}")

        report.completed_at = datetime.now(timezone.utc)
        return report

    def _scan_with_trivy(self, image_ref: str) -> list[ContainerFinding]:
        rc, stdout, stderr = self.command_runner(["trivy", "image", "--format", "json", image_ref])
        if rc != 0:
            logger.debug("trivy failed for %s: %s", image_ref, stderr)
            return []

        parsed = json.loads(stdout)
        findings: list[ContainerFinding] = []

        for result in parsed.get("Results", []):
            target = result.get("Target", image_ref)
            for vuln in result.get("Vulnerabilities", []) or []:
                finding = self._make_vuln_finding(
                    image_ref=image_ref,
                    target=target,
                    cve_id=vuln.get("VulnerabilityID"),
                    package_name=vuln.get("PkgName"),
                    installed_version=vuln.get("InstalledVersion"),
                    fixed_version=vuln.get("FixedVersion"),
                    severity=vuln.get("Severity"),
                    description=vuln.get("Description") or vuln.get("Title") or "Vulnerability found",
                    cvss_score=self._extract_trivy_cvss(vuln),
                    references=[vuln.get("PrimaryURL")] if vuln.get("PrimaryURL") else [],
                )
                findings.append(finding)

        return findings

    def _scan_with_grype(self, image_ref: str) -> list[ContainerFinding]:
        rc, stdout, stderr = self.command_runner(["grype", image_ref, "-o", "json"])
        if rc != 0:
            logger.debug("grype failed for %s: %s", image_ref, stderr)
            return []

        parsed = json.loads(stdout)
        findings: list[ContainerFinding] = []

        for match in parsed.get("matches", []):
            artifact = match.get("artifact", {})
            vulnerability = match.get("vulnerability", {})
            finding = self._make_vuln_finding(
                image_ref=image_ref,
                target=artifact.get("location") or image_ref,
                cve_id=vulnerability.get("id"),
                package_name=artifact.get("name"),
                installed_version=artifact.get("version"),
                fixed_version=(vulnerability.get("fix", {}) or {}).get("versions", [None])[0],
                severity=vulnerability.get("severity"),
                description=vulnerability.get("description") or "Vulnerability found",
                cvss_score=self._extract_grype_cvss(vulnerability),
                references=vulnerability.get("urls", []) or [],
            )
            findings.append(finding)

        return findings

    def _custom_vulnerability_scan(self, image_ref: str) -> list[ContainerFinding]:
        tag = image_ref.split(":", 1)[1] if ":" in image_ref else "latest"
        if tag == "latest":
            return [
                ContainerFinding(
                    finding_id=f"image-custom-unpinned-{image_ref}",
                    category=FindingCategory.IMAGE,
                    severity=ContainerSeverity.MEDIUM,
                    title="Image tag is mutable",
                    description=(
                        f"Image '{image_ref}' uses a mutable tag. This increases supply-chain risk and "
                        "makes vulnerability tracking less deterministic."
                    ),
                    resource_id=image_ref,
                    resource_type="container:image",
                    recommendation="Pin image references to immutable digests (e.g., sha256:...).",
                    compliance_issues=[_cis("4.1", "Ensure container images are trusted and immutable")],
                )
            ]
        return []

    def _assess_base_image(self, image_ref: str) -> list[ContainerFinding]:
        findings: list[ContainerFinding] = []
        base_image = self._guess_base_image(image_ref)

        if image_ref.endswith(":latest") or ":" not in image_ref:
            findings.append(
                ContainerFinding(
                    finding_id=f"image-base-mutable-{image_ref}",
                    category=FindingCategory.IMAGE,
                    severity=ContainerSeverity.MEDIUM,
                    title="Base image version appears unpinned",
                    description=(
                        f"Image '{image_ref}' appears to use a mutable tag ({base_image}). "
                        "Pinned versions and digests improve security reproducibility."
                    ),
                    resource_id=image_ref,
                    resource_type="container:image",
                    recommendation="Use explicit image versions and sha256 digests in builds.",
                    compliance_issues=[_cis("4.1", "Ensure image tags are immutable and controlled")],
                )
            )

        eol_patterns = [r"ubuntu:1[46]\.04", r"debian:(jessie|stretch)", r"alpine:3\.(7|8|9)"]
        if any(re.search(pattern, base_image) for pattern in eol_patterns):
            findings.append(
                ContainerFinding(
                    finding_id=f"image-base-eol-{image_ref}",
                    category=FindingCategory.IMAGE,
                    severity=ContainerSeverity.HIGH,
                    title="Potential end-of-life base image detected",
                    description=f"Base image '{base_image}' appears out of support.",
                    resource_id=image_ref,
                    resource_type="container:image",
                    recommendation="Migrate to a supported LTS base image and rebuild.",
                    compliance_issues=[_cis("4.5", "Ensure base image receives security updates")],
                )
            )

        return findings

    def _analyze_layers(self, image_ref: str) -> list[ContainerFinding]:
        findings: list[ContainerFinding] = []

        for idx, layer in enumerate(self._get_layer_history(image_ref)):
            created_by = layer.get("CreatedBy", "") or ""
            size = int(layer.get("Size", 0) or 0)

            if size > 200 * 1024 * 1024:
                findings.append(
                    ContainerFinding(
                        finding_id=f"image-layer-size-{image_ref}-{idx}",
                        category=FindingCategory.IMAGE,
                        severity=ContainerSeverity.LOW,
                        title="Large image layer detected",
                        description=(
                            f"Layer {idx} is unusually large ({size} bytes), which can increase attack surface "
                            "and hide excessive package additions."
                        ),
                        resource_id=image_ref,
                        resource_type="container:image-layer",
                        recommendation="Reduce layer size and remove unnecessary packages/artifacts.",
                        metadata={"layer_index": idx, "created_by": created_by, "size": size},
                    )
                )

            if any(pattern in created_by for pattern in ["curl", "wget"]) and "|" in created_by:
                findings.append(
                    ContainerFinding(
                        finding_id=f"image-layer-pipe-{image_ref}-{idx}",
                        category=FindingCategory.IMAGE,
                        severity=ContainerSeverity.MEDIUM,
                        title="Remote script execution pattern in layer",
                        description=(
                            f"Layer {idx} command appears to download and pipe a script: '{created_by}'."
                        ),
                        resource_id=image_ref,
                        resource_type="container:image-layer",
                        recommendation="Avoid curl|bash patterns; verify artifacts and use signed packages.",
                        compliance_issues=[_cis("4.4", "Ensure software supply chain integrity")],
                        metadata={"layer_index": idx, "created_by": created_by},
                    )
                )

        return findings

    def _make_vuln_finding(
        self,
        *,
        image_ref: str,
        target: str,
        cve_id: str | None,
        package_name: str | None,
        installed_version: str | None,
        fixed_version: str | None,
        severity: str | None,
        description: str,
        cvss_score: float | None,
        references: list[str],
    ) -> ContainerFinding:
        cve_meta = self.cve_database.lookup(cve_id) if cve_id else None

        normalized_severity = self._normalize_severity(severity, cvss_score, cve_meta)
        normalized_cvss = cvss_score if cvss_score is not None else (cve_meta.cvss_score if cve_meta else None)
        recommendation = self._build_remediation(package_name, fixed_version, cve_meta)

        return ContainerFinding(
            finding_id=f"image-vuln-{cve_id or 'unknown'}-{package_name or 'pkg'}",
            category=FindingCategory.IMAGE,
            severity=normalized_severity,
            title=f"Vulnerability detected in {package_name or 'package'}",
            description=description if description else (cve_meta.description if cve_meta else "Vulnerability detected"),
            resource_id=image_ref,
            resource_type="container:image",
            cve_id=cve_id,
            package_name=package_name,
            installed_version=installed_version,
            fixed_version=fixed_version,
            cvss_score=normalized_cvss,
            recommendation=recommendation,
            metadata={"target": target, "references": references + ((cve_meta.references if cve_meta else []) or [])},
        )

    @staticmethod
    def _normalize_severity(
        severity: str | None,
        cvss_score: float | None,
        cve_meta: CVEMetadata | None,
    ) -> ContainerSeverity:
        if severity:
            value = severity.strip().lower()
            mapping = {
                "critical": ContainerSeverity.CRITICAL,
                "high": ContainerSeverity.HIGH,
                "medium": ContainerSeverity.MEDIUM,
                "low": ContainerSeverity.LOW,
                "negligible": ContainerSeverity.LOW,
                "unknown": ContainerSeverity.INFO,
            }
            if value in mapping:
                return mapping[value]

        if cve_meta and cve_meta.severity:
            return cve_meta.severity

        if cvss_score is not None:
            if cvss_score >= 9.0:
                return ContainerSeverity.CRITICAL
            if cvss_score >= 7.0:
                return ContainerSeverity.HIGH
            if cvss_score >= 4.0:
                return ContainerSeverity.MEDIUM
            if cvss_score > 0:
                return ContainerSeverity.LOW

        return ContainerSeverity.INFO

    @staticmethod
    def _build_remediation(package_name: str | None, fixed_version: str | None, cve_meta: CVEMetadata | None) -> str:
        if fixed_version:
            if package_name:
                return f"Upgrade {package_name} to {fixed_version} or newer."
            return f"Upgrade to a fixed version ({fixed_version}) or newer."
        if cve_meta and cve_meta.remediation:
            return cve_meta.remediation
        return "Apply vendor patches and rebuild image with the latest security updates."

    @staticmethod
    def _extract_trivy_cvss(vuln: dict[str, Any]) -> float | None:
        cvss = vuln.get("CVSS", {})
        for vendor in ("nvd", "redhat", "ghsa"):
            entry = cvss.get(vendor)
            if entry and entry.get("V3Score") is not None:
                return float(entry["V3Score"])
        if vuln.get("CVSSScore") is not None:
            return float(vuln["CVSSScore"])
        return None

    @staticmethod
    def _extract_grype_cvss(vuln: dict[str, Any]) -> float | None:
        scores = vuln.get("cvss", []) or []
        for entry in scores:
            metrics = entry.get("metrics", {})
            if metrics.get("baseScore") is not None:
                return float(metrics["baseScore"])
        return None

    @staticmethod
    def _guess_base_image(image_ref: str) -> str:
        if "@" in image_ref:
            return image_ref.split("@", 1)[0]
        return image_ref

    def _get_layer_history(self, image_ref: str) -> list[dict[str, Any]]:
        if self.docker_client is not None:
            try:
                # docker-py low-level API returns layer history with CreatedBy/Size fields.
                return self.docker_client.api.history(image_ref)
            except Exception:  # noqa: BLE001
                logger.debug("docker api history failed for %s", image_ref)

        rc, stdout, _ = self.command_runner(["docker", "history", image_ref, "--no-trunc", "--format", "{{json .}}"])
        if rc != 0 or not stdout.strip():
            return []

        layers: list[dict[str, Any]] = []
        for line in stdout.splitlines():
            try:
                item = json.loads(line)
                item["CreatedBy"] = item.get("CreatedBy", "")
                size_field = str(item.get("Size", "0"))
                item["Size"] = self._parse_size_to_bytes(size_field)
                layers.append(item)
            except json.JSONDecodeError:
                continue
        return layers

    @staticmethod
    def _parse_size_to_bytes(size_text: str) -> int:
        size_text = size_text.strip().lower().replace(" ", "")
        match = re.match(r"^(\d+(?:\.\d+)?)(b|kb|mb|gb)?$", size_text)
        if not match:
            return 0

        value = float(match.group(1))
        unit = match.group(2) or "b"
        factor = {"b": 1, "kb": 1024, "mb": 1024**2, "gb": 1024**3}[unit]
        return int(value * factor)

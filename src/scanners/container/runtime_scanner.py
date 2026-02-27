"""Runtime container security scanner."""

from __future__ import annotations

import logging
import re
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable

from .models import ComplianceIssue, ContainerFinding, ContainerScanReport, ContainerSeverity, FindingCategory

logger = logging.getLogger(__name__)

try:
    import docker
except Exception:  # noqa: BLE001
    docker = None

CommandRunner = Callable[[list[str]], tuple[int, str, str]]


def _default_runner(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _cis(control_id: str, description: str) -> ComplianceIssue:
    return ComplianceIssue(framework="CIS Docker Benchmark", control_id=control_id, description=description)


class RuntimeScanner:
    """Scanner for runtime container security and configuration."""

    def __init__(self, *, docker_client: Any | None = None, command_runner: CommandRunner | None = None) -> None:
        self.command_runner = command_runner or _default_runner
        self.docker_client = docker_client

        if self.docker_client is None and docker is not None:
            try:
                self.docker_client = docker.from_env()
            except Exception:  # noqa: BLE001
                self.docker_client = None

    def scan(self, container_id: str) -> ContainerScanReport:
        now = datetime.now(timezone.utc)
        report = ContainerScanReport(scanner_name="runtime-scanner", target=container_id, started_at=now, completed_at=now)

        try:
            inspect_data = self._inspect_container(container_id)
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"failed to inspect container {container_id}: {exc}")
            report.completed_at = datetime.now(timezone.utc)
            return report

        report.findings.extend(self._check_cis_configuration(container_id, inspect_data))
        report.findings.extend(self._check_privilege_escalation(container_id, inspect_data))
        report.findings.extend(self._check_network_policy(container_id, inspect_data))
        report.findings.extend(self._check_secret_mounts(container_id, inspect_data))

        report.completed_at = datetime.now(timezone.utc)
        return report

    def _inspect_container(self, container_id: str) -> dict[str, Any]:
        if self.docker_client is not None:
            container = self.docker_client.containers.get(container_id)
            return container.attrs

        raise RuntimeError("docker SDK unavailable; inject docker_client for runtime scanning")

    def _check_cis_configuration(self, container_id: str, data: dict[str, Any]) -> list[ContainerFinding]:
        findings: list[ContainerFinding] = []
        host = data.get("HostConfig", {})
        config = data.get("Config", {})

        if host.get("Privileged"):
            findings.append(
                ContainerFinding(
                    finding_id=f"runtime-privileged-{container_id}",
                    category=FindingCategory.RUNTIME,
                    severity=ContainerSeverity.CRITICAL,
                    title="Container runs in privileged mode",
                    description="Privileged containers effectively disable isolation boundaries.",
                    resource_id=container_id,
                    resource_type="container:runtime",
                    recommendation="Disable privileged mode and grant only required capabilities.",
                    compliance_issues=[_cis("5.2", "Ensure privileged containers are not used")],
                )
            )

        user = str(config.get("User", "")).strip()
        if not user or user == "root" or user == "0":
            findings.append(
                ContainerFinding(
                    finding_id=f"runtime-root-user-{container_id}",
                    category=FindingCategory.RUNTIME,
                    severity=ContainerSeverity.HIGH,
                    title="Container defaults to root user",
                    description="Container process runs as root or user is unspecified.",
                    resource_id=container_id,
                    resource_type="container:runtime",
                    recommendation="Set a non-root USER in the image and runtime configuration.",
                    compliance_issues=[_cis("5.6", "Ensure containers do not run as root")],
                )
            )

        if not host.get("ReadonlyRootfs", False):
            findings.append(
                ContainerFinding(
                    finding_id=f"runtime-rootfs-writable-{container_id}",
                    category=FindingCategory.RUNTIME,
                    severity=ContainerSeverity.MEDIUM,
                    title="Container root filesystem is writable",
                    description="Writable root filesystem increases persistence opportunities for attackers.",
                    resource_id=container_id,
                    resource_type="container:runtime",
                    recommendation="Enable read-only root filesystem and use explicit writable volumes.",
                    compliance_issues=[_cis("5.12", "Ensure container root filesystem is read-only")],
                )
            )

        security_opts = [str(opt).lower() for opt in host.get("SecurityOpt", []) or []]
        if any("seccomp=unconfined" in opt or "apparmor=unconfined" in opt for opt in security_opts):
            findings.append(
                ContainerFinding(
                    finding_id=f"runtime-security-profile-{container_id}",
                    category=FindingCategory.RUNTIME,
                    severity=ContainerSeverity.HIGH,
                    title="Container security profile disabled",
                    description="Container appears to run with unconfined seccomp/apparmor profile.",
                    resource_id=container_id,
                    resource_type="container:runtime",
                    recommendation="Apply seccomp and apparmor profiles appropriate for workload behavior.",
                    compliance_issues=[_cis("5.9", "Ensure default seccomp profile is not disabled")],
                )
            )

        return findings

    def _check_privilege_escalation(self, container_id: str, data: dict[str, Any]) -> list[ContainerFinding]:
        findings: list[ContainerFinding] = []
        host = data.get("HostConfig", {})
        caps = {cap.upper() for cap in host.get("CapAdd", []) or []}

        risky_caps = sorted(caps.intersection({"SYS_ADMIN", "SYS_PTRACE", "NET_ADMIN", "DAC_READ_SEARCH"}))
        if risky_caps:
            findings.append(
                ContainerFinding(
                    finding_id=f"runtime-capabilities-{container_id}",
                    category=FindingCategory.RUNTIME,
                    severity=ContainerSeverity.HIGH,
                    title="Risky Linux capabilities added",
                    description=f"Container adds high-risk capabilities: {', '.join(risky_caps)}.",
                    resource_id=container_id,
                    resource_type="container:runtime",
                    recommendation="Drop added capabilities and use least privilege with --cap-drop ALL baseline.",
                    compliance_issues=[_cis("5.3", "Ensure Linux kernel capabilities are restricted")],
                    metadata={"capabilities": risky_caps},
                )
            )

        if host.get("PidMode") == "host" or host.get("IpcMode") == "host":
            findings.append(
                ContainerFinding(
                    finding_id=f"runtime-host-namespace-{container_id}",
                    category=FindingCategory.RUNTIME,
                    severity=ContainerSeverity.HIGH,
                    title="Container shares host namespace",
                    description="Container shares host PID/IPC namespace, increasing escape and reconnaissance risk.",
                    resource_id=container_id,
                    resource_type="container:runtime",
                    recommendation="Avoid host namespace sharing unless explicitly required and monitored.",
                    compliance_issues=[_cis("5.16", "Ensure host namespace sharing is not used")],
                )
            )

        return findings

    def _check_network_policy(self, container_id: str, data: dict[str, Any]) -> list[ContainerFinding]:
        findings: list[ContainerFinding] = []
        host = data.get("HostConfig", {})

        if host.get("NetworkMode") == "host":
            findings.append(
                ContainerFinding(
                    finding_id=f"runtime-host-network-{container_id}",
                    category=FindingCategory.RUNTIME,
                    severity=ContainerSeverity.HIGH,
                    title="Container uses host network mode",
                    description="Host network mode bypasses Docker network isolation.",
                    resource_id=container_id,
                    resource_type="container:runtime",
                    recommendation="Use bridge or dedicated user-defined networks and explicit policy controls.",
                    compliance_issues=[_cis("5.15", "Ensure host network namespace is not shared")],
                )
            )

        port_bindings = host.get("PortBindings", {}) or {}
        for port_proto, bindings in port_bindings.items():
            for binding in bindings or []:
                host_ip = str(binding.get("HostIp", "")).strip()
                if host_ip in {"", "0.0.0.0", "::"}:
                    findings.append(
                        ContainerFinding(
                            finding_id=f"runtime-public-port-{container_id}-{port_proto}",
                            category=FindingCategory.RUNTIME,
                            severity=ContainerSeverity.MEDIUM,
                            title="Container port exposed on all interfaces",
                            description=f"Port {port_proto} is bound publicly on host interface '{host_ip or '0.0.0.0'}'.",
                            resource_id=container_id,
                            resource_type="container:runtime",
                            recommendation="Bind ports to specific interfaces or ingress proxies with access controls.",
                        )
                    )

        return findings

    def _check_secret_mounts(self, container_id: str, data: dict[str, Any]) -> list[ContainerFinding]:
        findings: list[ContainerFinding] = []

        mounts = data.get("Mounts", []) or []
        for mount in mounts:
            source = str(mount.get("Source", ""))
            destination = str(mount.get("Destination", ""))
            if re.search(r"secret|token|passwd|\.pem|\.key", source, re.IGNORECASE) or destination.startswith(
                "/run/secrets"
            ):
                findings.append(
                    ContainerFinding(
                        finding_id=f"runtime-secret-mount-{container_id}-{destination}",
                        category=FindingCategory.RUNTIME,
                        severity=ContainerSeverity.HIGH,
                        title="Potential secret mount detected",
                        description=(
                            f"Container mounts potential secret material from '{source}' to '{destination}'."
                        ),
                        resource_id=container_id,
                        resource_type="container:runtime",
                        recommendation="Use dedicated secret stores and ensure mounted secrets are read-only and rotated.",
                        compliance_issues=[_cis("5.31", "Ensure secrets are managed securely")],
                        metadata={"source": source, "destination": destination},
                    )
                )

        envs = data.get("Config", {}).get("Env", []) or []
        for env in envs:
            key = env.split("=", 1)[0].upper()
            if any(token in key for token in ["SECRET", "TOKEN", "PASSWORD", "API_KEY"]):
                findings.append(
                    ContainerFinding(
                        finding_id=f"runtime-secret-env-{container_id}-{key}",
                        category=FindingCategory.RUNTIME,
                        severity=ContainerSeverity.MEDIUM,
                        title="Sensitive environment variable detected",
                        description=f"Environment variable '{key}' may contain sensitive secret material.",
                        resource_id=container_id,
                        resource_type="container:runtime",
                        recommendation="Move secrets out of environment variables into a secure secret backend.",
                        compliance_issues=[_cis("5.31", "Ensure secrets are managed securely")],
                        metadata={"variable": key},
                    )
                )

        return findings

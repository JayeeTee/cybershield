"""Open-port scanner wrapper around python-nmap."""

from __future__ import annotations

from typing import Any

from .models import AlertCategory, NetworkAlert, PortService, Severity

try:
    import nmap
except Exception:  # noqa: BLE001
    nmap = None


class PortScanner:
    """Simple nmap integration for host port discovery."""

    def __init__(self, scanner: Any | None = None) -> None:
        if scanner is not None:
            self._scanner = scanner
            return
        if nmap is None:
            raise RuntimeError("python-nmap is required for port scanning")
        self._scanner = nmap.PortScanner()

    def scan(self, target: str, arguments: str = "-sV -Pn --open") -> tuple[list[PortService], list[NetworkAlert]]:
        """Run nmap against target and return services and security alerts."""
        scan_result = self._scanner.scan(target, arguments=arguments)
        services: list[PortService] = []
        alerts: list[NetworkAlert] = []

        for host in self._scanner.all_hosts():
            for transport in self._scanner[host].all_protocols():
                ports = self._scanner[host][transport]
                for port, metadata in ports.items():
                    service = PortService(
                        host=host,
                        port=int(port),
                        transport=transport,
                        state=metadata.get("state", "unknown"),
                        service=metadata.get("name"),
                        product=metadata.get("product"),
                        version=metadata.get("version"),
                        extra_info=metadata.get("extrainfo"),
                    )
                    services.append(service)

                    if service.state == "open" and service.port in {21, 23, 3389, 445}:
                        alerts.append(
                            NetworkAlert(
                                alert_id=f"risky-port-{host}-{service.port}",
                                category=AlertCategory.CONFIGURATION,
                                severity=Severity.HIGH,
                                title="Potentially risky administrative port exposed",
                                description=(
                                    f"Host {host} exposes port {service.port} "
                                    f"({service.service or 'unknown service'})."
                                ),
                                src_ip=host,
                                evidence={"port": service.port, "service": service.service},
                            )
                        )

        if scan_result.get("nmap", {}).get("scanstats", {}).get("uphosts") == "0":
            alerts.append(
                NetworkAlert(
                    alert_id=f"scan-unreachable-{target}",
                    category=AlertCategory.CONFIGURATION,
                    severity=Severity.INFO,
                    title="Target appears unreachable",
                    description=f"No live hosts were discovered for target '{target}'.",
                    evidence={"target": target},
                )
            )
        return services, alerts

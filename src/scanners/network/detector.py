"""Threat detection and network security control analysis."""

from __future__ import annotations

import ipaddress
from collections import Counter, defaultdict

import requests

from .models import (
    AlertCategory,
    DNSSecurityResult,
    FirewallRuleFinding,
    NetworkAlert,
    NetworkFlow,
    Protocol,
    Severity,
    ThreatReport,
)

LATERAL_MOVEMENT_PORTS = {135, 139, 445, 3389, 5985, 5986}


class NetworkThreatDetector:
    """Detect C2/lateral movement/exfiltration and validate DNS/firewall controls."""

    def __init__(self, *, known_c2_ips: set[str] | None = None, known_c2_domains: set[str] | None = None) -> None:
        self.known_c2_ips = known_c2_ips or set()
        self.known_c2_domains = known_c2_domains or set()

    def detect_threats(self, flows: list[NetworkFlow]) -> ThreatReport:
        alerts: list[NetworkAlert] = []
        alerts.extend(self.detect_c2_communications(flows))
        alerts.extend(self.detect_lateral_movement(flows))
        alerts.extend(self.detect_exfiltration(flows))
        alerts.extend(self.detect_attack_signatures(flows))
        return ThreatReport(alerts=alerts)

    def detect_c2_communications(self, flows: list[NetworkFlow]) -> list[NetworkAlert]:
        """Detect known or suspicious C2-like communication patterns."""
        alerts: list[NetworkAlert] = []
        dst_frequency = Counter(flow.dst_ip for flow in flows)

        for flow in flows:
            is_known = flow.dst_ip in self.known_c2_ips
            repeated_short = (
                flow.packet_count >= 4
                and flow.payload_bytes < 50_000
                and dst_frequency[flow.dst_ip] >= 3
                and flow.duration_seconds > 60
            )
            if is_known or repeated_short:
                alerts.append(
                    NetworkAlert(
                        alert_id=f"c2-{flow.flow_id}",
                        category=AlertCategory.THREAT,
                        severity=Severity.CRITICAL if is_known else Severity.HIGH,
                        title="Potential command-and-control communication",
                        description=(
                            "Destination matches known C2 infrastructure."
                            if is_known
                            else "Repeated low-volume communication pattern resembles C2 beaconing."
                        ),
                        src_ip=flow.src_ip,
                        dst_ip=flow.dst_ip,
                        protocol=flow.protocol,
                        evidence={"packet_count": flow.packet_count, "payload_bytes": flow.payload_bytes},
                    )
                )
        return alerts

    def detect_lateral_movement(self, flows: list[NetworkFlow]) -> list[NetworkAlert]:
        """Detect internal lateral movement indicators."""
        alerts: list[NetworkAlert] = []
        source_targets: dict[str, set[str]] = defaultdict(set)

        for flow in flows:
            if not self._is_internal(flow.src_ip) or not self._is_internal(flow.dst_ip):
                continue
            source_targets[flow.src_ip].add(flow.dst_ip)
            if flow.dst_port in LATERAL_MOVEMENT_PORTS:
                alerts.append(
                    NetworkAlert(
                        alert_id=f"lateral-{flow.flow_id}",
                        category=AlertCategory.THREAT,
                        severity=Severity.HIGH,
                        title="Potential lateral movement activity",
                        description="Internal host communicated over common lateral movement port.",
                        src_ip=flow.src_ip,
                        dst_ip=flow.dst_ip,
                        protocol=flow.protocol,
                        evidence={"dst_port": flow.dst_port},
                    )
                )

        for src_ip, targets in source_targets.items():
            if len(targets) >= 8:
                alerts.append(
                    NetworkAlert(
                        alert_id=f"scan-internal-{src_ip}",
                        category=AlertCategory.THREAT,
                        severity=Severity.MEDIUM,
                        title="Internal host scanning multiple peers",
                        description="Source contacted many internal hosts, indicating possible discovery activity.",
                        src_ip=src_ip,
                        protocol=Protocol.TCP,
                        evidence={"unique_internal_targets": len(targets)},
                    )
                )
        return alerts

    def detect_exfiltration(self, flows: list[NetworkFlow], threshold: int = 10_000_000) -> list[NetworkAlert]:
        """Detect large outbound transfers to external addresses."""
        alerts: list[NetworkAlert] = []
        for flow in flows:
            if not self._is_internal(flow.src_ip) or self._is_internal(flow.dst_ip):
                continue
            if flow.total_bytes < threshold:
                continue
            alerts.append(
                NetworkAlert(
                    alert_id=f"outbound-exfil-{flow.flow_id}",
                    category=AlertCategory.THREAT,
                    severity=Severity.CRITICAL,
                    title="Large outbound transfer to external host",
                    description="Flow size exceeds expected threshold and may indicate data exfiltration.",
                    src_ip=flow.src_ip,
                    dst_ip=flow.dst_ip,
                    protocol=flow.protocol,
                    evidence={"bytes": flow.total_bytes, "dst_port": flow.dst_port},
                )
            )
        return alerts

    def detect_attack_signatures(self, flows: list[NetworkFlow]) -> list[NetworkAlert]:
        """Detect coarse network-based attack signatures."""
        alerts: list[NetworkAlert] = []
        for flow in flows:
            if flow.protocol == Protocol.SMB and flow.packet_count > 200:
                alerts.append(
                    NetworkAlert(
                        alert_id=f"sig-smb-abuse-{flow.flow_id}",
                        category=AlertCategory.SIGNATURE,
                        severity=Severity.HIGH,
                        title="SMB traffic spike signature",
                        description="High-volume SMB traffic may indicate brute-force or propagation.",
                        src_ip=flow.src_ip,
                        dst_ip=flow.dst_ip,
                        protocol=flow.protocol,
                        evidence={"packet_count": flow.packet_count},
                    )
                )
            if flow.dst_port == 4444 and flow.protocol in {Protocol.TCP, Protocol.UNKNOWN}:
                alerts.append(
                    NetworkAlert(
                        alert_id=f"sig-revshell-{flow.flow_id}",
                        category=AlertCategory.SIGNATURE,
                        severity=Severity.HIGH,
                        title="Reverse-shell port signature",
                        description="Traffic observed to common reverse-shell port 4444.",
                        src_ip=flow.src_ip,
                        dst_ip=flow.dst_ip,
                        protocol=flow.protocol,
                        evidence={"dst_port": flow.dst_port},
                    )
                )
        return alerts

    def analyze_dns_security(self, domain: str, timeout: float = 5.0) -> DNSSecurityResult:
        """Check DNSSEC and DoH support using DNS-over-HTTPS queries."""
        notes: list[str] = []
        dnssec_enabled = False
        doh_supported = False
        resolvers = ["https://cloudflare-dns.com/dns-query", "https://dns.google/resolve"]

        for resolver in resolvers:
            try:
                response = requests.get(
                    resolver,
                    params={"name": domain, "type": "DNSKEY", "do": "true"},
                    headers={"accept": "application/dns-json"},
                    timeout=timeout,
                )
                if response.ok:
                    doh_supported = True
                    data = response.json()
                    answers = data.get("Answer", [])
                    if any(record.get("type") == 48 for record in answers):
                        dnssec_enabled = True
            except Exception as exc:  # noqa: BLE001
                notes.append(f"{resolver} query failed: {exc}")

        if not dnssec_enabled:
            notes.append("No DNSKEY records were observed via tested resolvers.")
        if not doh_supported:
            notes.append("All DoH checks failed.")

        return DNSSecurityResult(
            domain=domain,
            dnssec_enabled=dnssec_enabled,
            doh_supported=doh_supported,
            resolvers_tested=resolvers,
            notes=notes,
        )

    def analyze_firewall_rules(self, rules: list[dict[str, str]]) -> list[FirewallRuleFinding]:
        """Analyze firewall rules for risky exposure patterns."""
        findings: list[FirewallRuleFinding] = []
        for rule in rules:
            action = (rule.get("action") or "").lower()
            source = (rule.get("source") or "").lower()
            destination_port = str(rule.get("destination_port") or "")
            name = rule.get("name") or "unnamed-rule"

            if action == "allow" and source in {"0.0.0.0/0", "::/0", "any"}:
                findings.append(
                    FirewallRuleFinding(
                        rule_name=name,
                        severity=Severity.HIGH,
                        issue="Rule allows traffic from any source",
                        recommendation="Restrict source CIDRs to trusted networks.",
                    )
                )
            if action == "allow" and destination_port in {"22", "3389", "445"} and source in {"0.0.0.0/0", "any"}:
                findings.append(
                    FirewallRuleFinding(
                        rule_name=name,
                        severity=Severity.CRITICAL,
                        issue=f"Administrative port {destination_port} exposed publicly",
                        recommendation="Limit management access via VPN or bastion host.",
                    )
                )
        return findings

    @staticmethod
    def _is_internal(ip_str: str) -> bool:
        try:
            return ipaddress.ip_address(ip_str).is_private
        except ValueError:
            return False

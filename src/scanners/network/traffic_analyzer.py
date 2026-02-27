"""Packet and flow analysis for network traffic."""

from __future__ import annotations

import hashlib
import logging
import statistics
from pathlib import Path
from typing import Iterable

from scapy.all import ICMP, IP, IPv6, Raw, TCP, UDP, rdpcap
from scapy.packet import Packet

from .models import AlertCategory, NetworkAlert, NetworkFlow, PacketSummary, Protocol, Severity, TrafficReport

logger = logging.getLogger(__name__)

WELL_KNOWN_PORT_PROTOCOLS: dict[int, Protocol] = {
    20: Protocol.FTP,
    21: Protocol.FTP,
    22: Protocol.SSH,
    25: Protocol.SMTP,
    53: Protocol.DNS,
    80: Protocol.HTTP,
    443: Protocol.HTTPS,
    445: Protocol.SMB,
}


class NetworkTrafficAnalyzer:
    """Analyze packet captures and detect traffic-level anomalies."""

    def __init__(
        self,
        *,
        beacon_min_events: int = 5,
        beacon_jitter_threshold: float = 0.2,
        exfiltration_bytes_threshold: int = 5_000_000,
        known_bad_ja3: set[str] | None = None,
    ) -> None:
        self.beacon_min_events = beacon_min_events
        self.beacon_jitter_threshold = beacon_jitter_threshold
        self.exfiltration_bytes_threshold = exfiltration_bytes_threshold
        self.known_bad_ja3 = known_bad_ja3 or set()

    def analyze_pcap(self, pcap_path: str | Path) -> TrafficReport:
        """Parse a PCAP file, reconstruct flows, and generate anomaly alerts."""
        report = TrafficReport()
        packets: list[Packet]

        try:
            packets = list(rdpcap(str(pcap_path)))
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"Failed to read PCAP '{pcap_path}': {exc}")
            return report

        flow_map: dict[str, NetworkFlow] = {}

        for packet in packets:
            packet_summary = self._decode_packet(packet)
            if packet_summary is None:
                continue
            report.packets.append(packet_summary)

            flow = flow_map.get(self._flow_id(packet_summary))
            if flow is None:
                flow = NetworkFlow(
                    flow_id=self._flow_id(packet_summary),
                    src_ip=packet_summary.src_ip,
                    dst_ip=packet_summary.dst_ip,
                    src_port=packet_summary.src_port,
                    dst_port=packet_summary.dst_port,
                    protocol=packet_summary.protocol,
                    start_time=packet_summary.timestamp,
                    end_time=packet_summary.timestamp,
                )
                flow_map[flow.flow_id] = flow

            flow.packet_count += 1
            flow.total_bytes += packet_summary.size
            flow.payload_bytes += packet_summary.payload_size
            flow.end_time = max(flow.end_time, packet_summary.timestamp)
            flow.packet_timestamps.append(packet_summary.timestamp)
            if packet_summary.ja3 and packet_summary.ja3 not in flow.ja3_fingerprints:
                flow.ja3_fingerprints.append(packet_summary.ja3)

        report.flows = list(flow_map.values())
        report.alerts.extend(self.detect_anomalies(report.flows))
        return report

    def detect_anomalies(self, flows: Iterable[NetworkFlow]) -> list[NetworkAlert]:
        """Run anomaly detection for beaconing, exfiltration, and JA3 hits."""
        alerts: list[NetworkAlert] = []
        for flow in flows:
            if self._is_beaconing(flow):
                alerts.append(
                    NetworkAlert(
                        alert_id=f"beacon-{flow.flow_id}",
                        category=AlertCategory.ANOMALY,
                        severity=Severity.HIGH,
                        title="Potential beaconing traffic detected",
                        description="Flow timing is highly regular and may indicate C2 beaconing.",
                        src_ip=flow.src_ip,
                        dst_ip=flow.dst_ip,
                        protocol=flow.protocol,
                        evidence={
                            "packet_count": flow.packet_count,
                            "duration_seconds": flow.duration_seconds,
                        },
                    )
                )

            if self._is_data_exfiltration(flow):
                alerts.append(
                    NetworkAlert(
                        alert_id=f"exfil-{flow.flow_id}",
                        category=AlertCategory.ANOMALY,
                        severity=Severity.CRITICAL,
                        title="Potential data exfiltration pattern detected",
                        description="A large outbound flow was observed to a non-standard destination.",
                        src_ip=flow.src_ip,
                        dst_ip=flow.dst_ip,
                        protocol=flow.protocol,
                        evidence={
                            "total_bytes": flow.total_bytes,
                            "payload_bytes": flow.payload_bytes,
                            "dst_port": flow.dst_port,
                        },
                    )
                )

            for fingerprint in flow.ja3_fingerprints:
                if fingerprint in self.known_bad_ja3:
                    alerts.append(
                        NetworkAlert(
                            alert_id=f"ja3-{flow.flow_id}-{fingerprint[:8]}",
                            category=AlertCategory.THREAT,
                            severity=Severity.CRITICAL,
                            title="Known malicious JA3 fingerprint observed",
                            description="TLS client fingerprint matches known bad JA3 indicator.",
                            src_ip=flow.src_ip,
                            dst_ip=flow.dst_ip,
                            protocol=Protocol.TLS,
                            evidence={"ja3": fingerprint},
                        )
                    )
        return alerts

    def _decode_packet(self, packet: Packet) -> PacketSummary | None:
        if not (packet.haslayer(IP) or packet.haslayer(IPv6)):
            return None

        ip_layer = packet[IP] if packet.haslayer(IP) else packet[IPv6]
        src_ip = getattr(ip_layer, "src", "")
        dst_ip = getattr(ip_layer, "dst", "")
        src_port: int | None = None
        dst_port: int | None = None
        tcp_flags: str | None = None
        protocol = Protocol.UNKNOWN

        if packet.haslayer(TCP):
            tcp_layer = packet[TCP]
            src_port = int(tcp_layer.sport)
            dst_port = int(tcp_layer.dport)
            tcp_flags = str(tcp_layer.flags)
            protocol = self._protocol_from_ports(src_port, dst_port, fallback=Protocol.TCP)
        elif packet.haslayer(UDP):
            udp_layer = packet[UDP]
            src_port = int(udp_layer.sport)
            dst_port = int(udp_layer.dport)
            protocol = self._protocol_from_ports(src_port, dst_port, fallback=Protocol.UDP)
        elif packet.haslayer(ICMP):
            protocol = Protocol.ICMP

        payload_size = len(bytes(packet[Raw])) if packet.haslayer(Raw) else 0
        ja3 = self._extract_ja3(packet, src_port, dst_port)

        return PacketSummary(
            timestamp=float(packet.time),
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            protocol=protocol,
            size=len(packet),
            payload_size=payload_size,
            tcp_flags=tcp_flags,
            ja3=ja3,
        )

    def _extract_ja3(self, packet: Packet, src_port: int | None, dst_port: int | None) -> str | None:
        tls_ports = {443, 8443, 9443}
        if src_port not in tls_ports and dst_port not in tls_ports:
            return None
        if not packet.haslayer(Raw):
            return None
        # Best-effort fingerprint fallback when full TLS parser is unavailable.
        raw_bytes = bytes(packet[Raw])[:128]
        if not raw_bytes:
            return None
        return hashlib.md5(raw_bytes).hexdigest()

    def _is_beaconing(self, flow: NetworkFlow) -> bool:
        if len(flow.packet_timestamps) < self.beacon_min_events:
            return False
        deltas = [b - a for a, b in zip(flow.packet_timestamps[:-1], flow.packet_timestamps[1:]) if b > a]
        if len(deltas) < self.beacon_min_events - 1:
            return False
        mean_delta = statistics.mean(deltas)
        if mean_delta <= 0:
            return False
        std_delta = statistics.pstdev(deltas)
        jitter_ratio = std_delta / mean_delta if mean_delta else 1.0
        return jitter_ratio <= self.beacon_jitter_threshold

    def _is_data_exfiltration(self, flow: NetworkFlow) -> bool:
        if flow.total_bytes < self.exfiltration_bytes_threshold:
            return False
        if flow.dst_port in {53, 80, 443}:
            return False
        return True

    @staticmethod
    def _protocol_from_ports(src_port: int, dst_port: int, *, fallback: Protocol) -> Protocol:
        if src_port in WELL_KNOWN_PORT_PROTOCOLS:
            return WELL_KNOWN_PORT_PROTOCOLS[src_port]
        if dst_port in WELL_KNOWN_PORT_PROTOCOLS:
            return WELL_KNOWN_PORT_PROTOCOLS[dst_port]
        return fallback

    @staticmethod
    def _flow_id(packet: PacketSummary) -> str:
        src = f"{packet.src_ip}:{packet.src_port or 0}"
        dst = f"{packet.dst_ip}:{packet.dst_port or 0}"
        return f"{src}->{dst}:{packet.protocol.value}"

"""Tests for network traffic scanner modules."""

from __future__ import annotations

import hashlib
import socket
from datetime import datetime, timedelta, timezone

import pytest
from scapy.all import IP, Raw, TCP, wrpcap

from src.scanners.network.detector import NetworkThreatDetector
from src.scanners.network.models import NetworkFlow, Protocol
from src.scanners.network.port_scanner import PortScanner
from src.scanners.network.ssl_checker import SSLChecker
from src.scanners.network.traffic_analyzer import NetworkTrafficAnalyzer


def test_traffic_analyzer_reconstructs_flows_and_detects_anomalies(tmp_path):
    pcap_path = tmp_path / "traffic.pcap"
    packets = []

    for idx in range(6):
        packet = IP(src="10.0.0.10", dst="198.51.100.20") / TCP(sport=50123, dport=9001) / Raw(load=b"A" * 80)
        packet.time = float(idx * 10 + 1)
        packets.append(packet)

    tls_payload = b"fake_client_hello_payload"
    tls_packet = IP(src="10.0.0.10", dst="198.51.100.30") / TCP(sport=50200, dport=443) / Raw(load=tls_payload)
    tls_packet.time = 100.0
    packets.append(tls_packet)

    wrpcap(str(pcap_path), packets)

    bad_ja3 = hashlib.md5(tls_payload[:128]).hexdigest()
    analyzer = NetworkTrafficAnalyzer(
        beacon_min_events=5,
        beacon_jitter_threshold=0.1,
        exfiltration_bytes_threshold=300,
        known_bad_ja3={bad_ja3},
    )
    report = analyzer.analyze_pcap(pcap_path)

    assert report.errors == []
    assert len(report.packets) == len(packets)
    assert len(report.flows) == 2
    titles = {alert.title for alert in report.alerts}
    assert "Potential beaconing traffic detected" in titles
    assert "Potential data exfiltration pattern detected" in titles
    assert "Known malicious JA3 fingerprint observed" in titles


class _FakeHostData(dict):
    def all_protocols(self):
        return list(self.keys())


class _FakeNmapScanner:
    def __init__(self):
        self._data = {
            "192.168.1.15": _FakeHostData(
                {
                    "tcp": {
                        22: {"state": "open", "name": "ssh", "product": "OpenSSH", "version": "9.0"},
                        443: {"state": "open", "name": "https"},
                    }
                }
            )
        }

    def scan(self, target, arguments=""):
        return {"nmap": {"scanstats": {"uphosts": "1"}}}

    def all_hosts(self):
        return list(self._data.keys())

    def __getitem__(self, host):
        return self._data[host]


def test_port_scanner_wraps_nmap_output():
    scanner = PortScanner(scanner=_FakeNmapScanner())
    services, alerts = scanner.scan("192.168.1.0/24")

    assert len(services) == 2
    assert any(service.port == 22 for service in services)
    assert any(alert.title == "Potentially risky administrative port exposed" for alert in alerts)


def test_ssl_checker_handles_handshake_failure(monkeypatch):
    checker = SSLChecker()

    def _boom(*args, **kwargs):
        raise socket.error("connection refused")

    monkeypatch.setattr(socket, "create_connection", _boom)
    result = checker.check("example.com", 443)

    assert not result.valid
    assert any("TLS handshake failed" in issue for issue in result.issues)


def test_ssl_checker_flags_weak_tls_and_self_signed(monkeypatch):
    checker = SSLChecker()
    now = datetime.now(timezone.utc)
    cert = {
        "subject": ((("commonName", "example.com"),),),
        "issuer": ((("commonName", "example.com"),),),
        "notBefore": (now - timedelta(days=1)).strftime("%b %d %H:%M:%S %Y GMT"),
        "notAfter": (now + timedelta(days=5)).strftime("%b %d %H:%M:%S %Y GMT"),
    }

    class _FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _FakeTLSSocket:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def version(self):
            return "TLSv1"

        def cipher(self):
            return ("RC4-MD5", "TLSv1", 128)

        def getpeercert(self):
            return cert

    class _FakeContext:
        def wrap_socket(self, sock, server_hostname=None):
            return _FakeTLSSocket()

    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: _FakeSocket())
    monkeypatch.setattr("src.scanners.network.ssl_checker.ssl.create_default_context", lambda: _FakeContext())

    result = checker.check("example.com", 443)
    assert not result.valid
    assert any("Weak TLS version" in issue for issue in result.issues)
    assert any("Weak cipher" in issue for issue in result.issues)
    assert any("self-signed" in issue.lower() for issue in result.issues)


def test_threat_detector_finds_c2_lateral_exfil_and_signatures():
    detector = NetworkThreatDetector(known_c2_ips={"203.0.113.66"})
    flows = [
        NetworkFlow(
            flow_id="c2-flow",
            src_ip="10.1.1.5",
            dst_ip="203.0.113.66",
            src_port=51111,
            dst_port=443,
            protocol=Protocol.HTTPS,
            packet_count=10,
            total_bytes=50_000,
            payload_bytes=20_000,
            start_time=0,
            end_time=200,
        ),
        NetworkFlow(
            flow_id="lateral-flow",
            src_ip="10.1.1.5",
            dst_ip="10.1.2.8",
            src_port=52331,
            dst_port=445,
            protocol=Protocol.SMB,
            packet_count=220,
            total_bytes=800_000,
            payload_bytes=700_000,
            start_time=0,
            end_time=60,
        ),
        NetworkFlow(
            flow_id="exfil-flow",
            src_ip="10.2.3.4",
            dst_ip="198.51.100.50",
            src_port=60000,
            dst_port=4444,
            protocol=Protocol.TCP,
            packet_count=120,
            total_bytes=12_000_000,
            payload_bytes=11_000_000,
            start_time=0,
            end_time=40,
        ),
    ]

    report = detector.detect_threats(flows)
    titles = {alert.title for alert in report.alerts}
    assert "Potential command-and-control communication" in titles
    assert "Potential lateral movement activity" in titles
    assert "Large outbound transfer to external host" in titles
    assert "SMB traffic spike signature" in titles
    assert "Reverse-shell port signature" in titles


def test_firewall_and_dns_checks(monkeypatch):
    detector = NetworkThreatDetector()
    rules = [
        {"name": "allow-any-rdp", "action": "allow", "source": "0.0.0.0/0", "destination_port": "3389"},
    ]
    findings = detector.analyze_firewall_rules(rules)
    assert len(findings) >= 2

    class _FakeResponse:
        ok = True

        @staticmethod
        def json():
            return {"Answer": [{"type": 48, "data": "fake-dnskey"}]}

    monkeypatch.setattr("src.scanners.network.detector.requests.get", lambda *args, **kwargs: _FakeResponse())
    dns = detector.analyze_dns_security("example.com")
    assert dns.doh_supported is True
    assert dns.dnssec_enabled is True


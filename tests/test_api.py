"""Integration tests for CyberShield FastAPI API."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

from cybershield.api.app import create_app


client = TestClient(create_app())


def _token() -> str:
    response = client.post(
        "/api/v1/auth/token",
        json={"username": "analyst", "password": "cybershield"},
    )
    assert response.status_code == 200
    payload = response.json()
    return payload["access_token"]


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token()}"}


def _wait_for_completion(scan_id: str, headers: dict[str, str]) -> dict:
    for _ in range(40):
        response = client.get(f"/api/v1/scan/{scan_id}/results", headers=headers)
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in {"completed", "failed"}:
            return payload
        time.sleep(0.05)
    raise AssertionError("scan did not complete in time")


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_openapi_documented_paths():
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/scan/cloud" in paths
    assert "/api/v1/intel/ioc/{indicator}" in paths
    assert "/api/v1/dashboard/summary" in paths


def test_scan_cloud_endpoint_and_results():
    headers = _auth_headers()
    response = client.post(
        "/api/v1/scan/cloud",
        json={
            "provider": "aws",
            "account_id": "123456789012",
            "regions": ["us-east-1"],
            "include_compliance": True,
        },
        headers=headers,
    )
    assert response.status_code == 202
    scan_id = response.json()["scan_id"]

    result = _wait_for_completion(scan_id, headers)
    assert result["status"] == "completed"
    assert result["summary"]["total_findings"] >= 1


def test_scan_secrets_endpoint():
    headers = _auth_headers()
    response = client.post(
        "/api/v1/scan/secrets",
        json={
            "repository_url": "https://example.com/org/repo.git",
            "branch": "main",
            "include_history": True,
        },
        headers=headers,
    )
    assert response.status_code == 202
    result = _wait_for_completion(response.json()["scan_id"], headers)
    assert result["status"] == "completed"


def test_scan_container_endpoint():
    headers = _auth_headers()
    response = client.post(
        "/api/v1/scan/container",
        json={"image": "ghcr.io/example/app", "tag": "latest", "runtime_checks": False},
        headers=headers,
    )
    assert response.status_code == 202
    result = _wait_for_completion(response.json()["scan_id"], headers)
    assert result["status"] == "completed"


def test_scan_network_endpoint():
    headers = _auth_headers()
    response = client.post(
        "/api/v1/scan/network",
        json={"source": "eth0", "duration_seconds": 10, "detect_anomalies": True},
        headers=headers,
    )
    assert response.status_code == 202
    result = _wait_for_completion(response.json()["scan_id"], headers)
    assert result["status"] == "completed"


def test_scan_validation_error():
    headers = _auth_headers()
    response = client.post(
        "/api/v1/scan/cloud",
        json={"provider": "digitalocean", "account_id": "abc"},
        headers=headers,
    )
    assert response.status_code == 422


def test_intel_endpoints():
    headers = _auth_headers()

    ioc_response = client.get("/api/v1/intel/ioc/malicious-domain.example", headers=headers)
    assert ioc_response.status_code == 200
    assert ioc_response.json()["malicious"] is True

    cve_response = client.get("/api/v1/intel/cve/CVE-2024-9999", headers=headers)
    assert cve_response.status_code == 200
    assert cve_response.json()["cve_id"] == "CVE-2024-9999"

    feed_response = client.get("/api/v1/intel/threats", headers=headers)
    assert feed_response.status_code == 200
    assert feed_response.json()["total"] >= 1


def test_dashboard_endpoints():
    headers = _auth_headers()
    summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert "overall_risk_score" in summary.json()

    findings = client.get("/api/v1/dashboard/findings", headers=headers)
    assert findings.status_code == 200
    assert "findings" in findings.json()

    metrics = client.get("/api/v1/dashboard/metrics", headers=headers)
    assert metrics.status_code == 200
    assert "findings_by_severity" in metrics.json()


def test_auth_required_for_protected_route():
    response = client.get("/api/v1/intel/threats")
    assert response.status_code == 403


def test_websocket_scan_updates():
    headers = _auth_headers()
    response = client.post(
        "/api/v1/scan/network",
        json={"source": "eth0", "duration_seconds": 15, "detect_anomalies": False},
        headers=headers,
    )
    assert response.status_code == 202
    scan_id = response.json()["scan_id"]

    with client.websocket_connect(f"/api/v1/scan/ws/scans/{scan_id}") as websocket:
        first = websocket.receive_json()
        assert "status" in first
        assert "progress" in first


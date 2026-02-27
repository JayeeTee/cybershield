"""Scan-related API routes and async orchestration."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from cybershield.api.auth import enforce_rate_limit, get_current_user
from cybershield.api.models import (
    CloudScanRequest,
    ContainerScanRequest,
    NetworkScanRequest,
    ScanAcceptedResponse,
    ScanFinding,
    ScanResultResponse,
    ScanStatus,
    ScanType,
    SecretScanRequest,
    Severity,
)


router = APIRouter(prefix="/api/v1/scan", tags=["scan"])


class ScanStore:
    """In-memory store for scan jobs and websocket subscribers."""

    def __init__(self) -> None:
        self.results: dict[str, ScanResultResponse] = {}
        self.subscribers: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def add_scan(self, result: ScanResultResponse) -> None:
        async with self._lock:
            self.results[result.scan_id] = result
            self.subscribers.setdefault(result.scan_id, set())

    async def get_scan(self, scan_id: str) -> ScanResultResponse | None:
        async with self._lock:
            return self.results.get(scan_id)

    async def all_scans(self) -> list[ScanResultResponse]:
        async with self._lock:
            return list(self.results.values())

    async def register_socket(self, scan_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            self.subscribers.setdefault(scan_id, set()).add(websocket)

    async def unregister_socket(self, scan_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            sockets = self.subscribers.get(scan_id)
            if sockets is None:
                return
            sockets.discard(websocket)

    async def broadcast(self, scan_id: str, payload: dict[str, str | int]) -> None:
        async with self._lock:
            sockets = list(self.subscribers.get(scan_id, set()))
        for socket in sockets:
            try:
                await socket.send_json(payload)
            except Exception:
                await self.unregister_socket(scan_id, socket)


scan_store = ScanStore()


def _sample_findings(scan_id: str, scan_type: ScanType) -> list[ScanFinding]:
    if scan_type == ScanType.CLOUD:
        return [
            ScanFinding(
                finding_id=f"{scan_id}-001",
                scan_id=scan_id,
                scan_type=scan_type,
                title="Public storage bucket detected",
                description="A cloud storage bucket allows public read access.",
                severity=Severity.HIGH,
                resource="storage://public-bucket",
            ),
            ScanFinding(
                finding_id=f"{scan_id}-002",
                scan_id=scan_id,
                scan_type=scan_type,
                title="MFA not enforced",
                description="Administrative identity does not enforce MFA.",
                severity=Severity.MEDIUM,
                resource="iam://admin-role",
            ),
        ]
    if scan_type == ScanType.SECRETS:
        return [
            ScanFinding(
                finding_id=f"{scan_id}-001",
                scan_id=scan_id,
                scan_type=scan_type,
                title="API key pattern found",
                description="Potential secret committed to repository history.",
                severity=Severity.CRITICAL,
                resource="repo://source/.env",
            )
        ]
    if scan_type == ScanType.CONTAINER:
        return [
            ScanFinding(
                finding_id=f"{scan_id}-001",
                scan_id=scan_id,
                scan_type=scan_type,
                title="Critical vulnerability in image",
                description="CVE package with remote code execution risk discovered.",
                severity=Severity.CRITICAL,
                resource="image://application:latest",
            ),
            ScanFinding(
                finding_id=f"{scan_id}-002",
                scan_id=scan_id,
                scan_type=scan_type,
                title="Image runs as root",
                description="Container configuration allows privileged execution.",
                severity=Severity.HIGH,
                resource="dockerfile://Dockerfile",
            ),
        ]
    return [
        ScanFinding(
            finding_id=f"{scan_id}-001",
            scan_id=scan_id,
            scan_type=scan_type,
            title="Suspicious outbound traffic",
            description="Connection to rare destination with malware fingerprint.",
            severity=Severity.HIGH,
            resource="flow://10.0.0.4->203.0.113.10",
        )
    ]


async def _run_scan(scan_id: str, scan_type: ScanType) -> None:
    scan = await scan_store.get_scan(scan_id)
    if scan is None:
        return
    scan.status = ScanStatus.RUNNING
    scan.updated_at = datetime.now(timezone.utc)
    await scan_store.broadcast(scan_id, {"status": scan.status.value, "progress": scan.progress})

    try:
        for progress in (15, 40, 65, 85):
            await asyncio.sleep(0.05)
            scan.progress = progress
            scan.updated_at = datetime.now(timezone.utc)
            await scan_store.broadcast(scan_id, {"status": scan.status.value, "progress": scan.progress})

        findings = _sample_findings(scan_id, scan_type)
        scan.findings = findings
        scan.summary = {
            "total_findings": len(findings),
            "critical": sum(1 for item in findings if item.severity == Severity.CRITICAL),
            "high": sum(1 for item in findings if item.severity == Severity.HIGH),
            "medium": sum(1 for item in findings if item.severity == Severity.MEDIUM),
        }
        scan.progress = 100
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.now(timezone.utc)
        scan.updated_at = scan.completed_at
        await scan_store.broadcast(scan_id, {"status": scan.status.value, "progress": scan.progress})
    except Exception as exc:
        scan.status = ScanStatus.FAILED
        scan.error = str(exc)
        scan.updated_at = datetime.now(timezone.utc)
        await scan_store.broadcast(scan_id, {"status": scan.status.value, "progress": scan.progress})


async def _create_scan(scan_type: ScanType) -> ScanAcceptedResponse:
    now = datetime.now(timezone.utc)
    scan_id = str(uuid4())
    initial = ScanResultResponse(
        scan_id=scan_id,
        scan_type=scan_type,
        status=ScanStatus.PENDING,
        started_at=now,
        updated_at=now,
    )
    await scan_store.add_scan(initial)
    asyncio.create_task(_run_scan(scan_id, scan_type))
    return ScanAcceptedResponse(scan_id=scan_id, status=ScanStatus.PENDING, scan_type=scan_type, submitted_at=now)


@router.post("/cloud", response_model=ScanAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_cloud_scan(
    request: CloudScanRequest,
    _: None = Depends(enforce_rate_limit),
) -> ScanAcceptedResponse:
    """Trigger an asynchronous cloud security posture scan."""
    if request.provider.lower() not in {"aws", "azure", "gcp"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="provider must be aws|azure|gcp")
    return await _create_scan(ScanType.CLOUD)


@router.post("/secrets", response_model=ScanAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_secret_scan(
    _: SecretScanRequest,
    __: None = Depends(enforce_rate_limit),
) -> ScanAcceptedResponse:
    """Trigger an asynchronous repository secret scan."""
    return await _create_scan(ScanType.SECRETS)


@router.post("/container", response_model=ScanAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_container_scan(
    _: ContainerScanRequest,
    __: None = Depends(enforce_rate_limit),
) -> ScanAcceptedResponse:
    """Trigger an asynchronous container image security scan."""
    return await _create_scan(ScanType.CONTAINER)


@router.post("/network", response_model=ScanAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_network_scan(
    _: NetworkScanRequest,
    __: None = Depends(enforce_rate_limit),
) -> ScanAcceptedResponse:
    """Trigger an asynchronous network traffic analysis scan."""
    return await _create_scan(ScanType.NETWORK)


@router.get("/{scan_id}/results", response_model=ScanResultResponse)
async def get_scan_results(
    scan_id: str,
    _: str = Depends(get_current_user),
    __: None = Depends(enforce_rate_limit),
) -> ScanResultResponse:
    """Fetch current or completed results for a scan execution."""
    result = await scan_store.get_scan(scan_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"scan_id '{scan_id}' not found")
    return result


@router.websocket("/ws/scans/{scan_id}")
async def scan_updates_socket(websocket: WebSocket, scan_id: str) -> None:
    """WebSocket endpoint for real-time scan progress updates."""
    await websocket.accept()
    await scan_store.register_socket(scan_id, websocket)
    result = await scan_store.get_scan(scan_id)
    if result is None:
        await websocket.send_json({"status": "not_found", "progress": 0})
    else:
        await websocket.send_json({"status": result.status.value, "progress": result.progress})

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await scan_store.unregister_socket(scan_id, websocket)


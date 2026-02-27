"""Tests for secrets detection and remediation."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone

from src.scanners.secrets.detector import SecretDetector
from src.scanners.secrets.models import DetectionMethod, SecretScanReport, Severity
from src.scanners.secrets.remediation import SecretAutoRemediator, severity_rank


def test_detects_regex_secrets_in_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".env").write_text(
        "AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF\n"
        "AWS_SECRET_ACCESS_KEY=abcdefghijklmnopqrstuvwxyz1234567890ABCD\n",
        encoding="utf-8",
    )
    (repo / "config.yml").write_text("stripe_key: sk_test_FAKE_KEY_FOR_TESTING_12345\n", encoding="utf-8")

    detector = SecretDetector()
    report = detector.scan_repository(repo)

    assert report.finding_count >= 3
    assert report.stats.regex_findings >= 3
    assert any(f.provider == "aws" for f in report.findings)
    assert any(f.provider == "stripe" for f in report.findings)
    assert any(f.file_path == ".env" and f.severity in {Severity.CRITICAL, Severity.HIGH} for f in report.findings)


def test_entropy_detection_finds_high_random_token(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "settings.properties").write_text(
        "auth_token=Q2hRck5lN0hKV09TTVQ5cVBRWjB6bGxjSmpMUT09\n",
        encoding="utf-8",
    )

    detector = SecretDetector(entropy_threshold=3.8)
    report = detector.scan_repository(repo)

    entropy_findings = [f for f in report.findings if f.detected_by == DetectionMethod.ENTROPY]
    assert entropy_findings
    assert report.stats.entropy_findings >= 1


def test_git_history_scanning_adds_findings(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=(
                "__COMMIT__abc123\n"
                "diff --git a/.env b/.env\n"
                "+++ b/.env\n"
                "+GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)

    detector = SecretDetector()
    report = detector.scan_repository(repo, scan_git_history=True)

    assert any(f.git_commit == "abc123" for f in report.findings)
    assert report.stats.git_history_findings >= 1


def test_remediation_builds_alerts_rotation_and_vault_hooks():
    report = SecretScanReport(
        repository="/tmp/repo",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        findings=[],
    )
    detector = SecretDetector()
    # Create one realistic finding via scanner path to ensure model fields stay consistent.
    sample_report = detector.scan_repository("tests")
    if sample_report.findings:
        report.findings.append(sample_report.findings[0])
    else:
        from src.scanners.secrets.models import SecretFinding

        report.findings.append(
            SecretFinding(
                finding_id="f1",
                secret_type="api_key",
                severity=Severity.HIGH,
                description="API key exposed",
                file_path=".env",
                line_number=1,
                match="sk_l...1234",
                provider="stripe",
                detected_by=DetectionMethod.REGEX,
                confidence=0.9,
            )
        )

    remediator = SecretAutoRemediator(default_alert_channels=["security", "pagerduty"])
    plan = remediator.build_plan(report)

    assert len(plan.alerts) == len(report.findings)
    assert len(plan.rotation_suggestions) == len(report.findings)
    assert len(plan.vault_hooks) == len(report.findings)
    assert all(alert.channels == ["security", "pagerduty"] for alert in plan.alerts)


def test_severity_rank_ordering():
    assert severity_rank(Severity.CRITICAL) > severity_rank(Severity.HIGH)
    assert severity_rank(Severity.HIGH) > severity_rank(Severity.MEDIUM)

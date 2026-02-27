"""TLS configuration validation checks."""

from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone

from .models import SSLResult

WEAK_CIPHER_HINTS = ("RC4", "3DES", "MD5", "NULL", "DES")
WEAK_TLS_VERSIONS = {"TLSv1", "TLSv1.1", "SSLv2", "SSLv3"}


class SSLChecker:
    """Perform SSL/TLS checks for a target endpoint."""

    def __init__(self, *, timeout: float = 5.0) -> None:
        self.timeout = timeout

    def check(self, host: str, port: int = 443) -> SSLResult:
        """Validate certificate and transport settings."""
        issues: list[str] = []
        tls_version: str | None = None
        cipher_name: str | None = None
        cert_subject: str | None = None
        cert_issuer: str | None = None
        not_before: datetime | None = None
        not_after: datetime | None = None

        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=self.timeout) as raw_sock:
                with context.wrap_socket(raw_sock, server_hostname=host) as tls_sock:
                    tls_version = tls_sock.version()
                    cipher_data = tls_sock.cipher()
                    cipher_name = cipher_data[0] if cipher_data else None
                    cert = tls_sock.getpeercert()
        except Exception as exc:  # noqa: BLE001
            return SSLResult(
                host=host,
                port=port,
                valid=False,
                issues=[f"TLS handshake failed: {exc}"],
            )

        if tls_version in WEAK_TLS_VERSIONS:
            issues.append(f"Weak TLS version negotiated: {tls_version}")
        if cipher_name and any(token in cipher_name.upper() for token in WEAK_CIPHER_HINTS):
            issues.append(f"Weak cipher negotiated: {cipher_name}")

        if cert:
            cert_subject = self._flatten_name(cert.get("subject", ()))
            cert_issuer = self._flatten_name(cert.get("issuer", ()))
            if cert_subject and cert_subject == cert_issuer:
                issues.append("Certificate appears self-signed")

            not_before = self._parse_cert_time(cert.get("notBefore"))
            not_after = self._parse_cert_time(cert.get("notAfter"))

            now = datetime.now(timezone.utc)
            if not_after and not_after < now:
                issues.append("Certificate has expired")
            if not_after and (not_after - now).days <= 30:
                issues.append("Certificate expires within 30 days")
        else:
            issues.append("Peer certificate missing")

        return SSLResult(
            host=host,
            port=port,
            valid=not issues,
            tls_version=tls_version,
            cipher=cipher_name,
            certificate_subject=cert_subject,
            certificate_issuer=cert_issuer,
            certificate_not_before=not_before,
            certificate_not_after=not_after,
            issues=issues,
        )

    @staticmethod
    def _flatten_name(name_tuples: tuple[tuple[tuple[str, str], ...], ...]) -> str | None:
        parts: list[str] = []
        for component in name_tuples:
            for key, value in component:
                parts.append(f"{key}={value}")
        return ", ".join(parts) if parts else None

    @staticmethod
    def _parse_cert_time(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromtimestamp(ssl.cert_time_to_seconds(value), tz=timezone.utc)
        except Exception:  # noqa: BLE001
            return None

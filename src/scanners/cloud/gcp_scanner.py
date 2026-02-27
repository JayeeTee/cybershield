"""GCP cloud security posture scanner."""

from __future__ import annotations

import logging
from typing import Any

from .base import CloudScannerBase
from .models import CloudFinding, CloudProvider, ComplianceIssue, Severity

logger = logging.getLogger(__name__)

try:
    from google.cloud import compute_v1
    from google.cloud import resourcemanager_v3
    from google.cloud import storage
except Exception:  # noqa: BLE001
    compute_v1 = None
    resourcemanager_v3 = None
    storage = None


def _cis(control_id: str, description: str) -> ComplianceIssue:
    return ComplianceIssue(framework="CIS Google Cloud Platform Foundations Benchmark", control_id=control_id, description=description)


class GCPScanner(CloudScannerBase):
    """Scanner implementing common GCP CSPM checks."""

    def __init__(
        self,
        *,
        project_id: str,
        storage_client: Any | None = None,
        firewalls_client: Any | None = None,
        disks_client: Any | None = None,
        projects_client: Any | None = None,
    ) -> None:
        super().__init__(CloudProvider.GCP)
        self.project_id = project_id

        self.storage_client = storage_client
        self.firewalls_client = firewalls_client
        self.disks_client = disks_client
        self.projects_client = projects_client

        if not all([self.storage_client, self.firewalls_client, self.disks_client, self.projects_client]):
            if not all([storage, compute_v1, resourcemanager_v3]):
                raise RuntimeError("google-cloud-* SDK packages are required unless GCP clients are injected")

            self.storage_client = self.storage_client or storage.Client(project=project_id)
            self.firewalls_client = self.firewalls_client or compute_v1.FirewallsClient()
            self.disks_client = self.disks_client or compute_v1.DisksClient()
            self.projects_client = self.projects_client or resourcemanager_v3.ProjectsClient()

    def scan(self):
        report = self._new_report()
        self._run_check(report, "exposed_gcs_buckets", self._check_exposed_buckets)
        self._run_check(report, "public_firewall_rules", self._check_public_firewall_rules)
        self._run_check(report, "unencrypted_disks_databases", self._check_unencrypted_storage)
        self._run_check(report, "over_privileged_iam", self._check_over_privileged_iam)
        self._run_check(report, "missing_root_mfa", self._check_root_mfa)
        return self._complete_report(report)

    def _check_exposed_buckets(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []
        for bucket in self.storage_client.list_buckets(project=self.project_id):
            bucket_name = getattr(bucket, "name", "unknown")
            public = False

            iam_config = getattr(bucket, "iam_configuration", None)
            pap = str(getattr(iam_config, "public_access_prevention", "")).lower() if iam_config else ""
            if pap != "enforced":
                policy = bucket.get_iam_policy(requested_policy_version=3)
                for binding in getattr(policy, "bindings", []):
                    members = set(binding.get("members", []))
                    if members.intersection({"allUsers", "allAuthenticatedUsers"}):
                        public = True
                        break

            if public:
                findings.append(
                    self._make_finding(
                        finding_id=f"gcp-gcs-public-{bucket_name}",
                        severity=Severity.HIGH,
                        title="Cloud Storage bucket is publicly accessible",
                        description=f"GCS bucket '{bucket_name}' allows public principal access.",
                        resource_id=bucket_name,
                        resource_type="gcp:gcs:bucket",
                        recommendation="Enforce public access prevention and remove public IAM members.",
                        compliance_issues=[_cis("5.1", "Ensure Cloud Storage buckets are not anonymously accessible")],
                    )
                )

        return findings

    def _check_public_firewall_rules(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []
        for rule in self.firewalls_client.list(project=self.project_id):
            direction = str(getattr(rule, "direction", "")).upper()
            source_ranges = set(getattr(rule, "source_ranges", []) or [])
            allowed = getattr(rule, "allowed", []) or []

            if direction == "INGRESS" and "0.0.0.0/0" in source_ranges and allowed:
                findings.append(
                    self._make_finding(
                        finding_id=f"gcp-firewall-public-{getattr(rule, 'name', 'rule')}",
                        severity=Severity.CRITICAL,
                        title="Firewall rule allows public ingress",
                        description=(
                            f"Firewall rule '{getattr(rule, 'name', 'unknown')}' permits ingress from 0.0.0.0/0."
                        ),
                        resource_id=getattr(rule, "name", "unknown"),
                        resource_type="gcp:compute:firewall",
                        recommendation="Restrict source ranges and expose only required ports/services.",
                        compliance_issues=[_cis("3.6", "Ensure no broad public ingress firewall rules")],
                    )
                )

        return findings

    def _check_unencrypted_storage(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []

        # GCP encrypts disks at rest by default; this check flags disks without CMEK as posture gap.
        for zone, scoped_list in self.disks_client.aggregated_list(project=self.project_id):
            disks = getattr(scoped_list, "disks", None) or []
            for disk in disks:
                disk_name = getattr(disk, "name", "unknown")
                kms_key = getattr(getattr(disk, "disk_encryption_key", None), "kms_key_name", None)
                if not kms_key:
                    findings.append(
                        self._make_finding(
                            finding_id=f"gcp-disk-cmek-missing-{disk_name}",
                            severity=Severity.MEDIUM,
                            title="Compute disk lacks customer-managed encryption key",
                            description=(
                                f"Disk '{disk_name}' in '{zone}' does not use CMEK. "
                                "Google-managed keys are used by default."
                            ),
                            resource_id=disk_name,
                            resource_type="gcp:compute:disk",
                            recommendation="Configure CMEK for sensitive workloads requiring customer key control.",
                            compliance_issues=[_cis("3.11", "Ensure disk volumes use strong encryption controls")],
                        )
                    )

        return findings

    def _check_over_privileged_iam(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []
        project_name = f"projects/{self.project_id}"
        policy = self.projects_client.get_iam_policy(request={"resource": project_name})

        high_priv_roles = {"roles/owner", "roles/editor"}
        for binding in getattr(policy, "bindings", []):
            role = binding.get("role", "")
            members = binding.get("members", [])

            if role in high_priv_roles:
                findings.append(
                    self._make_finding(
                        finding_id=f"gcp-iam-overprivileged-{role.split('/')[-1]}",
                        severity=Severity.HIGH,
                        title="Project has broad privileged role assignments",
                        description=f"Role '{role}' is assigned to {len(members)} principal(s).",
                        resource_id=project_name,
                        resource_type="gcp:iam:project-policy",
                        recommendation="Replace owner/editor roles with least-privilege custom or predefined roles.",
                        compliance_issues=[_cis("1.1", "Ensure IAM users are not assigned excessive privileges")],
                        metadata={"members": members},
                    )
                )

            if set(members).intersection({"allUsers", "allAuthenticatedUsers"}):
                findings.append(
                    self._make_finding(
                        finding_id=f"gcp-iam-public-binding-{role.split('/')[-1]}",
                        severity=Severity.CRITICAL,
                        title="IAM policy grants role to public principals",
                        description=f"Role '{role}' is assigned to public principal(s): {members}.",
                        resource_id=project_name,
                        resource_type="gcp:iam:project-policy",
                        recommendation="Remove public principals from IAM bindings.",
                        compliance_issues=[_cis("1.7", "Ensure no IAM roles are granted to anonymous users")],
                    )
                )

        return findings

    def _check_root_mfa(self) -> list[CloudFinding]:
        # GCP uses Google identities and organization policy controls rather than a root account.
        return [
            self._make_finding(
                finding_id="gcp-root-mfa-not-applicable",
                severity=Severity.INFO,
                title="Root MFA check not directly applicable",
                description=(
                    "GCP does not expose a root account primitive. Enforce MFA for privileged Google accounts "
                    "and admins via organization policy and IdP controls."
                ),
                resource_id=f"projects/{self.project_id}",
                resource_type="gcp:organization",
                recommendation="Require MFA in Google Workspace/Cloud Identity for admin and high-privilege users.",
                compliance_issues=[_cis("1.4", "Ensure MFA is enabled for administrative accounts")],
            )
        ]

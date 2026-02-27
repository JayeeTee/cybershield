"""Azure cloud security posture scanner."""

from __future__ import annotations

import logging
from typing import Any

from .base import CloudScannerBase
from .models import CloudFinding, CloudProvider, ComplianceIssue, Severity

logger = logging.getLogger(__name__)

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.authorization import AuthorizationManagementClient
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.network import NetworkManagementClient
    from azure.mgmt.resource import SubscriptionClient
    from azure.mgmt.sql import SqlManagementClient
    from azure.mgmt.storage import StorageManagementClient
except Exception:  # noqa: BLE001
    DefaultAzureCredential = None
    AuthorizationManagementClient = None
    ComputeManagementClient = None
    NetworkManagementClient = None
    SubscriptionClient = None
    SqlManagementClient = None
    StorageManagementClient = None


def _cis(control_id: str, description: str) -> ComplianceIssue:
    return ComplianceIssue(framework="CIS Microsoft Azure Foundations Benchmark", control_id=control_id, description=description)


class AzureScanner(CloudScannerBase):
    """Scanner implementing common Azure CSPM checks."""

    def __init__(
        self,
        *,
        subscription_id: str | None = None,
        credential: Any | None = None,
        storage_client: Any | None = None,
        network_client: Any | None = None,
        compute_client: Any | None = None,
        sql_client: Any | None = None,
        authorization_client: Any | None = None,
    ) -> None:
        super().__init__(CloudProvider.AZURE)

        self.subscription_id = subscription_id
        self.credential = credential
        self.storage_client = storage_client
        self.network_client = network_client
        self.compute_client = compute_client
        self.sql_client = sql_client
        self.authorization_client = authorization_client

        provided = all(
            [
                self.storage_client,
                self.network_client,
                self.compute_client,
                self.sql_client,
                self.authorization_client,
                self.subscription_id,
            ]
        )
        if provided:
            return

        if not all(
            [
                DefaultAzureCredential,
                AuthorizationManagementClient,
                ComputeManagementClient,
                NetworkManagementClient,
                SqlManagementClient,
                StorageManagementClient,
            ]
        ):
            raise RuntimeError("Azure SDK packages are required unless Azure clients are injected")

        self.credential = self.credential or DefaultAzureCredential()
        self.subscription_id = self.subscription_id or self._discover_subscription_id()
        self.storage_client = self.storage_client or StorageManagementClient(self.credential, self.subscription_id)
        self.network_client = self.network_client or NetworkManagementClient(self.credential, self.subscription_id)
        self.compute_client = self.compute_client or ComputeManagementClient(self.credential, self.subscription_id)
        self.sql_client = self.sql_client or SqlManagementClient(self.credential, self.subscription_id)
        self.authorization_client = self.authorization_client or AuthorizationManagementClient(
            self.credential, self.subscription_id
        )

    def scan(self):
        report = self._new_report()
        self._run_check(report, "exposed_storage_accounts", self._check_exposed_storage)
        self._run_check(report, "public_firewall_rules", self._check_public_firewall_rules)
        self._run_check(report, "unencrypted_disks_databases", self._check_unencrypted_storage)
        self._run_check(report, "over_privileged_iam", self._check_over_privileged_iam)
        self._run_check(report, "missing_root_mfa", self._check_root_mfa)
        return self._complete_report(report)

    def _discover_subscription_id(self) -> str:
        if SubscriptionClient is None:
            raise RuntimeError("azure-mgmt-resource is required to discover subscription id")
        sub_client = SubscriptionClient(self.credential)
        for sub in sub_client.subscriptions.list():
            return sub.subscription_id
        raise RuntimeError("No Azure subscriptions found")

    def _check_exposed_storage(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []
        for account in self.storage_client.storage_accounts.list():
            account_id = getattr(account, "id", "unknown")
            account_name = getattr(account, "name", "unknown")
            public_access = getattr(account, "allow_blob_public_access", False)
            public_network_access = str(getattr(account, "public_network_access", "")).lower()

            if public_access or public_network_access == "enabled":
                findings.append(
                    self._make_finding(
                        finding_id=f"azure-storage-public-{account_name}",
                        severity=Severity.HIGH,
                        title="Azure Storage account may allow public data exposure",
                        description=(
                            f"Storage account '{account_name}' has potentially public configuration "
                            f"(allow_blob_public_access={public_access}, public_network_access={public_network_access})."
                        ),
                        resource_id=account_id,
                        resource_type="azure:storage:account",
                        recommendation="Disable blob public access and restrict storage network exposure.",
                        compliance_issues=[_cis("3.1", "Ensure storage accounts are securely configured")],
                    )
                )

        return findings

    def _check_public_firewall_rules(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []
        for nsg in self.network_client.network_security_groups.list_all():
            nsg_name = getattr(nsg, "name", "unknown")
            nsg_id = getattr(nsg, "id", "unknown")
            rules = getattr(nsg, "security_rules", []) or []
            for rule in rules:
                access = str(getattr(rule, "access", "")).lower()
                direction = str(getattr(rule, "direction", "")).lower()
                source = str(getattr(rule, "source_address_prefix", ""))
                source_ranges = getattr(rule, "source_address_prefixes", None) or []
                port = str(getattr(rule, "destination_port_range", "*"))

                public_source = source in {"*", "0.0.0.0/0", "internet"} or any(
                    item in {"*", "0.0.0.0/0", "internet"} for item in source_ranges
                )

                if access == "allow" and direction == "inbound" and public_source:
                    findings.append(
                        self._make_finding(
                            finding_id=f"azure-nsg-public-{nsg_name}-{getattr(rule, 'name', 'rule')}",
                            severity=Severity.CRITICAL,
                            title="NSG allows public inbound traffic",
                            description=(
                                f"NSG '{nsg_name}' has inbound allow rule '{getattr(rule, 'name', 'unknown')}' "
                                f"from public sources to destination port {port}."
                            ),
                            resource_id=nsg_id,
                            resource_type="azure:network:nsg",
                            recommendation="Limit inbound NSG source ranges and block internet-wide access.",
                            compliance_issues=[_cis("6.1", "Ensure no NSG allows unrestricted inbound access")],
                        )
                    )

        return findings

    def _check_unencrypted_storage(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []

        for disk in self.compute_client.disks.list():
            disk_name = getattr(disk, "name", "unknown")
            disk_id = getattr(disk, "id", "unknown")
            encryption = getattr(disk, "encryption", None)
            if not encryption:
                findings.append(
                    self._make_finding(
                        finding_id=f"azure-disk-unencrypted-{disk_name}",
                        severity=Severity.HIGH,
                        title="Managed disk encryption details missing",
                        description=f"Azure disk '{disk_name}' has no explicit encryption settings.",
                        resource_id=disk_id,
                        resource_type="azure:compute:disk",
                        recommendation="Enable disk encryption sets or platform/customer-managed encryption.",
                        compliance_issues=[_cis("7.1", "Ensure managed disks are encrypted")],
                    )
                )

        for server in self.sql_client.servers.list():
            server_name = getattr(server, "name", "unknown")
            resource_group = self._extract_resource_group(getattr(server, "id", ""))
            if not resource_group:
                continue
            for db in self.sql_client.databases.list_by_server(resource_group, server_name):
                db_name = getattr(db, "name", "unknown")
                tde = self.sql_client.transparent_data_encryptions.get(resource_group, server_name, db_name, "current")
                status = str(getattr(tde, "status", "")).lower()
                if status != "enabled":
                    findings.append(
                        self._make_finding(
                            finding_id=f"azure-sql-unencrypted-{server_name}-{db_name}",
                            severity=Severity.HIGH,
                            title="SQL database TDE is disabled",
                            description=f"Azure SQL database '{server_name}/{db_name}' has TDE status '{status}'.",
                            resource_id=f"{server_name}/{db_name}",
                            resource_type="azure:sql:database",
                            recommendation="Enable Transparent Data Encryption for all SQL databases.",
                            compliance_issues=[_cis("4.1", "Ensure SQL databases use data-at-rest encryption")],
                        )
                    )

        return findings

    def _check_over_privileged_iam(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []
        scope = f"/subscriptions/{self.subscription_id}"

        for role_def in self.authorization_client.role_definitions.list(scope=scope):
            role_id = getattr(role_def, "id", "unknown")
            role_name = getattr(role_def, "role_name", "unknown")
            permissions = getattr(role_def, "permissions", []) or []

            for perm in permissions:
                actions = set(getattr(perm, "actions", []) or [])
                data_actions = set(getattr(perm, "data_actions", []) or [])
                if "*" in actions or "*" in data_actions:
                    findings.append(
                        self._make_finding(
                            finding_id=f"azure-iam-overprivileged-{role_name}",
                            severity=Severity.CRITICAL,
                            title="Azure role grants wildcard privileges",
                            description=f"Role definition '{role_name}' includes wildcard actions.",
                            resource_id=role_id,
                            resource_type="azure:iam:role-definition",
                            recommendation="Reduce wildcard permissions and apply least-privilege role scopes.",
                            compliance_issues=[_cis("1.1", "Ensure least privilege for Azure RBAC roles")],
                        )
                    )
                    break

        return findings

    def _check_root_mfa(self) -> list[CloudFinding]:
        # Azure does not have a root account analog in the same sense as AWS root user.
        return [
            self._make_finding(
                finding_id="azure-root-mfa-not-applicable",
                severity=Severity.INFO,
                title="Root MFA check not directly applicable",
                description=(
                    "Azure uses tenant identities rather than a root account. Review tenant-wide MFA and "
                    "conditional access for privileged roles."
                ),
                resource_id=self.subscription_id or "subscription",
                resource_type="azure:tenant",
                recommendation="Require MFA for Global Admin and privileged roles via Conditional Access.",
                compliance_issues=[_cis("1.2", "Ensure MFA is enabled for all privileged users")],
            )
        ]

    @staticmethod
    def _extract_resource_group(resource_id: str) -> str | None:
        parts = resource_id.split("/")
        for idx, value in enumerate(parts):
            if value.lower() == "resourcegroups" and idx + 1 < len(parts):
                return parts[idx + 1]
        return None

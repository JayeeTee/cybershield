"""AWS cloud security posture scanner."""

from __future__ import annotations

import json
import logging
from typing import Any

from .base import CloudScannerBase
from .models import CloudFinding, CloudProvider, ComplianceIssue, Severity

logger = logging.getLogger(__name__)

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:  # noqa: BLE001
    boto3 = None
    BotoCoreError = Exception
    ClientError = Exception


def _cis(control_id: str, description: str) -> ComplianceIssue:
    return ComplianceIssue(framework="CIS AWS Foundations Benchmark", control_id=control_id, description=description)


class AWSScanner(CloudScannerBase):
    """Scanner implementing common AWS CSPM checks."""

    def __init__(
        self,
        *,
        s3_client: Any | None = None,
        ec2_client: Any | None = None,
        rds_client: Any | None = None,
        iam_client: Any | None = None,
        session: Any | None = None,
    ) -> None:
        super().__init__(CloudProvider.AWS)
        self._session = session
        self.s3_client = s3_client
        self.ec2_client = ec2_client
        self.rds_client = rds_client
        self.iam_client = iam_client

        if not all([self.s3_client, self.ec2_client, self.rds_client, self.iam_client]):
            if boto3 is None:
                raise RuntimeError("boto3 is required unless AWS clients are injected")
            sess = self._session or boto3.session.Session()
            self.s3_client = self.s3_client or sess.client("s3")
            self.ec2_client = self.ec2_client or sess.client("ec2")
            self.rds_client = self.rds_client or sess.client("rds")
            self.iam_client = self.iam_client or sess.client("iam")

    def scan(self):
        report = self._new_report()
        self._run_check(report, "exposed_s3_buckets", self._check_exposed_s3_buckets)
        self._run_check(report, "public_security_groups", self._check_public_security_groups)
        self._run_check(report, "unencrypted_volumes_databases", self._check_unencrypted_storage)
        self._run_check(report, "over_privileged_iam", self._check_over_privileged_iam)
        self._run_check(report, "missing_root_mfa", self._check_root_mfa)
        return self._complete_report(report)

    def _check_exposed_s3_buckets(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []
        buckets = self.s3_client.list_buckets().get("Buckets", [])

        for bucket in buckets:
            name = bucket.get("Name", "unknown")
            is_public = False
            reasons: list[str] = []

            try:
                status = self.s3_client.get_bucket_policy_status(Bucket=name)
                if status.get("PolicyStatus", {}).get("IsPublic"):
                    is_public = True
                    reasons.append("bucket policy allows public access")
            except ClientError:
                logger.debug("Bucket %s has no policy status", name)

            try:
                acl = self.s3_client.get_bucket_acl(Bucket=name)
                for grant in acl.get("Grants", []):
                    uri = grant.get("Grantee", {}).get("URI", "")
                    if uri.endswith("AllUsers") or uri.endswith("AuthenticatedUsers"):
                        is_public = True
                        reasons.append("bucket ACL grants public or authenticated-users access")
                        break
            except (ClientError, BotoCoreError):
                logger.debug("Unable to fetch ACL for bucket %s", name)

            if is_public:
                findings.append(
                    self._make_finding(
                        finding_id=f"aws-s3-public-{name}",
                        severity=Severity.HIGH,
                        title="S3 bucket is publicly accessible",
                        description=f"S3 bucket '{name}' appears publicly accessible ({'; '.join(reasons)}).",
                        resource_id=name,
                        resource_type="aws:s3:bucket",
                        recommendation="Block public access and remove anonymous ACL/policy grants.",
                        compliance_issues=[
                            _cis("2.1.1", "Ensure S3 buckets are not publicly accessible"),
                            _cis("3.1", "Ensure no security group allows unrestricted ingress")
                        ],
                    )
                )

        return findings

    def _check_public_security_groups(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []
        paginator = self.ec2_client.get_paginator("describe_security_groups")
        for page in paginator.paginate():
            for sg in page.get("SecurityGroups", []):
                group_id = sg.get("GroupId", "unknown")
                group_name = sg.get("GroupName", "unknown")
                for permission in sg.get("IpPermissions", []):
                    from_port = permission.get("FromPort", -1)
                    to_port = permission.get("ToPort", -1)
                    proto = permission.get("IpProtocol", "-1")
                    for ipr in permission.get("IpRanges", []):
                        cidr = ipr.get("CidrIp")
                        if cidr == "0.0.0.0/0":
                            findings.append(
                                self._make_finding(
                                    finding_id=f"aws-sg-public-{group_id}-{from_port}-{to_port}-{proto}",
                                    severity=Severity.CRITICAL,
                                    title="Security group allows public ingress",
                                    description=(
                                        f"Security group '{group_name}' ({group_id}) allows ingress from 0.0.0.0/0 "
                                        f"on protocol {proto} ports {from_port}-{to_port}."
                                    ),
                                    resource_id=group_id,
                                    resource_type="aws:ec2:security-group",
                                    recommendation="Restrict ingress CIDRs and expose only approved ports.",
                                    compliance_issues=[_cis("5.2", "Ensure no security groups allow ingress from 0.0.0.0/0")],
                                )
                            )
                    for ipr in permission.get("Ipv6Ranges", []):
                        cidr = ipr.get("CidrIpv6")
                        if cidr == "::/0":
                            findings.append(
                                self._make_finding(
                                    finding_id=f"aws-sg-public-v6-{group_id}-{from_port}-{to_port}-{proto}",
                                    severity=Severity.CRITICAL,
                                    title="Security group allows public IPv6 ingress",
                                    description=(
                                        f"Security group '{group_name}' ({group_id}) allows ingress from ::/0 "
                                        f"on protocol {proto} ports {from_port}-{to_port}."
                                    ),
                                    resource_id=group_id,
                                    resource_type="aws:ec2:security-group",
                                    recommendation="Restrict IPv6 ingress CIDRs and expose only approved ports.",
                                    compliance_issues=[_cis("5.2", "Ensure no security groups allow ingress from 0.0.0.0/0")],
                                )
                            )

        return findings

    def _check_unencrypted_storage(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []

        volumes = self.ec2_client.describe_volumes().get("Volumes", [])
        for volume in volumes:
            if not volume.get("Encrypted", False):
                volume_id = volume.get("VolumeId", "unknown")
                findings.append(
                    self._make_finding(
                        finding_id=f"aws-ebs-unencrypted-{volume_id}",
                        severity=Severity.HIGH,
                        title="EBS volume is not encrypted",
                        description=f"EBS volume '{volume_id}' is not encrypted at rest.",
                        resource_id=volume_id,
                        resource_type="aws:ec2:volume",
                        region=volume.get("AvailabilityZone"),
                        recommendation="Enable EBS encryption and migrate data to encrypted volumes.",
                        compliance_issues=[_cis("2.2.1", "Ensure EBS volume encryption is enabled")],
                    )
                )

        dbs = self.rds_client.describe_db_instances().get("DBInstances", [])
        for db in dbs:
            if not db.get("StorageEncrypted", False):
                db_id = db.get("DBInstanceIdentifier", "unknown")
                findings.append(
                    self._make_finding(
                        finding_id=f"aws-rds-unencrypted-{db_id}",
                        severity=Severity.HIGH,
                        title="RDS instance is not encrypted",
                        description=f"RDS instance '{db_id}' has storage encryption disabled.",
                        resource_id=db_id,
                        resource_type="aws:rds:db-instance",
                        region=db.get("AvailabilityZone") or db.get("DBSubnetGroup", {}).get("VpcId"),
                        recommendation="Enable RDS storage encryption for all production databases.",
                        compliance_issues=[_cis("2.3.1", "Ensure RDS instances are encrypted")],
                    )
                )

        return findings

    def _check_over_privileged_iam(self) -> list[CloudFinding]:
        findings: list[CloudFinding] = []
        paginator = self.iam_client.get_paginator("list_policies")

        for page in paginator.paginate(Scope="Local"):
            for policy in page.get("Policies", []):
                policy_arn = policy.get("Arn", "unknown")
                policy_name = policy.get("PolicyName", "unknown")
                version_id = policy.get("DefaultVersionId")
                if not version_id:
                    continue

                policy_version = self.iam_client.get_policy_version(PolicyArn=policy_arn, VersionId=version_id)
                document = policy_version.get("PolicyVersion", {}).get("Document", {})
                if self._policy_is_over_privileged(document):
                    findings.append(
                        self._make_finding(
                            finding_id=f"aws-iam-overprivileged-{policy_name}",
                            severity=Severity.CRITICAL,
                            title="IAM policy grants wildcard admin access",
                            description=(
                                f"IAM policy '{policy_name}' ({policy_arn}) contains an Allow statement with "
                                "Action='*' and Resource='*'."
                            ),
                            resource_id=policy_arn,
                            resource_type="aws:iam:policy",
                            recommendation="Apply least-privilege IAM permissions and scope actions/resources.",
                            compliance_issues=[_cis("1.16", "Ensure IAM policies follow least privilege")],
                        )
                    )

        return findings

    def _check_root_mfa(self) -> list[CloudFinding]:
        summary = self.iam_client.get_account_summary().get("SummaryMap", {})
        mfa_enabled = summary.get("AccountMFAEnabled", 0)

        if int(mfa_enabled) == 1:
            return []

        return [
            self._make_finding(
                finding_id="aws-root-mfa-disabled",
                severity=Severity.CRITICAL,
                title="Root account MFA is not enabled",
                description="AWS account root user does not have MFA enabled.",
                resource_id="root-account",
                resource_type="aws:iam:root-account",
                recommendation="Enable hardware or virtual MFA on the root account immediately.",
                compliance_issues=[_cis("1.5", "Ensure MFA is enabled for the root account")],
            )
        ]

    @staticmethod
    def _policy_is_over_privileged(document: dict[str, Any] | str) -> bool:
        if isinstance(document, str):
            try:
                document = json.loads(document)
            except json.JSONDecodeError:
                return False

        statements = document.get("Statement", [])
        if isinstance(statements, dict):
            statements = [statements]

        for statement in statements:
            if statement.get("Effect") != "Allow":
                continue
            actions = statement.get("Action", [])
            resources = statement.get("Resource", [])

            if isinstance(actions, str):
                actions = [actions]
            if isinstance(resources, str):
                resources = [resources]

            if "*" in actions and "*" in resources:
                return True

        return False

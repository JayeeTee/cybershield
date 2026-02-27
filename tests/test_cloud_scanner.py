"""Tests for cloud security scanners."""

from __future__ import annotations

from types import SimpleNamespace

from src.scanners.cloud.aws_scanner import AWSScanner
from src.scanners.cloud.azure_scanner import AzureScanner
from src.scanners.cloud.gcp_scanner import GCPScanner
from src.scanners.cloud.models import CloudProvider


class _Paginator:
    def __init__(self, pages):
        self._pages = pages

    def paginate(self, **kwargs):
        return self._pages


class FakeAWSS3Client:
    def list_buckets(self):
        return {"Buckets": [{"Name": "public-bucket"}]}

    def get_bucket_policy_status(self, Bucket):
        return {"PolicyStatus": {"IsPublic": True}}

    def get_bucket_acl(self, Bucket):
        return {"Grants": []}


class FakeAWSEC2Client:
    def get_paginator(self, name):
        assert name == "describe_security_groups"
        return _Paginator(
            [
                {
                    "SecurityGroups": [
                        {
                            "GroupId": "sg-123",
                            "GroupName": "public-sg",
                            "IpPermissions": [
                                {
                                    "IpProtocol": "tcp",
                                    "FromPort": 22,
                                    "ToPort": 22,
                                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                                }
                            ],
                        }
                    ]
                }
            ]
        )

    def describe_volumes(self):
        return {"Volumes": [{"VolumeId": "vol-123", "Encrypted": False, "AvailabilityZone": "us-east-1a"}]}


class FakeAWSRDSClient:
    def describe_db_instances(self):
        return {"DBInstances": [{"DBInstanceIdentifier": "db-1", "StorageEncrypted": False}]}


class FakeAWSIAMClient:
    def get_paginator(self, name):
        assert name == "list_policies"
        return _Paginator(
            [
                {
                    "Policies": [
                        {
                            "Arn": "arn:aws:iam::123456789012:policy/AdminPolicy",
                            "PolicyName": "AdminPolicy",
                            "DefaultVersionId": "v1",
                        }
                    ]
                }
            ]
        )

    def get_policy_version(self, PolicyArn, VersionId):
        return {
            "PolicyVersion": {
                "Document": {
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "*",
                            "Resource": "*",
                        }
                    ]
                }
            }
        }

    def get_account_summary(self):
        return {"SummaryMap": {"AccountMFAEnabled": 0}}


def test_aws_scanner_detects_core_findings():
    scanner = AWSScanner(
        s3_client=FakeAWSS3Client(),
        ec2_client=FakeAWSEC2Client(),
        rds_client=FakeAWSRDSClient(),
        iam_client=FakeAWSIAMClient(),
    )

    report = scanner.scan()

    assert report.provider == CloudProvider.AWS
    assert report.finding_count >= 6
    assert report.errors == []
    titles = {f.title for f in report.findings}
    assert "S3 bucket is publicly accessible" in titles
    assert "Security group allows public ingress" in titles
    assert "EBS volume is not encrypted" in titles
    assert "RDS instance is not encrypted" in titles
    assert "IAM policy grants wildcard admin access" in titles
    assert "Root account MFA is not enabled" in titles


class FakeAzureStorageClient:
    class storage_accounts:
        @staticmethod
        def list():
            return [
                SimpleNamespace(
                    id="/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/acc1",
                    name="acc1",
                    allow_blob_public_access=True,
                    public_network_access="Enabled",
                )
            ]


class FakeAzureNetworkClient:
    class network_security_groups:
        @staticmethod
        def list_all():
            return [
                SimpleNamespace(
                    id="/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Network/networkSecurityGroups/nsg1",
                    name="nsg1",
                    security_rules=[
                        SimpleNamespace(
                            name="allow-internet",
                            access="Allow",
                            direction="Inbound",
                            source_address_prefix="*",
                            source_address_prefixes=None,
                            destination_port_range="22",
                        )
                    ],
                )
            ]


class FakeAzureComputeClient:
    class disks:
        @staticmethod
        def list():
            return [SimpleNamespace(name="disk1", id="disk1", encryption=None)]


class FakeAzureSqlClient:
    class servers:
        @staticmethod
        def list():
            return [
                SimpleNamespace(
                    name="sql1",
                    id="/subscriptions/sub-1/resourceGroups/rg/providers/Microsoft.Sql/servers/sql1",
                )
            ]

    class databases:
        @staticmethod
        def list_by_server(resource_group, server_name):
            return [SimpleNamespace(name="db1")]

    class transparent_data_encryptions:
        @staticmethod
        def get(resource_group, server_name, db_name, tde_name):
            return SimpleNamespace(status="Disabled")


class FakeAzureAuthorizationClient:
    class role_definitions:
        @staticmethod
        def list(scope):
            return [
                SimpleNamespace(
                    id="role-1",
                    role_name="CustomAdmin",
                    permissions=[SimpleNamespace(actions=["*"], data_actions=[])],
                )
            ]


def test_azure_scanner_detects_core_findings():
    scanner = AzureScanner(
        subscription_id="sub-1",
        storage_client=FakeAzureStorageClient(),
        network_client=FakeAzureNetworkClient(),
        compute_client=FakeAzureComputeClient(),
        sql_client=FakeAzureSqlClient(),
        authorization_client=FakeAzureAuthorizationClient(),
    )

    report = scanner.scan()

    assert report.provider == CloudProvider.AZURE
    assert report.finding_count >= 6
    titles = {f.title for f in report.findings}
    assert "Azure Storage account may allow public data exposure" in titles
    assert "NSG allows public inbound traffic" in titles
    assert "Managed disk encryption details missing" in titles
    assert "SQL database TDE is disabled" in titles
    assert "Azure role grants wildcard privileges" in titles
    assert "Root MFA check not directly applicable" in titles


class FakeGCPPolicy:
    def __init__(self):
        self.bindings = [
            {"role": "roles/owner", "members": ["user:admin@example.com"]},
            {"role": "roles/viewer", "members": ["allUsers"]},
        ]


class FakeGCPBucketPolicy:
    def __init__(self):
        self.bindings = [{"role": "roles/storage.objectViewer", "members": ["allUsers"]}]


class FakeGCPBucket:
    def __init__(self, name: str):
        self.name = name
        self.iam_configuration = SimpleNamespace(public_access_prevention="inherited")

    def get_iam_policy(self, requested_policy_version=3):
        return FakeGCPBucketPolicy()


class FakeGCPStorageClient:
    def list_buckets(self, project):
        return [FakeGCPBucket("bucket-1")]


class FakeGCPFirewallsClient:
    def list(self, project):
        return [SimpleNamespace(name="allow-all", direction="INGRESS", source_ranges=["0.0.0.0/0"], allowed=[{"IPProtocol": "tcp"}])]


class FakeGCPDisksClient:
    def aggregated_list(self, project):
        return [("zones/us-central1-a", SimpleNamespace(disks=[SimpleNamespace(name="disk-1", disk_encryption_key=None)]))]


class FakeGCPProjectsClient:
    def get_iam_policy(self, request):
        return FakeGCPPolicy()


def test_gcp_scanner_detects_core_findings():
    scanner = GCPScanner(
        project_id="project-1",
        storage_client=FakeGCPStorageClient(),
        firewalls_client=FakeGCPFirewallsClient(),
        disks_client=FakeGCPDisksClient(),
        projects_client=FakeGCPProjectsClient(),
    )

    report = scanner.scan()

    assert report.provider == CloudProvider.GCP
    assert report.finding_count >= 6
    titles = {f.title for f in report.findings}
    assert "Cloud Storage bucket is publicly accessible" in titles
    assert "Firewall rule allows public ingress" in titles
    assert "Compute disk lacks customer-managed encryption key" in titles
    assert "Project has broad privileged role assignments" in titles
    assert "IAM policy grants role to public principals" in titles
    assert "Root MFA check not directly applicable" in titles


def test_scanner_continues_when_check_raises_error():
    scanner = AWSScanner(
        s3_client=FakeAWSS3Client(),
        ec2_client=FakeAWSEC2Client(),
        rds_client=FakeAWSRDSClient(),
        iam_client=FakeAWSIAMClient(),
    )

    scanner._check_public_security_groups = lambda: (_ for _ in ()).throw(RuntimeError("boom"))  # type: ignore[method-assign]
    report = scanner.scan()

    assert report.finding_count >= 1
    assert any("public_security_groups failed" in error for error in report.errors)

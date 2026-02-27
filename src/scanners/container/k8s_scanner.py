"""Kubernetes security scanner for workload and cluster policy posture."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .models import ComplianceIssue, ContainerFinding, ContainerScanReport, ContainerSeverity, FindingCategory


def _cis(control_id: str, description: str) -> ComplianceIssue:
    return ComplianceIssue(framework="CIS Kubernetes Benchmark", control_id=control_id, description=description)


class KubernetesScanner:
    """Manifest/API driven Kubernetes security scanner."""

    def scan(self, resources: dict[str, list[dict[str, Any]]]) -> ContainerScanReport:
        now = datetime.now(timezone.utc)
        report = ContainerScanReport(scanner_name="k8s-scanner", target="kubernetes-cluster", started_at=now, completed_at=now)

        pods = resources.get("pods", [])
        service_accounts = resources.get("service_accounts", [])
        roles = resources.get("roles", []) + resources.get("cluster_roles", [])
        role_bindings = resources.get("role_bindings", []) + resources.get("cluster_role_bindings", [])
        network_policies = resources.get("network_policies", [])

        report.findings.extend(self._check_pod_security(pods))
        report.findings.extend(self._check_rbac(roles, role_bindings))
        report.findings.extend(self._check_network_policies(pods, network_policies))
        report.findings.extend(self._check_service_accounts(pods, service_accounts, role_bindings))

        report.completed_at = datetime.now(timezone.utc)
        return report

    def _check_pod_security(self, pods: list[dict[str, Any]]) -> list[ContainerFinding]:
        findings: list[ContainerFinding] = []

        for pod in pods:
            metadata = pod.get("metadata", {})
            spec = pod.get("spec", {})
            pod_name = metadata.get("name", "unknown")
            namespace = metadata.get("namespace", "default")
            pod_ref = f"{namespace}/{pod_name}"

            if spec.get("hostNetwork") or spec.get("hostPID") or spec.get("hostIPC"):
                findings.append(
                    ContainerFinding(
                        finding_id=f"k8s-pod-host-namespace-{pod_ref}",
                        category=FindingCategory.KUBERNETES,
                        severity=ContainerSeverity.HIGH,
                        title="Pod shares host namespaces",
                        description="Pod enables hostNetwork/hostPID/hostIPC which weakens isolation.",
                        resource_id=pod_ref,
                        resource_type="k8s:pod",
                        recommendation="Disable host namespace sharing for regular workloads.",
                        compliance_issues=[_cis("5.2.4", "Minimize pod host namespace sharing")],
                    )
                )

            pod_sc = spec.get("securityContext", {})
            if pod_sc.get("runAsNonRoot") is False:
                findings.append(
                    ContainerFinding(
                        finding_id=f"k8s-pod-runasroot-{pod_ref}",
                        category=FindingCategory.KUBERNETES,
                        severity=ContainerSeverity.HIGH,
                        title="Pod allows root execution",
                        description="Pod security context explicitly disables runAsNonRoot.",
                        resource_id=pod_ref,
                        resource_type="k8s:pod",
                        recommendation="Set runAsNonRoot=true at pod or container security context.",
                        compliance_issues=[_cis("5.2.5", "Ensure containers do not run as root")],
                    )
                )

            for container in spec.get("containers", []) or []:
                name = container.get("name", "container")
                c_sc = container.get("securityContext", {}) or {}
                if c_sc.get("privileged") is True:
                    findings.append(
                        ContainerFinding(
                            finding_id=f"k8s-pod-privileged-{pod_ref}-{name}",
                            category=FindingCategory.KUBERNETES,
                            severity=ContainerSeverity.CRITICAL,
                            title="Privileged container detected",
                            description=f"Container '{name}' in pod '{pod_ref}' runs privileged.",
                            resource_id=pod_ref,
                            resource_type="k8s:pod",
                            recommendation="Avoid privileged containers and use fine-grained capabilities.",
                            compliance_issues=[_cis("5.2.1", "Minimize privileged containers")],
                        )
                    )
                if c_sc.get("allowPrivilegeEscalation") is True:
                    findings.append(
                        ContainerFinding(
                            finding_id=f"k8s-pod-privesc-{pod_ref}-{name}",
                            category=FindingCategory.KUBERNETES,
                            severity=ContainerSeverity.HIGH,
                            title="Privilege escalation allowed",
                            description=f"Container '{name}' allows privilege escalation.",
                            resource_id=pod_ref,
                            resource_type="k8s:pod",
                            recommendation="Set allowPrivilegeEscalation=false.",
                            compliance_issues=[_cis("5.2.8", "Disallow privilege escalation")],
                        )
                    )

        return findings

    def _check_rbac(
        self,
        roles: list[dict[str, Any]],
        role_bindings: list[dict[str, Any]],
    ) -> list[ContainerFinding]:
        findings: list[ContainerFinding] = []

        for role in roles:
            metadata = role.get("metadata", {})
            name = metadata.get("name", "unknown")
            namespace = metadata.get("namespace", "cluster")
            role_ref = f"{namespace}/{name}"

            rules = role.get("rules", []) or []
            for rule in rules:
                verbs = set(rule.get("verbs", []) or [])
                resources = set(rule.get("resources", []) or [])
                if "*" in verbs or "*" in resources:
                    findings.append(
                        ContainerFinding(
                            finding_id=f"k8s-rbac-wildcard-{role_ref}",
                            category=FindingCategory.KUBERNETES,
                            severity=ContainerSeverity.HIGH,
                            title="RBAC role grants wildcard access",
                            description=f"Role '{role_ref}' includes wildcard verbs/resources.",
                            resource_id=role_ref,
                            resource_type="k8s:rbac:role",
                            recommendation="Replace wildcard RBAC permissions with explicit least-privilege rules.",
                            compliance_issues=[_cis("5.1.3", "Minimize wildcard RBAC privileges")],
                        )
                    )
                    break

        for binding in role_bindings:
            metadata = binding.get("metadata", {})
            binding_name = metadata.get("name", "unknown")
            namespace = metadata.get("namespace", "cluster")
            binding_ref = f"{namespace}/{binding_name}"
            role_ref = binding.get("roleRef", {})
            role_name = role_ref.get("name", "")

            for subject in binding.get("subjects", []) or []:
                subject_kind = subject.get("kind", "")
                subject_name = subject.get("name", "")
                if role_name == "cluster-admin":
                    findings.append(
                        ContainerFinding(
                            finding_id=f"k8s-rbac-cluster-admin-{binding_ref}-{subject_name}",
                            category=FindingCategory.KUBERNETES,
                            severity=ContainerSeverity.CRITICAL,
                            title="Cluster-admin role binding detected",
                            description=(
                                f"Binding '{binding_ref}' grants cluster-admin to {subject_kind}/{subject_name}."
                            ),
                            resource_id=binding_ref,
                            resource_type="k8s:rbac:binding",
                            recommendation="Restrict cluster-admin bindings and use scoped roles.",
                            compliance_issues=[_cis("5.1.1", "Minimize cluster-admin privileges")],
                        )
                    )
                if subject_kind == "Group" and subject_name in {"system:unauthenticated", "system:authenticated"}:
                    findings.append(
                        ContainerFinding(
                            finding_id=f"k8s-rbac-public-group-{binding_ref}-{subject_name}",
                            category=FindingCategory.KUBERNETES,
                            severity=ContainerSeverity.CRITICAL,
                            title="RBAC binding includes broad system group",
                            description=(
                                f"Binding '{binding_ref}' assigns access to broad group '{subject_name}'."
                            ),
                            resource_id=binding_ref,
                            resource_type="k8s:rbac:binding",
                            recommendation="Remove broad system groups from privileged RBAC bindings.",
                            compliance_issues=[_cis("5.1.2", "Avoid anonymous/broad RBAC bindings")],
                        )
                    )

        return findings

    def _check_network_policies(
        self,
        pods: list[dict[str, Any]],
        network_policies: list[dict[str, Any]],
    ) -> list[ContainerFinding]:
        findings: list[ContainerFinding] = []

        namespaces_with_pods = {pod.get("metadata", {}).get("namespace", "default") for pod in pods}
        namespaces_with_policy = {
            policy.get("metadata", {}).get("namespace", "default") for policy in network_policies
        }

        for namespace in sorted(namespaces_with_pods - namespaces_with_policy):
            findings.append(
                ContainerFinding(
                    finding_id=f"k8s-networkpolicy-missing-{namespace}",
                    category=FindingCategory.KUBERNETES,
                    severity=ContainerSeverity.MEDIUM,
                    title="Namespace lacks NetworkPolicy",
                    description=(
                        f"Namespace '{namespace}' has pods but no NetworkPolicy. East-west traffic may be unrestricted."
                    ),
                    resource_id=namespace,
                    resource_type="k8s:namespace",
                    recommendation="Define default-deny ingress/egress NetworkPolicies for each namespace.",
                    compliance_issues=[_cis("5.3.2", "Ensure network segmentation controls are used")],
                )
            )

        for policy in network_policies:
            metadata = policy.get("metadata", {})
            spec = policy.get("spec", {})
            policy_name = metadata.get("name", "unknown")
            namespace = metadata.get("namespace", "default")
            policy_ref = f"{namespace}/{policy_name}"

            pod_selector = spec.get("podSelector", {})
            ingress = spec.get("ingress", [])
            if pod_selector == {} and ingress == [{}]:
                findings.append(
                    ContainerFinding(
                        finding_id=f"k8s-networkpolicy-open-{policy_ref}",
                        category=FindingCategory.KUBERNETES,
                        severity=ContainerSeverity.HIGH,
                        title="Overly permissive NetworkPolicy",
                        description=f"NetworkPolicy '{policy_ref}' appears to allow unrestricted ingress.",
                        resource_id=policy_ref,
                        resource_type="k8s:networkpolicy",
                        recommendation="Constrain pod selectors and ingress peers/ports with least privilege.",
                        compliance_issues=[_cis("5.3.2", "Restrict network policy scope")],
                    )
                )

        return findings

    def _check_service_accounts(
        self,
        pods: list[dict[str, Any]],
        service_accounts: list[dict[str, Any]],
        role_bindings: list[dict[str, Any]],
    ) -> list[ContainerFinding]:
        findings: list[ContainerFinding] = []

        for pod in pods:
            metadata = pod.get("metadata", {})
            spec = pod.get("spec", {})
            namespace = metadata.get("namespace", "default")
            name = metadata.get("name", "unknown")
            pod_ref = f"{namespace}/{name}"

            service_account = spec.get("serviceAccountName", "default")
            if service_account == "default":
                findings.append(
                    ContainerFinding(
                        finding_id=f"k8s-sa-default-{pod_ref}",
                        category=FindingCategory.KUBERNETES,
                        severity=ContainerSeverity.MEDIUM,
                        title="Pod uses default service account",
                        description=f"Pod '{pod_ref}' uses the default service account.",
                        resource_id=pod_ref,
                        resource_type="k8s:pod",
                        recommendation="Create dedicated least-privilege service accounts per workload.",
                        compliance_issues=[_cis("5.1.5", "Avoid default service accounts for workloads")],
                    )
                )

            if spec.get("automountServiceAccountToken") is not False:
                findings.append(
                    ContainerFinding(
                        finding_id=f"k8s-sa-token-mount-{pod_ref}",
                        category=FindingCategory.KUBERNETES,
                        severity=ContainerSeverity.MEDIUM,
                        title="Service account token automount enabled",
                        description=f"Pod '{pod_ref}' allows automount of service account token.",
                        resource_id=pod_ref,
                        resource_type="k8s:pod",
                        recommendation="Disable automountServiceAccountToken unless Kubernetes API access is required.",
                        compliance_issues=[_cis("5.1.6", "Minimize automatic service account token mounting")],
                    )
                )

        for sa in service_accounts:
            metadata = sa.get("metadata", {})
            namespace = metadata.get("namespace", "default")
            name = metadata.get("name", "default")
            sa_ref = f"{namespace}/{name}"
            if sa.get("automountServiceAccountToken") is not False:
                findings.append(
                    ContainerFinding(
                        finding_id=f"k8s-sa-automount-{sa_ref}",
                        category=FindingCategory.KUBERNETES,
                        severity=ContainerSeverity.LOW,
                        title="Service account token automount not disabled",
                        description=(
                            f"Service account '{sa_ref}' does not explicitly disable token automount."
                        ),
                        resource_id=sa_ref,
                        resource_type="k8s:serviceaccount",
                        recommendation="Set automountServiceAccountToken=false where API tokens are unnecessary.",
                    )
                )

        privileged_sas: set[str] = set()
        for binding in role_bindings:
            role_ref = binding.get("roleRef", {})
            role_name = role_ref.get("name", "")
            if role_name != "cluster-admin":
                continue
            for subject in binding.get("subjects", []) or []:
                if subject.get("kind") == "ServiceAccount":
                    sa_ns = subject.get("namespace", "default")
                    sa_name = subject.get("name", "default")
                    privileged_sas.add(f"{sa_ns}/{sa_name}")

        for sa_ref in sorted(privileged_sas):
            findings.append(
                ContainerFinding(
                    finding_id=f"k8s-sa-cluster-admin-{sa_ref}",
                    category=FindingCategory.KUBERNETES,
                    severity=ContainerSeverity.CRITICAL,
                    title="Service account bound to cluster-admin",
                    description=f"Service account '{sa_ref}' is granted cluster-admin privileges.",
                    resource_id=sa_ref,
                    resource_type="k8s:serviceaccount",
                    recommendation="Replace cluster-admin binding with scoped Role/ClusterRole permissions.",
                    compliance_issues=[_cis("5.1.1", "Minimize cluster-admin assignments")],
                )
            )

        return findings

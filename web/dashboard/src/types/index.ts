export interface Finding {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: 'cloud' | 'secrets' | 'threat_intel' | 'container' | 'network';
  source: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface DashboardSummary {
  total_findings: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  last_scan: string;
}

export interface CloudFinding {
  provider: 'aws' | 'azure' | 'gcp';
  resource: string;
  issue: string;
  severity: string;
  region: string;
  recommendation: string;
}

export interface SecretsFinding {
  file_path: string;
  secret_type: string;
  line_number: number;
  severity: string;
  remediation: string;
}

export interface ThreatIntelIOC {
  ioc_type: string;
  value: string;
  threat_type: string;
  confidence: number;
  source: string;
  first_seen: string;
  last_seen: string;
}

export interface ContainerFinding {
  image: string;
  vulnerability: string;
  severity: string;
  package: string;
  installed_version: string;
  fixed_version: string;
}

export interface NetworkFinding {
  src_ip: string;
  dst_ip: string;
  port: number;
  protocol: string;
  anomaly_type: string;
  severity: string;
  timestamp: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  username: string;
  email: string;
  role: string;
}

# CyberShield

[![CI/CD](https://github.com/JayeeTee/cybershield/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/JayeeTee/cybershield/actions/workflows/ci.yml)
[![Security Scan](https://github.com/JayeeTee/cybershield/workflows/Security%20Scan/badge.svg)](https://github.com/JayeeTee/cybershield/actions/workflows/security.yml)
[![Docker Build](https://github.com/JayeeTee/cybershield/workflows/Docker%20Build/badge.svg)](https://github.com/JayeeTee/cybershield/actions/workflows/docker.yml)
[![codecov](https://codecov.io/gh/JayeeTee/cybershield/branch/main/graph/badge.svg)](https://codecov.io/gh/JayeeTee/cybershield)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Unified cybersecurity platform for continuous risk visibility across cloud, code, containers, and network activity.

## ✅ Current Status: Backend Complete (v0.1.0)

**Built in one day (Feb 27, 2026):**

✅ **All 5 Security Modules:**
1. Cloud Security Scanner - AWS/Azure/GCP CSPM with CIS benchmarks
2. Secrets Scanner - API key detection, regex patterns, auto-remediation
3. Threat Intelligence - MITRE ATT&CK, CVE, multiple threat feeds
4. Container Security - Trivy/Grype scanning, Kubernetes hardening
5. Network Traffic Analyzer - PCAP analysis, port scanning, C2 detection

✅ **FastAPI REST API:**
- Scanner endpoints (cloud, secrets, container, network)
- Threat intel endpoints (IOC, CVE, feeds)
- Dashboard endpoints (summary, metrics, findings)
- JWT authentication + rate limiting
- WebSocket support for real-time updates

✅ **Code Quality:**
- Pydantic v2 validation
- Type hints throughout
- Comprehensive error handling
- CIS compliance mappings
- Test suites for all modules

**Coming Next:**
- [ ] React dashboard frontend
- [ ] Database migrations
- [ ] Integration tests
- [ ] Deployment guides

## Overview

CyberShield consolidates five critical security capabilities into one platform:

1. **Cloud Security Posture Monitoring (CSPM)**
2. **Secrets Scanning & Auto-Remediation**
3. **Threat Intelligence Aggregation**
4. **Container Security Scanner**
5. **Network Traffic Analysis**

The platform ingests telemetry from cloud providers, source repositories, container runtimes, and network sensors, then correlates findings into prioritized, actionable risk insights.

## Core Features

- Multi-cloud posture assessment (AWS, Azure, GCP)
- Policy-as-code compliance checks (CIS, NIST, custom policies)
- Repository and artifact secrets scanning
- Threat feed ingestion and IOC matching
- Container image vulnerability and misconfiguration scanning
- Runtime container behavior monitoring
- Flow and packet metadata analytics
- Correlation engine for cross-domain alert fusion
- Risk scoring, triage queues, and remediation workflows
- API-first design with dashboard for SOC and platform teams

## Architecture

```text
                        +----------------------+
                        |     Web Dashboard    |
                        |  (SOC / SecOps UI)   |
                        +----------+-----------+
                                   |
                          REST/GraphQL API
                                   |
+------------------+     +---------v----------+     +------------------+
| Cloud Connectors |---->|  Ingestion Layer   |<----| Repo Connectors  |
| AWS/Azure/GCP    |     | (events, scans)    |     | GitHub/GitLab    |
+------------------+     +---------+----------+     +------------------+
                                   |
                          +--------v---------+
                          | Message Bus/Queue|
                          +---+---+---+---+-+
                              |   |   |   |
      +-----------------------+   |   |   +------------------------+
      |                           |   |                            |
+-----v---------------+   +-------v-------+   +--------------------v----+
| Cloud Posture Engine|   | Secrets Engine|   | Container Sec Engine     |
| Misconfig + policy  |   | Detection +   |   | Image + runtime analysis |
+----------+----------+   | validation    |   +------------+-------------+
           |              +-------+-------+                |
           |                      |                        |
           +------------------+   |   +--------------------+
                              |   |   |
                      +-------v---v---v--------+
                      | Threat Intel + Network |
                      | IOC matching + anomaly |
                      +-----------+------------+
                                  |
                        +---------v----------+
                        | Correlation Engine |
                        | Risk scoring/prio  |
                        +---------+----------+
                                  |
                        +---------v----------+
                        | Alerts + Reporting |
                        | SIEM/SOAR/Webhooks |
                        +--------------------+
```

## Tech Stack

- **Backend:** Python 3.11+ (core engine), Go (high-performance services)
- **Data:** PostgreSQL, Redis, OpenSearch
- **Messaging:** NATS or Kafka
- **Frontend:** React + TypeScript
- **Deployment:** Docker, Kubernetes, Terraform
- **CI/CD:** GitHub Actions

## Quick Start

### 1. Prerequisites

- Docker 24+
- Docker Compose v2+
- Python 3.11+
- Node.js 20+ (for dashboard)
- Make

### 2. Clone and Configure

```bash
git clone https://github.com/<your-username>/cybershield.git
cd cybershield
cp .env.example .env
```

### 3. Start Local Dependencies

```bash
docker compose up -d
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run API Server

```bash
python -m cybershield.api
```

### 6. Run Dashboard

```bash
cd web/dashboard
npm install
npm run dev
```

Visit `http://localhost:3000` to access the dashboard.

## Configuration

Environment variables are managed via `.env`:

```bash
# Cloud Providers
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AZURE_SUBSCRIPTION_ID=your-subscription
GCP_PROJECT_ID=your-project

# Threat Intelligence
VIRUSTOTAL_API_KEY=your-key
ALIENVAULT_API_KEY=your-key

# Database
DATABASE_URL=postgresql://localhost/cybershield
REDIS_URL=redis://localhost:6379

# Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

## Modules

### 1. Cloud Security Posture
- AWS, Azure, GCP security checks
- CIS benchmark compliance
- Custom policy support
- Real-time drift detection

### 2. Secrets Scanner
- Git repository scanning
- Cloud storage (S3, Blob, GCS)
- Docker image layers
- Auto-redaction & rotation

### 3. Threat Intelligence
- Multiple threat feeds
- IOC matching
- IP/domain reputation
- MITRE ATT&CK mapping

### 4. Container Security
- CVE database checks
- Base image analysis
- Runtime monitoring
- Kubernetes integration

### 5. Network Analysis
- Traffic capture
- Anomaly detection (ML)
- Attack signatures
- Flow visualization

## API Documentation

API endpoints are documented with OpenAPI:

```bash
# View API docs
open http://localhost:8000/docs
```

## Development

### Run Tests

```bash
pytest tests/
```

### Run Linter

```bash
flake8 cybershield/
black cybershield/
```

### Build Docker Image

```bash
docker build -t cybershield:latest .
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🔒 Security

### Default Credentials

**⚠️ IMPORTANT:** This repository contains default credentials for **development and testing only**.

- **Admin Login:** `admin` / `cybershield`
- **Database:** `cybershield` / `password`

**These must be changed before production deployment!** See [SECURITY.md](SECURITY.md) for details.

### Security Best Practices

- ✅ No real API keys or passwords committed to git
- ✅ `.env` files excluded via `.gitignore`
- ✅ Test credentials isolated from production configs
- ✅ Docker configs use environment variables
- ✅ Pre-commit hooks for secret scanning (recommended)

- ✅ Weekly dependency vulnerability scanning

### Reporting Security Issues

Found a vulnerability? Please email **security@example.com** instead of opening a public issue.

### Security Documentation

- **Full Security Policy:** See [SECURITY.md](SECURITY.md)
- **Default Credentials:** Change before production!
- **Production Security Checklist:** See SECURITY.md#security-checklist

## License

MIT License - see [LICENSE](LICENSE) for details.

## Roadmap

- [ ] Kubernetes operator for auto-remediation
- [ ] Machine learning for anomaly detection
- [ ] Mobile app for alerts
- [ ] SIEM integrations (Splunk, QRadar)
- [ ] SOAR playbooks

## Authors

Built with ❤️ by the CyberShield Team

## Acknowledgments

- OpenClaw for AI agent orchestration
- Codex CLI for intelligent code generation
- The open-source security community

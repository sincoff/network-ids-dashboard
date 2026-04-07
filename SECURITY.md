# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Network IDS Dashboard seriously. If you have discovered a security vulnerability, we appreciate your help in disclosing it to us responsibly.

### How to Report

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please send an email to **[INSERT SECURITY EMAIL]** with:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Impact assessment** — what could an attacker achieve?
4. **Suggested fix** (if you have one)

### What to Expect

- **Acknowledgment** within 48 hours of your report.
- **Status update** within 5 business days.
- **Resolution timeline** — we aim to patch critical vulnerabilities within 7 days.

### Scope

The following are in scope for security reports:

- Backend API vulnerabilities (injection, authentication bypass, etc.)
- WebSocket security issues
- Cross-site scripting (XSS) in the frontend dashboard
- Sensitive data exposure
- Denial of service vulnerabilities in the detection engine

### Out of Scope

- The DDoS simulation scripts (`scripts/simulate_ddos.sh`) — these are intentionally designed to generate attack traffic in isolated lab environments.
- Issues in third-party dependencies — please report these to the respective maintainers.

## Security Best Practices for Deployment

- **Never** expose the dashboard to the public internet without authentication.
- **Always** run behind a reverse proxy (Nginx) with TLS.
- **Restrict** firewall rules to trusted IP ranges.
- **Rotate** environment variables and credentials regularly.
- See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for secure deployment instructions.

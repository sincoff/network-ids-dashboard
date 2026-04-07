# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-04-07

### Added
- **Real-time packet capture** — Scapy-based sniffer monitoring TCP/IP traffic on configurable network interfaces.
- **Flood detection engine** — Configurable thresholds for SYN flood, UDP flood, ICMP flood, and volumetric attack classification.
- **GeoIP resolution** — MaxMind GeoLite2 integration for geographic origin mapping of source IPs.
- **Interactive attack map** — Leaflet.js world map with color-coded markers per threat classification.
- **Live event feed** — Real-time WebSocket-driven event stream with severity indicators.
- **Dashboard statistics** — Total alerts, unique sources, packets/window, and threat level counters.
- **REST API** — Status, health check, recent events, and statistics endpoints.
- **WebSocket API** — Live event broadcasting to connected dashboard clients.
- **DDoS simulation scripts** — `hping3`-based SYN and UDP flood generators for controlled lab testing.
- **Vercel frontend deployment** — Static dashboard hosted on Vercel free tier.
- **Ubuntu 24.04 LTS production deployment** — Systemd service, Nginx reverse proxy, UFW firewall configuration.
- **Comprehensive documentation** — Architecture guide, API reference, deployment manual, and contributing guidelines.
- **CI/CD pipeline** — GitHub Actions for linting, type-checking, and automated deployment.
- **Open-source standards** — MIT License, Contributing guide, Code of Conduct, Security policy.

### Security
- CORS configuration with configurable origin allowlist.
- Rate limiting on API endpoints.
- Systemd service hardening (NoNewPrivileges, ProtectSystem, PrivateTmp).
- Nginx security headers (X-Frame-Options, X-Content-Type-Options, CSP).

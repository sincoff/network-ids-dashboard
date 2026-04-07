# NetShield IDS — Real-Time Intrusion Detection Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-00a393.svg)](https://fastapi.tiangolo.com)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000.svg)](https://vercel.com)

**NetShield IDS** is an open-source, real-time visual intrusion detection tool built for Linux environments. It monitors incoming network traffic in real-time, detecting volumetric attacks such as DDoS floods, and dynamically plots the geographic origins of the attacks on an interactive, live web-based map.

> **Note**: This project was built for educational and demonstration purposes (Clemson University CPSC 4240 — System Administration and Security).

---

## 🎯 Features

- **Real-Time Packet Capture**: Python-based daemon utilizing `scapy` with raw sockets for low-level TCP/IP traffic inspection.
- **Flood Detection Engine**: Configurable thresholds to identify TCP SYN floods, UDP floods, ICMP floods, and volumetric attacks.
- **GeoIP Resolution**: Fast, local IP-to-location mapping using MaxMind GeoLite2 databases.
- **Premium Cyber Dashboard**: Responsive, glassmorphism UI with live stat counters and animated Leaflet.js attack maps.
- **WebSocket Streaming**: Instant event delivery from backend detector to frontend clients.
- **Production Ready**: Systemd integration, Nginx reverse proxy configurations, rate limiting, and UFW firewall rules included.

---

## 🏗️ Architecture Overview

NetShield IDS follows a decoupled frontend/backend architecture designed for security and scalability.

1. **Python Packet Sniffer**: Runs with escalated privileges (`CAP_NET_RAW`) on the target Ubuntu VM, inspecting packets on a specified network interface.
2. **Detection Engine**: Analyzes traffic windows and flags thresholds.
3. **FastAPI Backend**: Serves the REST API for historical data and a WebSocket endpoint for live streaming.
4. **Vercel / Static Frontend**: The dashboard UI can be hosted remotely on a CDN like Vercel or locally via Nginx. It connects to the VM's backend to render the data.

For detailed diagrams and data flows, see the [Architecture Documentation](docs/ARCHITECTURE.md).

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- Ubuntu 24.04 LTS (or compatible Linux)
- Python 3.12+
- `libpcap-dev`
- Root/sudo access (required for packet sniffing)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/network-ids-dashboard.git
   cd network-ids-dashboard
   ```

2. **Install system dependencies:**
   ```bash
   sudo apt update
   sudo apt install -y python3-venv python3-pip libpcap-dev
   ```

3. **Setup Python environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` and set `SNIFF_INTERFACE` to your active network interface (find it using `ip -br a`)*.

5. **Download GeoIP Database:**
   Download the [GeoLite2-City.mmdb](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data) file from MaxMind and place it in the `data/` directory.

6. **Run the API / Sniffer:**
   ```bash
   sudo -E .venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
   ```

7. **Access Dashboard:** Open your browser and navigate to `http://127.0.0.1:8000`.

---

## 🌐 Production Deployment

NetShield IDS provides full documentation and scripts to deploy the system in a production environment.

### 1. Ubuntu 24.04 LTS Backend Deployment
Use the included setup script to install dependencies, configure a Python virtual environment, set up a Systemd service, and implement an Nginx reverse proxy.
See [Deployment Guide: Ubuntu 24.04 LTS](docs/DEPLOYMENT.md#ubuntu-2404-lts-virtual-machine)

### 2. Vercel Frontend Hosting (Optional)
The dashboard UI can be hosted globally on Vercel's Free Tier, while connecting back to your Ubuntu VM's IP or Domain for the actual packet sniffing data.
See [Deployment Guide: Vercel Hosting](docs/DEPLOYMENT.md#vercel-hosting-frontend)

---

## 🧪 DDoS Simulation

To test the dashboard, you can use the included `simulate_ddos.sh` script from an **Attacker VM** located on the same isolated subnet.

```bash
# On the attacker VM
sudo apt install hping3
chmod +x scripts/simulate_ddos.sh

# Run a SYN flood against the Target VM
./scripts/simulate_ddos.sh <target-ip> syn

# Run a UDP flood
./scripts/simulate_ddos.sh <target-ip> udp
```

> **⚠️ WARNING:** Only run this script in isolated, controlled lab environments. Never execute a DDoS simulation against public IP addresses or networks you do not own.

---

## 📚 Documentation

- [Architecture Design](docs/ARCHITECTURE.md)
- [Deployment Guides](docs/DEPLOYMENT.md)
- [API Reference](docs/API.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

---

## 👨‍💻 Authors

- **Anthony Martino**
- **Ian Sincoff**
- **Tyler Good**

Developed for Clemson University CPSC 4240.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Deployment Guide

NetShield IDS consists of two parts: the backend sniffer and the frontend dashboard, both securely hosted locally on your Ubuntu VM via Nginx.

Because the Python backend uses `scapy` to capture raw network packets, it requires `root` privileges (`CAP_NET_RAW`) to run. It **must** run on a Linux Virtual Machine or physical server.

### Automated Production Setup

We provide a one-command setup script that will create a production-ready environment on Ubuntu 24.04 LTS. It configures Systemd, Nginx, Python Virtual Environments, and applies basic firewall rules.

1. **Clone the repository on the target VM:**
   ```bash
   git clone https://github.com/your-org/network-ids-dashboard.git
   cd network-ids-dashboard
   ```

2. **Download the GeoIP Database (Required for Mapping)**
   Download the `GeoLite2-City.mmdb` from MaxMind and place it in the `data/` folder:
   ```bash
   mkdir -p data
   # Assuming you downloaded the database into this directory
   ```

3. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set SNIFF_INTERFACE to your network interface (e.g. enp0s3)
   ```

4. **Run the Deployment Script:**
   ```bash
   sudo bash deploy/setup.sh
   ```

5. **Run Firewall Configuration (Optional but Recommended):**
   ```bash
   sudo bash deploy/ufw-rules.sh
   ```

### Verification

Check the status of the systemd daemon:
```bash
sudo systemctl status network-ids
```

You can now visit the VM's IP address in your browser: `http://<your-vm-ip>/`



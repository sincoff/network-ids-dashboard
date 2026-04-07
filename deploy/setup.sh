#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# NetShield IDS — One-Command Ubuntu 24.04 LTS Production Setup
# ═══════════════════════════════════════════════════════════════════
#
# Usage: sudo bash deploy/setup.sh
#
# This script:
#   1. Installs system dependencies (Python, libpcap, Nginx)
#   2. Creates a Python virtual environment
#   3. Installs pip packages
#   4. Configures the systemd service
#   5. Configures Nginx reverse proxy
#   6. Enables and starts services
#
# Requirements: Ubuntu 24.04 LTS, root/sudo access
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Colors ───────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[NetShield]${NC} $1"; }
ok()   { echo -e "${GREEN}[  OK  ]${NC} $1"; }
warn() { echo -e "${YELLOW}[ WARN ]${NC} $1"; }
err()  { echo -e "${RED}[ERROR ]${NC} $1"; exit 1; }

# ── Preflight ────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
  err "This script must be run as root. Use: sudo bash deploy/setup.sh"
fi

INSTALL_DIR="/opt/network-ids-dashboard"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log "NetShield IDS — Production Setup"
log "Source:  ${SCRIPT_DIR}"
log "Install: ${INSTALL_DIR}"
echo ""

# ── Step 1: System Dependencies ─────────────────────────────────
log "Installing system dependencies…"
apt update -qq
apt install -y python3 python3-pip python3-venv libpcap-dev nginx curl
ok "System dependencies installed."

# ── Step 2: Copy Application ────────────────────────────────────
log "Deploying application to ${INSTALL_DIR}…"
mkdir -p "${INSTALL_DIR}"
rsync -a --exclude='.venv' --exclude='.git' --exclude='__pycache__' \
  "${SCRIPT_DIR}/" "${INSTALL_DIR}/"
ok "Application deployed."

# ── Step 3: Python Virtual Environment ──────────────────────────
log "Creating Python virtual environment…"
python3 -m venv "${INSTALL_DIR}/.venv"
"${INSTALL_DIR}/.venv/bin/pip" install --quiet --upgrade pip
"${INSTALL_DIR}/.venv/bin/pip" install --quiet -r "${INSTALL_DIR}/backend/requirements.txt"
ok "Python dependencies installed."

# ── Step 4: Environment File ────────────────────────────────────
if [[ ! -f "${INSTALL_DIR}/.env" ]]; then
  cp "${INSTALL_DIR}/.env.example" "${INSTALL_DIR}/.env"
  warn "Created .env from .env.example — edit ${INSTALL_DIR}/.env to set your network interface."
  warn "Find your interface with: ip -br a"
else
  ok ".env already exists — skipping."
fi

# ── Step 5: GeoIP Database ──────────────────────────────────────
if [[ ! -f "${INSTALL_DIR}/data/GeoLite2-City.mmdb" ]]; then
  warn "GeoIP database not found at ${INSTALL_DIR}/data/GeoLite2-City.mmdb"
  warn "Download GeoLite2-City.mmdb from https://dev.maxmind.com/geoip/geolite2-free-geolocation-data"
  warn "Place it in ${INSTALL_DIR}/data/ for geographic resolution."
else
  ok "GeoIP database found."
fi

# ── Step 6: Systemd Service ─────────────────────────────────────
log "Installing systemd service…"
cp "${INSTALL_DIR}/deploy/network-ids.service" /etc/systemd/system/network-ids.service
systemctl daemon-reload
systemctl enable network-ids.service
ok "Systemd service installed and enabled."

# ── Step 7: Nginx ────────────────────────────────────────────────
log "Configuring Nginx reverse proxy…"
cp "${INSTALL_DIR}/deploy/nginx.conf" /etc/nginx/sites-available/network-ids
ln -sf /etc/nginx/sites-available/network-ids /etc/nginx/sites-enabled/network-ids

# Remove default site if it exists
rm -f /etc/nginx/sites-enabled/default

nginx -t 2>/dev/null
systemctl reload nginx
ok "Nginx configured."

# ── Step 8: Start Service ───────────────────────────────────────
log "Starting NetShield IDS…"
systemctl start network-ids.service
sleep 2

if systemctl is-active --quiet network-ids.service; then
  ok "NetShield IDS is running!"
else
  warn "Service may still be starting. Check: sudo journalctl -u network-ids -f"
fi

# ── Done ─────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  NetShield IDS — Setup Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo ""
echo "  Dashboard:  http://$(hostname -I | awk '{print $1}')"
echo "  API Health:  http://$(hostname -I | awk '{print $1}')/api/health"
echo ""
echo "  Manage service:"
echo "    sudo systemctl status network-ids"
echo "    sudo systemctl restart network-ids"
echo "    sudo journalctl -u network-ids -f"
echo ""
echo "  Edit config: sudo nano ${INSTALL_DIR}/.env"
echo ""

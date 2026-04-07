#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# NetShield IDS — UFW Firewall Rules
# ═══════════════════════════════════════════════════════════════════
#
# Usage: sudo bash deploy/ufw-rules.sh
#
# Configures firewall rules for the production dashboard.
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Error: Run with sudo"
  exit 1
fi

echo "[NetShield] Configuring UFW firewall rules…"

# Reset (optional — uncomment if starting fresh)
# ufw --force reset

# Default policies
ufw default deny incoming
ufw default allow outgoing

# SSH (always keep this!)
ufw allow ssh

# HTTP (Nginx serves dashboard)
ufw allow 80/tcp

# HTTPS (if using Let's Encrypt / TLS)
ufw allow 443/tcp

# Enable firewall
ufw --force enable

echo ""
echo "[NetShield] Firewall rules configured:"
ufw status verbose
echo ""
echo "NOTE: The backend port 8000 is NOT exposed directly."
echo "      All traffic goes through the Nginx reverse proxy on port 80/443."
echo ""

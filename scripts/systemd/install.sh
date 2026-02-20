#!/bin/bash
# Install SEJFA systemd services
# Usage: sudo bash scripts/systemd/install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing SEJFA systemd services..."

# Copy service files
for svc in sejfa-voice-pipeline sejfa-loop-runner sejfa-bookit; do
    cp "$SCRIPT_DIR/$svc.service" /etc/systemd/system/
    echo "  Installed $svc.service"
done

# Reload systemd
systemctl daemon-reload

echo ""
echo "Services installed. To enable and start:"
echo ""
echo "  # Voice pipeline + loop runner (the full SEJFA loop)"
echo "  sudo systemctl enable --now sejfa-voice-pipeline"
echo "  sudo systemctl enable --now sejfa-loop-runner"
echo ""
echo "  # BookIt (independent)"
echo "  sudo systemctl enable --now sejfa-bookit"
echo ""
echo "  # Check status"
echo "  systemctl status sejfa-voice-pipeline sejfa-loop-runner"
echo ""
echo "  # View logs"
echo "  journalctl -u sejfa-voice-pipeline -f"
echo "  journalctl -u sejfa-loop-runner -f"
echo ""
echo "IMPORTANT: Create .env first!"
echo "  cp agentic-devops-loop/.env.example .env"
echo "  nano .env  # Fill in Jira credentials"

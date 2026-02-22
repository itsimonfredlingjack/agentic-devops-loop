#!/bin/bash
# Hetzner CX23 initial setup script
# Run from Mac: ssh root@89.167.80.226 < infra/hetzner-setup.sh
# Or copy to server and run: bash hetzner-setup.sh

set -e

echo "=== 1. System update ==="
apt-get update && apt-get upgrade -y

echo "=== 2. Install Docker ==="
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    echo "Docker installed"
else
    echo "Docker already installed: $(docker --version)"
fi

echo "=== 3. Configure UFW firewall ==="
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
echo "y" | ufw enable
ufw status

echo "=== 4. Create application directory ==="
mkdir -p /opt/sejfa
cd /opt/sejfa

echo "=== 5. Add ai-server2 SSH key (for CI/CD) ==="
# Add ai-server2's public key so GitHub Actions (or ai-server2) can deploy
AI_SERVER2_KEY="$(cat /dev/stdin 2>/dev/null || true)"
if [ -n "$AI_SERVER2_KEY" ]; then
    echo "$AI_SERVER2_KEY" >> ~/.ssh/authorized_keys
    echo "Added ai-server2 key"
fi

echo "=== Setup complete ==="
echo ""
echo "Next steps (run manually):"
echo "  1. Clone repo:  cd /opt/sejfa && git clone <REPO_URL> ."
echo "  2. Create .env:  nano /opt/sejfa/.env"
echo "     Required vars:"
echo "       POSTGRES_PASSWORD=<strong-password>"
echo "       CF_API_TOKEN=<cloudflare-dns-token>"
echo "       GITHUB_REPO=<org/repo>"
echo "       IMAGE_TAG=latest"
echo "  3. Login to ghcr.io: echo <TOKEN> | docker login ghcr.io -u <user> --password-stdin"
echo "  4. First deploy: set -a && source .env && set +a && docker compose -f docker-compose.prod.yml up -d"

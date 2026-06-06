#!/bin/bash
# One-time setup on a fresh Ubuntu/Debian VM (Oracle Cloud Always Free, etc.)
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo bash scripts/setup-vm.sh"
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl git ufw

# Docker Engine + Compose plugin
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "${VERSION_CODENAME}") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

systemctl enable docker
systemctl start docker

# Firewall: SSH only — HTTPS is handled by Cloudflare Tunnel (no inbound 80/443 needed)
ufw allow OpenSSH
ufw --force enable

echo ""
echo "Done. Next steps:"
echo "  1. Clone this repo and cd into it"
echo "  2. cp .env.example .env  &&  edit .env"
echo "  3. docker compose up -d --build"
echo "  4. docker compose exec backend python manage.py createsuperuser"
echo "  See DEPLOY.md for Cloudflare Tunnel hostname setup."

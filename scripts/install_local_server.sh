#!/usr/bin/env bash
set -euo pipefail

sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin git ffmpeg python3 python3-pip python3-venv
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER"

echo "Docker installed. Re-login is recommended before running docker compose."
echo "Then run:"
echo "  cd deployments/local-server && docker compose up -d --build"

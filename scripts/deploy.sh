#!/usr/bin/env bash
# ==============================================================================
# MaaHifazat AI — Automated Server Deployment Script (Ubuntu LTS)
# ==============================================================================
set -euo pipefail

APP_DIR="/opt/maahifazat-ai"
SERVICE_NAME="maahifazat"

echo "======================================================================"
echo "🚀 MaaHifazat AI Production Deployment Starting..."
echo "======================================================================"

# 1. System Package Setup
echo "[1/7] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-pip python3-venv nginx certbot python3-certbot-nginx libomp-dev ufw logrotate

# 2. System Service User Setup
echo "[2/7] Ensuring system user 'maahifazat' exists..."
if ! id -u maahifazat >/dev/null 2>&1; then
    sudo useradd --system --shell /bin/false --home-dir /var/lib/maahifazat maahifazat
fi

# 3. Environment & Dependencies Setup
echo "[3/7] Setting up Python virtual environment and dependencies..."
sudo mkdir -p "${APP_DIR}"
sudo chown -R $USER:$USER "${APP_DIR}"

if [ ! -d "${APP_DIR}/.venv" ]; then
    python3 -m venv "${APP_DIR}/.venv"
fi

"${APP_DIR}/.venv/bin/pip" install --upgrade pip -q
"${APP_DIR}/.venv/bin/pip" install -r requirements-backend.txt -r requirements.txt -q

# 4. Systemd Service Installation
echo "[4/7] Installing systemd service..."
sudo cp deployment/systemd/maahifazat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

# 5. Nginx & Logrotate Installation
echo "[5/7] Configuring Nginx reverse proxy and Logrotate..."
sudo cp deployment/nginx/maahifazat.conf /etc/nginx/sites-available/maahifazat
sudo ln -sf /etc/nginx/sites-available/maahifazat /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default || true
sudo cp deployment/logrotate.d/maahifazat /etc/logrotate.d/maahifazat

sudo nginx -t
sudo systemctl restart nginx

# 6. Firewall Verification
echo "[6/7] Configuring UFW firewall rules..."
sudo ufw allow 80/tcp || true
sudo ufw allow 443/tcp || true
sudo ufw allow 22/tcp || true

# 7. Post-Deployment Smoke Test Execution
echo "[7/7] Running post-deployment smoke tests..."
sleep 3
"${APP_DIR}/.venv/bin/python" scripts/smoke_test.py http://127.0.0.1:8000

echo "======================================================================"
echo "🎉 MaaHifazat AI Backend Deployment Complete!"
echo "======================================================================"

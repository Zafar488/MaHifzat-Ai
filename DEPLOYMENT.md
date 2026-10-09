# 🚀 MaaHifazat AI — Server Deployment & Operations Guide

> **Production Deployment Guide for Ubuntu 22.04 LTS / 24.04 LTS VPS & AWS EC2 Instances**  
> *Prepared by Senior DevOps Engineer & Backend Deployment Specialist*

---

## 📋 Table of Contents
1. [Architecture & System Prerequisites](#1-architecture--system-prerequisites)
2. [Phase 1: Server Provisioning & Initial Setup](#phase-1-server-provisioning--initial-setup)
3. [Phase 2: Repository & Dependency Setup](#phase-2-repository--dependency-setup)
4. [Phase 3: Production Environment Configuration](#phase-3-production-environment-configuration)
5. [Phase 4: Systemd Service Management](#phase-4-systemd-service-management)
6. [Phase 5: Nginx Reverse Proxy & TLS/HTTPS Setup](#phase-5-nginx-reverse-proxy--tlshttps-setup)
7. [Phase 6: UFW Firewall & SSH Hardening](#phase-6-ufw-firewall--ssh-hardening)
8. [Phase 7: Log Rotation & Maintenance](#phase-7-log-rotation--maintenance)
9. [Phase 8: Automated Deployment & Smoke Testing](#phase-8-automated-deployment--smoke-testing)
10. [Phase 9: Tested Rollback & Troubleshooting](#phase-9-tested-rollback--troubleshooting)

---

## 1. Architecture & System Prerequisites

### Minimum Server Requirements
* **OS:** Ubuntu 22.04 LTS or Ubuntu 24.04 LTS (x86_64)
* **CPU:** 2 vCPU cores (4 vCPU recommended for high-throughput inference)
* **RAM:** 4 GB minimum (8 GB recommended for loading all 5 ML models into memory)
* **Disk:** 20 GB SSD storage
* **System Library:** `libomp-dev` (OpenMP library required by LightGBM model runtime)

### Ports Configuration
| Port | Protocol | Purpose | Access Level |
| :--- | :--- | :--- | :--- |
| **22** | TCP | SSH Administration | Restricted / Allowed IPs only |
| **80** | TCP | HTTP (ACME Challenge / SSL Redirect) | Public |
| **443** | TCP | HTTPS (Encrypted API & Frontend) | Public |
| **8000** | TCP | FastAPI Backend Internal Gateway | Internal Localhost (`127.0.0.1`) only |

---

## Phase 1: Server Provisioning & Initial Setup

Update system packages and install necessary runtime utilities:

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv nginx certbot python3-certbot-nginx libomp-dev ufw logrotate git
```

Create a dedicated non-privileged system user for running backend processes:

```bash
sudo useradd --system --shell /bin/false --home-dir /var/lib/maahifazat maahifazat
```

---

## Phase 2: Repository & Dependency Setup

Clone the repository into `/opt/maahifazat-ai`:

```bash
sudo mkdir -p /opt/maahifazat-ai
sudo chown -R $USER:$USER /opt/maahifazat-ai
git clone https://github.com/Zafar488/MaHifzat-Ai.git /opt/maahifazat-ai
cd /opt/maahifazat-ai
```

Create a clean Python 3.11/3.12 virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-backend.txt -r requirements.txt
```

---

## Phase 3: Production Environment Configuration

Copy the production environment variable template to `.env`:

```bash
cp .env.production.example .env
nano .env
```

### Essential `.env` Variables to Configure
```env
DEBUG=False
JWT_SECRET=<generate using: openssl rand -hex 32>
GROQ_API_KEY=your_production_groq_api_key
HOST=127.0.0.1
PORT=8000
DATABASE_URL=sqlite+aiosqlite:////var/lib/maahifazat/maahifazat.db
```

Secure permissions on the `.env` file:
```bash
chmod 600 .env
sudo chown maahifazat:maahifazat /opt/maahifazat-ai/.env
```

---

## Phase 4: Systemd Service Management

Install the Systemd unit file:

```bash
sudo cp deployment/systemd/maahifazat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable maahifazat
sudo systemctl start maahifazat
```

### Useful Management Commands
* **Check Status:** `sudo systemctl status maahifazat`
* **Restart Service:** `sudo systemctl restart maahifazat`
* **View Live Logs:** `sudo journalctl -u maahifazat -f -o cat`

---

## Phase 5: Nginx Reverse Proxy & TLS/HTTPS Setup

Install the Nginx configuration:

```bash
sudo cp deployment/nginx/maahifazat.conf /etc/nginx/sites-available/maahifazat
sudo ln -sf /etc/nginx/sites-available/maahifazat /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### Obtain Let's Encrypt TLS/HTTPS Certificate
Run Certbot to obtain free SSL certificates:

```bash
sudo certbot --nginx -d maahifazat.example.com
```

Test automatic certificate renewal:
```bash
sudo certbot renew --dry-run
```

---

## Phase 6: UFW Firewall & SSH Hardening

Configure a restrictive firewall policy using UFW:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw enable
```

### Recommended SSH Hardening (`/etc/ssh/sshd_config`)
```ini
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
X11Forwarding no
```
Reload SSH after changes: `sudo systemctl reload ssh`

---

## Phase 7: Log Rotation & Maintenance

Install the logrotate configuration to maintain server disk space:

```bash
sudo cp deployment/logrotate.d/maahifazat /etc/logrotate.d/maahifazat
sudo chmod 644 /etc/logrotate.d/maahifazat
```

---

## Phase 8: Automated Deployment & Smoke Testing

To execute an automated deployment and run post-deployment smoke tests:

```bash
cd /opt/maahifazat-ai
./scripts/deploy.sh
```

### Run Smoke Test Manually
```bash
python3 scripts/smoke_test.py http://127.0.0.1:8000
```

---

## Phase 9: Tested Rollback & Troubleshooting

### Rollback Procedure
If a deployment fails or exhibits issues:

1. **Revert Git Commit:**
   ```bash
   git reset --hard HEAD~1
   ```
2. **Re-install Stable Dependencies:**
   ```bash
   .venv/bin/pip install -r requirements-backend.txt -r requirements.txt
   ```
3. **Restart Backend Service:**
   ```bash
   sudo systemctl restart maahifazat
   ```
4. **Re-run Smoke Tests:**
   ```bash
   python3 scripts/smoke_test.py http://127.0.0.1:8000
   ```

### Common Troubleshooting Scenarios
* **Model Fails to Load (`libomp.dylib` / `libomp.so` missing):**
  Install OpenMP: `sudo apt-get install -y libomp-dev`
* **Port 8000 Already in Use:**
  Check process using port 8000: `sudo lsof -i :8000` or `sudo netstat -tlpn | grep 8000`
* **Permission Denied on Database File:**
  Ensure `/var/lib/maahifazat` directory is owned by `maahifazat:maahifazat`.

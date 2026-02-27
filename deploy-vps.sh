#!/bin/bash
# Smart AI Trading Strategy Optimizer - VPS Deployment Script
# Run as root on Ubuntu 20.04

set -e

VPS_IP="45.138.132.189"
REPO_URL="https://github.com/avira1987/Smart-AI-Trading-Strategy-Optimizer.git"
DEPLOY_DIR="/root/Smart-AI-Trading-Strategy-Optimizer"

echo "=========================================="
echo "Smart AI Trading - VPS Deployment"
echo "=========================================="

# Update system
echo "[1/7] Updating system..."
apt-get update -qq && apt-get upgrade -y -qq

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[2/7] Installing Docker..."
    apt-get install -y -qq ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io
    systemctl enable docker
    systemctl start docker
else
    echo "[2/7] Docker already installed"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo "[3/7] Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "[3/7] Docker Compose already installed"
fi

# Clone or update repository
echo "[4/7] Setting up project..."
if [ -d "$DEPLOY_DIR" ]; then
    cd "$DEPLOY_DIR"
    git fetch origin
    git reset --hard origin/main
    git pull origin main
else
    git clone "$REPO_URL" "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

# Use nginx config for IP deployment (HTTP only)
echo "[5/7] Configuring nginx for IP access..."
cat > nginx.conf << 'NGINXCONF'
server {
    listen 80 default_server;
    server_name _;
    server_tokens off;
    error_page 403 /403.html;
    error_page 404 /404.html;
    location = /403.html { root /usr/share/nginx/html; internal; }
    location = /404.html { root /usr/share/nginx/html; internal; }
    client_max_body_size 100M;
    root /usr/share/nginx/html;
    index index.html;
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml font/truetype font/opentype application/vnd.ms-fontobject image/svg+xml;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    location = /robots.txt { try_files $uri /robots.txt; access_log off; expires 1d; add_header Cache-Control "public, max-age=86400"; }
    location = /sitemap.xml { try_files $uri /sitemap.xml; access_log off; expires 1d; add_header Content-Type "application/xml; charset=utf-8"; }
    location / { try_files $uri $uri/ /index.html; add_header Cache-Control "no-cache, no-store, must-revalidate"; }
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
        proxy_request_buffering off;
    }
    location /static/ { proxy_pass http://backend:8000/static/; expires 1y; add_header Cache-Control "public, immutable"; }
    location /media/ { proxy_pass http://backend:8000/media/; expires 30d; add_header Cache-Control "public"; }
    location /health { access_log off; return 200 "healthy\n"; add_header Content-Type text/plain; }
}
NGINXCONF

# Update Dockerfile.frontend to copy 403/404 if they exist
# Create .env for production if not exists
if [ ! -f ".env" ]; then
    echo "[6/7] Creating .env file..."
    cat > .env << 'ENVFILE'
SECRET_KEY=change-this-to-a-random-secret-key-in-production
DEBUG=False
ENV=PRODUCTION
DB_NAME=forex_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1,45.138.132.189,*
ENVFILE
fi

# Use docker compose (v2) or docker-compose (v1)
DCOMPOSE="docker compose"
if ! docker compose version &>/dev/null; then
    DCOMPOSE="docker-compose"
fi

echo "[7/7] Building and starting containers..."
$DCOMPOSE down 2>/dev/null || true
$DCOMPOSE build --no-cache
$DCOMPOSE up -d

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "Website: http://${VPS_IP}"
echo "=========================================="
echo ""
echo "Waiting for services to start (60 seconds)..."
sleep 60
$DCOMPOSE ps

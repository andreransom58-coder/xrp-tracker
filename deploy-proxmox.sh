#!/bin/bash
set -e

# XRP Tracker Proxmox Deployment Script
# This script deploys the XRP tracker to a Proxmox LXC container or VM

echo "=== XRP Tracker Proxmox Deployment ==="
echo ""

# Configuration
APP_DIR="/opt/xrp-tracker"
DATA_DIR="/var/lib/xrp-tracker"
SERVICE_NAME="xrp-tracker"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Step 1: Install dependencies
print_info "Installing dependencies..."
apt-get update
apt-get install -y \
    docker.io \
    docker-compose \
    git \
    curl

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Step 2: Create directories
print_info "Creating application directories..."
mkdir -p "$APP_DIR"
mkdir -p "$DATA_DIR"

# Step 3: Copy application files
print_info "Deploying application files..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copy all necessary files
cp -r "$SCRIPT_DIR"/* "$APP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR"/.env.example "$APP_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR"/.gitignore "$APP_DIR/" 2>/dev/null || true

# Step 4: Configure environment
if [ ! -f "$APP_DIR/.env" ]; then
    print_warn ".env file not found. Creating from .env.example..."
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"

    echo ""
    print_warn "IMPORTANT: Please edit $APP_DIR/.env and configure:"
    echo "  - XRPL_ACCOUNT_ADDRESSES (your XRP wallet addresses)"
    echo "  - API_KEY (secure random string for MCP access)"
    echo "  - Alert settings (email, webhook, thresholds)"
    echo ""
    read -p "Press Enter to open the .env file for editing (Ctrl+C to skip)..." -r
    ${EDITOR:-nano} "$APP_DIR/.env"
else
    print_info "Using existing .env file"
fi

# Update docker-compose to use correct data directory
cd "$APP_DIR"
sed -i "s|./data|$DATA_DIR|g" docker-compose.yml

# Step 5: Create systemd service
print_info "Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=XRP Tracker MCP Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/docker-compose up -d --build
ExecStop=/usr/bin/docker-compose down
ExecReload=/usr/bin/docker-compose restart

[Install]
WantedBy=multi-user.target
EOF

# Step 6: Set permissions
print_info "Setting permissions..."
chown -R root:root "$APP_DIR"
chmod 600 "$APP_DIR/.env"
chown -R 1000:1000 "$DATA_DIR"  # Docker container user

# Step 7: Enable and start service
print_info "Enabling and starting service..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}

# Step 8: Wait for service to start
print_info "Waiting for service to start..."
sleep 5

# Check if container is running
if docker ps | grep -q xrp-monitor; then
    print_info "Deployment successful!"
    echo ""
    echo "=== Deployment Summary ==="
    echo "Application directory: $APP_DIR"
    echo "Data directory: $DATA_DIR"
    echo "Service status: $(systemctl is-active ${SERVICE_NAME})"
    echo "MCP endpoint: http://$(hostname -I | awk '{print $1}'):8000"
    echo ""
    echo "Useful commands:"
    echo "  systemctl status ${SERVICE_NAME}  # Check service status"
    echo "  systemctl restart ${SERVICE_NAME} # Restart service"
    echo "  docker logs xrp-monitor-xrp-monitor-1 -f # View logs"
    echo "  nano $APP_DIR/.env                # Edit configuration"
    echo ""
    echo "Next steps:"
    echo "1. Configure your .env file: nano $APP_DIR/.env"
    echo "2. Restart service: systemctl restart ${SERVICE_NAME}"
    echo "3. Configure Claude Desktop with:"
    echo "   - URL: http://YOUR_SERVER_IP:8000"
    echo "   - API Key: (from your .env file)"
else
    print_error "Deployment failed. Check logs with:"
    echo "  docker logs xrp-monitor-xrp-monitor-1"
    echo "  systemctl status ${SERVICE_NAME}"
    exit 1
fi

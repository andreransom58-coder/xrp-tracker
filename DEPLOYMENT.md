# Proxmox Deployment Guide

This guide will help you deploy the XRP Tracker to your Proxmox server.

## Prerequisites

- Proxmox VE server (7.0 or later)
- LXC container or VM running Debian/Ubuntu
- SSH access to the container/VM
- At least 1GB RAM and 10GB disk space

## Option 1: Quick Deployment (Recommended)

### 1. Create LXC Container on Proxmox

In Proxmox web UI:
1. Click "Create CT"
2. Configure:
   - **Hostname**: xrp-tracker
   - **Template**: ubuntu-22.04 or debian-12
   - **Memory**: 1024 MB (1 GB)
   - **Swap**: 512 MB
   - **CPU**: 1 core
   - **Disk**: 10 GB
   - **Network**: Bridge with static IP or DHCP
3. Start the container

### 2. Enable Nesting (Required for Docker)

In Proxmox shell:
```bash
pct set <CTID> -features nesting=1
pct reboot <CTID>
```

Replace `<CTID>` with your container ID.

### 3. Deploy to Container

SSH into your container:
```bash
ssh root@<container-ip>
```

Clone the repository:
```bash
cd /tmp
git clone https://github.com/YOUR_USERNAME/xrp-tracker.git
cd xrp-tracker
```

Run the deployment script:
```bash
chmod +x deploy-proxmox.sh
sudo ./deploy-proxmox.sh
```

The script will:
- ✅ Install Docker and dependencies
- ✅ Create application directories
- ✅ Set up systemd service
- ✅ Configure auto-start on boot
- ✅ Start the XRP tracker

### 4. Configure Your Settings

Edit the configuration file:
```bash
sudo nano /opt/xrp-tracker/.env
```

**Required settings:**
- `XRPL_ACCOUNT_ADDRESSES`: Your XRP wallet address(es) (comma-separated)
- `API_KEY`: Secure random string for MCP authentication

**Optional settings:**
- `XRPL_WS_URL`: XRPL WebSocket URL (default: testnet)
- `ALERT_MIN_XRP`: Minimum XRP amount for alerts
- `SMTP_*`: Email notification settings
- `WEBHOOK_URL`: Webhook for alerts

After editing, restart the service:
```bash
sudo systemctl restart xrp-tracker
```

### 5. Configure Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "xrp-tracker": {
      "url": "http://YOUR_SERVER_IP:8000",
      "headers": {
        "X-API-Key": "YOUR_API_KEY_FROM_ENV"
      }
    }
  }
}
```

Restart Claude Desktop.

## Option 2: Manual VM Deployment

### 1. Create VM

In Proxmox:
1. Create a new VM with Ubuntu 22.04 or Debian 12
2. Allocate at least 1GB RAM, 10GB disk
3. Install and update the OS

### 2. Install Docker

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git
sudo systemctl enable docker
sudo systemctl start docker
```

### 3. Deploy Application

Follow steps 3-5 from Option 1 above.

## Management Commands

### Service Management
```bash
# Check service status
sudo systemctl status xrp-tracker

# Start service
sudo systemctl start xrp-tracker

# Stop service
sudo systemctl stop xrp-tracker

# Restart service
sudo systemctl restart xrp-tracker

# View startup logs
sudo journalctl -u xrp-tracker -f
```

### Docker Container Management
```bash
# View container logs
sudo docker logs xrp-monitor-xrp-monitor-1 -f

# Check container status
sudo docker ps

# Access container shell
sudo docker exec -it xrp-monitor-xrp-monitor-1 bash

# Restart container
cd /opt/xrp-tracker
sudo docker-compose restart

# Rebuild container after changes
cd /opt/xrp-tracker
sudo docker-compose up -d --build
```

### Database Management
```bash
# View database
sudo sqlite3 /var/lib/xrp-tracker/xrp_monitor.db

# Backup database
sudo cp /var/lib/xrp-tracker/xrp_monitor.db /backup/xrp_monitor_$(date +%Y%m%d).db

# Check database size
sudo du -sh /var/lib/xrp-tracker/
```

## Firewall Configuration

If you have a firewall enabled, allow port 8000:

```bash
# UFW
sudo ufw allow 8000/tcp

# iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

## Reverse Proxy (Optional)

For HTTPS access, configure Nginx or Caddy as a reverse proxy:

### Nginx Example
```nginx
server {
    listen 443 ssl;
    server_name xrp.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Service won't start
```bash
# Check service logs
sudo journalctl -u xrp-tracker -n 50

# Check Docker logs
sudo docker logs xrp-monitor-xrp-monitor-1
```

### Connection issues
```bash
# Test local connection
curl http://localhost:8000

# Check if port is listening
sudo netstat -tlnp | grep 8000

# Check firewall
sudo iptables -L -n | grep 8000
```

### High memory usage
```bash
# Check container stats
sudo docker stats

# Adjust memory limit in docker-compose.yml
# Add under xrp-monitor service:
mem_limit: 512m
```

### Database is too large
```bash
# Check database size
sudo du -sh /var/lib/xrp-tracker/

# Archive old transactions (connect to container)
sudo docker exec -it xrp-monitor-xrp-monitor-1 bash
# Then run SQL to delete old records
sqlite3 /app/data/xrp_monitor.db "DELETE FROM transactions WHERE created_at < datetime('now', '-30 days');"
```

## Backup and Restore

### Backup
```bash
#!/bin/bash
BACKUP_DIR="/backup/xrp-tracker"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
sudo cp /var/lib/xrp-tracker/xrp_monitor.db $BACKUP_DIR/xrp_monitor_$DATE.db

# Backup configuration
sudo cp /opt/xrp-tracker/.env $BACKUP_DIR/env_$DATE

echo "Backup completed: $BACKUP_DIR"
```

### Restore
```bash
# Stop service
sudo systemctl stop xrp-tracker

# Restore database
sudo cp /backup/xrp-tracker/xrp_monitor_YYYYMMDD.db /var/lib/xrp-tracker/xrp_monitor.db

# Restore configuration
sudo cp /backup/xrp-tracker/env_YYYYMMDD /opt/xrp-tracker/.env

# Start service
sudo systemctl start xrp-tracker
```

## Updating

To update the application:

```bash
cd /tmp
git clone https://github.com/YOUR_USERNAME/xrp-tracker.git
cd xrp-tracker

# Stop service
sudo systemctl stop xrp-tracker

# Backup current version
sudo cp -r /opt/xrp-tracker /opt/xrp-tracker.backup

# Copy new files (preserve .env)
sudo cp -r ./* /opt/xrp-tracker/

# Rebuild and restart
cd /opt/xrp-tracker
sudo docker-compose up -d --build
sudo systemctl start xrp-tracker
```

## Security Recommendations

1. **Change default API key**: Use a strong, random string
2. **Firewall**: Restrict port 8000 to trusted IPs only
3. **Use HTTPS**: Set up a reverse proxy with SSL/TLS
4. **Regular updates**: Keep the OS and Docker updated
5. **Monitor logs**: Check for suspicious activity
6. **Backup regularly**: Automate database backups

## Performance Tuning

For high-volume wallets:

1. Increase container memory in docker-compose.yml
2. Adjust database vacuum schedule
3. Consider PostgreSQL instead of SQLite
4. Enable database connection pooling

## Support

- GitHub Issues: https://github.com/YOUR_USERNAME/xrp-tracker/issues
- Documentation: See README.md

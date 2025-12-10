#!/bin/bash

# XRP Tracker Control Script
# Provides easy management of the XRP tracker service

APP_DIR="/opt/xrp-tracker"
DATA_DIR="/var/lib/xrp-tracker"
SERVICE_NAME="xrp-tracker"
CONTAINER_NAME="xrp-monitor-xrp-monitor-1"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_header() { echo -e "${BLUE}=== $1 ===${NC}"; }

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run as root (use sudo)"
        exit 1
    fi
}

show_usage() {
    cat << EOF
XRP Tracker Control Script

Usage: $(basename $0) [command]

Commands:
  status          Show service and container status
  start           Start the service
  stop            Stop the service
  restart         Restart the service
  logs            View container logs (follow mode)
  logs-service    View systemd service logs
  config          Edit configuration file
  backup          Create backup of database and config
  restore         Restore from backup
  update          Update application from git
  shell           Access container shell
  db              Access database shell
  stats           Show resource usage statistics
  test            Test API endpoint
  help            Show this help message

Examples:
  $(basename $0) status       # Check service status
  $(basename $0) logs         # View live logs
  $(basename $0) backup       # Create backup

EOF
}

cmd_status() {
    print_header "Service Status"
    systemctl status $SERVICE_NAME --no-pager -l

    echo ""
    print_header "Container Status"
    docker ps -a | grep xrp-monitor || echo "Container not found"

    echo ""
    print_header "Resource Usage"
    docker stats --no-stream $CONTAINER_NAME 2>/dev/null || echo "Container not running"
}

cmd_start() {
    print_info "Starting $SERVICE_NAME..."
    systemctl start $SERVICE_NAME
    sleep 3
    systemctl status $SERVICE_NAME --no-pager
}

cmd_stop() {
    print_info "Stopping $SERVICE_NAME..."
    systemctl stop $SERVICE_NAME
    echo "Service stopped"
}

cmd_restart() {
    print_info "Restarting $SERVICE_NAME..."
    systemctl restart $SERVICE_NAME
    sleep 3
    systemctl status $SERVICE_NAME --no-pager
}

cmd_logs() {
    print_info "Showing container logs (Ctrl+C to exit)..."
    docker logs $CONTAINER_NAME -f --tail 100
}

cmd_logs_service() {
    print_info "Showing service logs (Ctrl+C to exit)..."
    journalctl -u $SERVICE_NAME -f
}

cmd_config() {
    check_root
    print_info "Opening configuration file..."
    ${EDITOR:-nano} $APP_DIR/.env
    echo ""
    read -p "Restart service to apply changes? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cmd_restart
    fi
}

cmd_backup() {
    check_root
    BACKUP_DIR="${1:-/backup/xrp-tracker}"
    DATE=$(date +%Y%m%d_%H%M%S)

    print_info "Creating backup..."
    mkdir -p $BACKUP_DIR

    # Backup database
    if [ -f "$DATA_DIR/xrp_monitor.db" ]; then
        cp $DATA_DIR/xrp_monitor.db $BACKUP_DIR/xrp_monitor_$DATE.db
        print_info "Database backed up: $BACKUP_DIR/xrp_monitor_$DATE.db"
    fi

    # Backup config
    if [ -f "$APP_DIR/.env" ]; then
        cp $APP_DIR/.env $BACKUP_DIR/env_$DATE
        print_info "Config backed up: $BACKUP_DIR/env_$DATE"
    fi

    # Create compressed archive
    tar -czf $BACKUP_DIR/xrp-tracker-backup-$DATE.tar.gz \
        -C $DATA_DIR . \
        -C $APP_DIR .env 2>/dev/null

    print_info "Backup completed: $BACKUP_DIR/xrp-tracker-backup-$DATE.tar.gz"
}

cmd_restore() {
    check_root
    BACKUP_FILE="$1"

    if [ -z "$BACKUP_FILE" ]; then
        print_error "Usage: $(basename $0) restore <backup-file>"
        exit 1
    fi

    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi

    print_warn "This will overwrite current data!"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi

    print_info "Stopping service..."
    systemctl stop $SERVICE_NAME

    print_info "Restoring from $BACKUP_FILE..."
    tar -xzf $BACKUP_FILE -C /tmp/xrp-restore
    cp /tmp/xrp-restore/xrp_monitor.db $DATA_DIR/
    cp /tmp/xrp-restore/.env $APP_DIR/
    rm -rf /tmp/xrp-restore

    print_info "Starting service..."
    systemctl start $SERVICE_NAME

    print_info "Restore completed"
}

cmd_update() {
    check_root
    print_warn "This will update the application from git"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi

    print_info "Stopping service..."
    systemctl stop $SERVICE_NAME

    print_info "Backing up current version..."
    cp -r $APP_DIR ${APP_DIR}.backup.$(date +%Y%m%d_%H%M%S)

    print_info "Pulling latest changes..."
    cd $APP_DIR
    git pull

    print_info "Rebuilding container..."
    docker-compose build

    print_info "Starting service..."
    systemctl start $SERVICE_NAME

    print_info "Update completed"
}

cmd_shell() {
    print_info "Accessing container shell..."
    docker exec -it $CONTAINER_NAME bash
}

cmd_db() {
    print_info "Accessing database shell (type .exit to quit)..."
    docker exec -it $CONTAINER_NAME sqlite3 /app/data/xrp_monitor.db
}

cmd_stats() {
    print_header "Resource Statistics"

    echo "Container:"
    docker stats --no-stream $CONTAINER_NAME 2>/dev/null || echo "Container not running"

    echo ""
    echo "Database size:"
    du -sh $DATA_DIR 2>/dev/null || echo "Data directory not found"

    echo ""
    echo "Disk usage:"
    df -h $APP_DIR | tail -1

    echo ""
    echo "Transaction count:"
    docker exec $CONTAINER_NAME sqlite3 /app/data/xrp_monitor.db \
        "SELECT COUNT(*) FROM transactions;" 2>/dev/null || echo "Cannot query database"
}

cmd_test() {
    print_header "Testing API Endpoint"

    # Get API key from .env
    if [ -f "$APP_DIR/.env" ]; then
        API_KEY=$(grep "^API_KEY=" $APP_DIR/.env | cut -d'=' -f2)
    fi

    print_info "Testing connection to http://localhost:8000..."

    if [ -n "$API_KEY" ]; then
        curl -s -H "X-API-Key: $API_KEY" http://localhost:8000 | head -20
    else
        curl -s http://localhost:8000 | head -20
    fi

    echo ""
    echo ""
    print_info "If you see a response above, the service is working!"
}

# Main command dispatcher
case "${1:-help}" in
    status)
        cmd_status
        ;;
    start)
        check_root
        cmd_start
        ;;
    stop)
        check_root
        cmd_stop
        ;;
    restart)
        check_root
        cmd_restart
        ;;
    logs)
        cmd_logs
        ;;
    logs-service)
        cmd_logs_service
        ;;
    config)
        cmd_config
        ;;
    backup)
        cmd_backup "$2"
        ;;
    restore)
        cmd_restore "$2"
        ;;
    update)
        cmd_update
        ;;
    shell)
        cmd_shell
        ;;
    db)
        cmd_db
        ;;
    stats)
        cmd_stats
        ;;
    test)
        cmd_test
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac

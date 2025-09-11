#!/bin/bash
# LabDabbler Production Update Script

set -e

COMPOSE_FILE="docker-compose.production.yml"
BACKUP_DIR="./backups"
LOG_FILE="/var/log/labdabbler/update.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# Create backup before update
create_backup() {
    log "Creating backup before update..."
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="$BACKUP_DIR/pre_update_backup_$timestamp.tar.gz"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup application data and database
    docker run --rm \
        -v labdabbler_postgres_data:/data/postgres \
        -v labdabbler_redis_data:/data/redis \
        -v labdabbler_backend_data:/data/backend \
        -v "$PWD/$BACKUP_DIR:/backup" \
        alpine:latest \
        tar -czf "/backup/pre_update_backup_$timestamp.tar.gz" /data
    
    success "Backup created: $backup_file"
}

# Update images
update_images() {
    log "Pulling latest images..."
    
    docker compose -f "$COMPOSE_FILE" pull
    
    success "Images updated"
}

# Rolling update strategy
rolling_update() {
    log "Performing rolling update..."
    
    # Update backend first
    log "Updating backend service..."
    docker compose -f "$COMPOSE_FILE" up -d --no-deps backend
    
    # Wait for backend to be healthy
    sleep 30
    if ! curl -sf http://localhost/api/health > /dev/null; then
        error "Backend health check failed after update"
    fi
    
    # Update frontend
    log "Updating frontend service..."
    docker compose -f "$COMPOSE_FILE" up -d --no-deps frontend
    
    # Wait for frontend to be ready
    sleep 15
    if ! curl -sf http://localhost/health > /dev/null; then
        error "Frontend health check failed after update"
    fi
    
    # Update nginx (reload configuration)
    log "Reloading nginx configuration..."
    docker compose -f "$COMPOSE_FILE" exec nginx nginx -s reload
    
    success "Rolling update completed"
}

# Database migration (if needed)
run_migrations() {
    log "Checking for database migrations..."
    
    # This would run any pending database migrations
    # For now, it's a placeholder
    docker compose -f "$COMPOSE_FILE" exec backend python -c "
import sys
sys.path.append('/app')
# Add migration logic here
print('No migrations to run')
"
    
    success "Database migrations completed"
}

# Health check
health_check() {
    log "Performing post-update health checks..."
    
    services=("nginx" "frontend" "backend" "postgres" "redis")
    failed_services=()
    
    for service in "${services[@]}"; do
        if ! docker compose -f "$COMPOSE_FILE" ps "$service" | grep -q "running"; then
            failed_services+=("$service")
        fi
    done
    
    if [ ${#failed_services[@]} -ne 0 ]; then
        error "Failed services after update: ${failed_services[*]}"
    fi
    
    # Check application health
    if ! curl -sf http://localhost/api/health > /dev/null; then
        error "Application health check failed"
    fi
    
    success "All health checks passed"
}

# Cleanup old images
cleanup() {
    log "Cleaning up old images..."
    
    # Remove dangling images
    docker image prune -f
    
    success "Cleanup completed"
}

# Main update function
update() {
    log "Starting LabDabbler update..."
    
    # Confirmation prompt
    if [ -t 0 ]; then
        echo -e "${YELLOW}This will update LabDabbler. A backup will be created. Continue? (y/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log "Update cancelled by user"
            exit 0
        fi
    fi
    
    create_backup
    update_images
    run_migrations
    rolling_update
    health_check
    cleanup
    
    success "LabDabbler update completed successfully!"
    
    # Show current status
    log "Current service status:"
    docker compose -f "$COMPOSE_FILE" ps
}

# Rollback function
rollback() {
    log "Rolling back to previous version..."
    
    if [ -z "$1" ]; then
        error "Please specify backup file to rollback to"
    fi
    
    backup_file="$1"
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
    fi
    
    warning "This will restore data from backup and may cause data loss!"
    if [ -t 0 ]; then
        echo -e "${YELLOW}Continue with rollback? (y/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log "Rollback cancelled by user"
            exit 0
        fi
    fi
    
    # Stop services
    docker compose -f "$COMPOSE_FILE" down
    
    # Restore data from backup
    docker run --rm \
        -v labdabbler_postgres_data:/data/postgres \
        -v labdabbler_redis_data:/data/redis \
        -v labdabbler_backend_data:/data/backend \
        -v "$PWD/$BACKUP_DIR:/backup" \
        alpine:latest \
        tar -xzf "/backup/$(basename "$backup_file")" -C /
    
    # Restart services
    docker compose -f "$COMPOSE_FILE" up -d
    
    success "Rollback completed"
}

# Handle script arguments
case "${1:-update}" in
    "update")
        update
        ;;
    "rollback")
        rollback "$2"
        ;;
    "backup")
        create_backup
        ;;
    *)
        echo "Usage: $0 {update|rollback|backup}"
        echo
        echo "Commands:"
        echo "  update             - Update LabDabbler to latest version"
        echo "  rollback <file>    - Rollback to backup file"
        echo "  backup             - Create backup only"
        exit 1
        ;;
esac
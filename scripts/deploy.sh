#!/bin/bash
# LabDabbler Production Deployment Script

set -e

# Configuration
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"
LOG_FILE="/var/log/labdabbler/deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Pre-deployment checks
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
    fi
    
    # Check if Docker Compose is available
    if ! docker compose version &> /dev/null; then
        error "Docker Compose is not available"
    fi
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        error "Environment file $ENV_FILE not found. Copy from $ENV_FILE.template and configure."
    fi
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Docker Compose file $COMPOSE_FILE not found"
    fi
    
    success "Prerequisites check passed"
}

# Check environment variables and security configuration
check_environment() {
    log "Checking environment configuration..."
    
    required_vars=(
        "DATABASE_PASSWORD"
        "REDIS_PASSWORD"
        "SECRET_KEY"
        "JWT_SECRET"
        "GRAFANA_PASSWORD"
    )
    
    missing_vars=()
    
    # Source environment file
    set -a
    source "$ENV_FILE"
    set +a
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        error "Missing required environment variables: ${missing_vars[*]}"
    fi
    
    success "Environment configuration check passed"
}

# Security validation for production deployment
check_security_configuration() {
    log "Performing security configuration checks..."
    
    # Source environment file
    set -a
    source "$ENV_FILE"
    set +a
    
    security_issues=()
    
    # Check for default/weak passwords
    if [[ "$DATABASE_PASSWORD" == *"CHANGE_ME"* ]] || [ ${#DATABASE_PASSWORD} -lt 32 ]; then
        security_issues+=("DATABASE_PASSWORD: Must be changed from default and be at least 32 characters")
    fi
    
    if [[ "$REDIS_PASSWORD" == *"CHANGE_ME"* ]] || [ ${#REDIS_PASSWORD} -lt 24 ]; then
        security_issues+=("REDIS_PASSWORD: Must be changed from default and be at least 24 characters")
    fi
    
    if [[ "$SECRET_KEY" == *"CHANGE_ME"* ]] || [ ${#SECRET_KEY} -lt 32 ]; then
        security_issues+=("SECRET_KEY: Must be changed from default and be at least 32 characters")
    fi
    
    if [[ "$JWT_SECRET" == *"CHANGE_ME"* ]] || [ ${#JWT_SECRET} -lt 32 ]; then
        security_issues+=("JWT_SECRET: Must be changed from default and be at least 32 characters")
    fi
    
    if [[ "$GRAFANA_PASSWORD" == *"CHANGE_ME"* ]] || [ ${#GRAFANA_PASSWORD} -lt 12 ]; then
        security_issues+=("GRAFANA_PASSWORD: Must be changed from default and be at least 12 characters")
    fi
    
    # Check ALLOWED_HOSTS configuration
    if [[ "$ALLOWED_HOSTS" == *"your-domain.com"* ]]; then
        security_issues+=("ALLOWED_HOSTS: Must be updated with your actual domain names")
    fi
    
    # Check CORS_ORIGINS configuration
    if [[ "$CORS_ORIGINS" == *"your-domain.com"* ]]; then
        security_issues+=("CORS_ORIGINS: Must be updated with your actual frontend URLs")
    fi
    
    # Check for weak patterns in passwords
    if [[ "$DATABASE_PASSWORD" =~ ^[a-zA-Z0-9]*$ ]]; then
        warning "DATABASE_PASSWORD: Consider using special characters for stronger security"
    fi
    
    if [[ "$REDIS_PASSWORD" =~ ^[a-zA-Z0-9]*$ ]]; then
        warning "REDIS_PASSWORD: Consider using special characters for stronger security"
    fi
    
    # Report security issues
    if [ ${#security_issues[@]} -ne 0 ]; then
        error "CRITICAL SECURITY ISSUES DETECTED:\n$(printf '%s\n' "${security_issues[@]}")\n\nPlease fix these issues in $ENV_FILE before deploying to production."
    fi
    
    success "Security configuration validation passed"
}

# Backup current deployment
backup_current() {
    log "Creating backup of current deployment..."
    
    mkdir -p "$BACKUP_DIR"
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="$BACKUP_DIR/labdabbler_backup_$timestamp.tar.gz"
    
    # Backup data volumes (using project prefix)
    PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]')
    docker run --rm \
        -v "${PROJECT_NAME}_postgres_data:/data/postgres" \
        -v "${PROJECT_NAME}_redis_data:/data/redis" \
        -v "${PROJECT_NAME}_backend_data:/data/backend" \
        -v "${PROJECT_NAME}_backend_labs:/data/labs" \
        -v "${PROJECT_NAME}_backend_configs:/data/configs" \
        -v "${PROJECT_NAME}_backend_uploads:/data/uploads" \
        -v "$PWD/$BACKUP_DIR:/backup" \
        alpine:latest \
        tar -czf "/backup/labdabbler_backup_$timestamp.tar.gz" /data
    
    success "Backup created: $backup_file"
}

# Pull latest images
pull_images() {
    log "Pulling latest Docker images..."
    
    docker compose -f "$COMPOSE_FILE" pull
    
    success "Images pulled successfully"
}

# Generate SSL certificates if needed
setup_ssl() {
    log "Setting up SSL certificates..."
    
    if [ ! -f "ssl/labdabbler.crt" ] || [ ! -f "ssl/labdabbler.key" ]; then
        warning "SSL certificates not found. Generating self-signed certificates..."
        chmod +x ssl/generate-certs.sh
        ./ssl/generate-certs.sh
    else
        log "SSL certificates already exist"
    fi
    
    success "SSL setup completed"
}

# Start services
start_services() {
    log "Starting LabDabbler services..."
    
    # Start database and cache first
    docker compose -f "$COMPOSE_FILE" up -d postgres redis
    
    # Wait for database to be ready
    log "Waiting for PostgreSQL to be ready..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U labdabbler_user; then
            break
        fi
        sleep 2
        ((timeout -= 2))
    done
    
    if [ $timeout -le 0 ]; then
        error "PostgreSQL failed to start within timeout"
    fi
    
    # Start application services
    docker compose -f "$COMPOSE_FILE" up -d backend frontend
    
    # Start monitoring and logging
    docker compose -f "$COMPOSE_FILE" up -d prometheus grafana fluentd
    
    # Start nginx last
    docker compose -f "$COMPOSE_FILE" up -d nginx
    
    success "All services started successfully"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check if all containers are running
    failed_services=()
    services=("nginx" "frontend" "backend" "postgres" "redis" "prometheus" "grafana")
    
    for service in "${services[@]}"; do
        if ! docker compose -f "$COMPOSE_FILE" ps "$service" | grep -q "running"; then
            failed_services+=("$service")
        fi
    done
    
    if [ ${#failed_services[@]} -ne 0 ]; then
        error "Failed services: ${failed_services[*]}"
    fi
    
    # Check health endpoints
    log "Checking health endpoints..."
    
    # Wait for services to be fully ready
    sleep 30
    
    # Check backend health
    if ! curl -sf http://localhost/api/health > /dev/null; then
        warning "Backend health check failed"
    else
        success "Backend health check passed"
    fi
    
    # Check frontend
    if ! curl -sf http://localhost/health > /dev/null; then
        warning "Frontend health check failed"
    else
        success "Frontend health check passed"
    fi
    
    success "Deployment verification completed"
}

# Show deployment status
show_status() {
    log "Deployment Status:"
    echo
    docker compose -f "$COMPOSE_FILE" ps
    echo
    log "Service URLs:"
    log "  Frontend: http://localhost/ (or https://your-domain.com/)"
    log "  Backend API: http://localhost/api/ (or https://api.your-domain.com/)"
    log "  Grafana: http://localhost:3000/"
    log "  Prometheus: http://localhost:9090/"
    echo
    log "Log locations:"
    log "  Application: /var/log/labdabbler/"
    log "  Deployment: $LOG_FILE"
}

# Cleanup old images and containers
cleanup() {
    log "Cleaning up old Docker images and containers..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful with this)
    # docker volume prune -f
    
    success "Cleanup completed"
}

# Main deployment function
deploy() {
    log "Starting LabDabbler production deployment..."
    
    check_prerequisites
    check_environment
    check_security_configuration
    
    # Ask for confirmation in interactive mode
    if [ -t 0 ]; then
        echo -e "${YELLOW}This will deploy LabDabbler to production. Continue? (y/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log "Deployment cancelled by user"
            exit 0
        fi
    fi
    
    backup_current
    pull_images
    setup_ssl
    start_services
    verify_deployment
    cleanup
    show_status
    
    success "LabDabbler production deployment completed successfully!"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "status")
        docker compose -f "$COMPOSE_FILE" ps
        ;;
    "logs")
        docker compose -f "$COMPOSE_FILE" logs -f "${2:-}"
        ;;
    "stop")
        log "Stopping LabDabbler services..."
        docker compose -f "$COMPOSE_FILE" down
        success "Services stopped"
        ;;
    "restart")
        log "Restarting LabDabbler services..."
        docker compose -f "$COMPOSE_FILE" restart "${2:-}"
        success "Services restarted"
        ;;
    "backup")
        backup_current
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 {deploy|status|logs|stop|restart|backup|cleanup}"
        echo
        echo "Commands:"
        echo "  deploy   - Deploy LabDabbler to production"
        echo "  status   - Show service status"
        echo "  logs     - Show service logs (optionally specify service name)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart services (optionally specify service name)"
        echo "  backup   - Create backup of current deployment"
        echo "  cleanup  - Clean up old Docker images"
        exit 1
        ;;
esac
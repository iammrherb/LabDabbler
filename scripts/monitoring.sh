#!/bin/bash
# LabDabbler Production Monitoring Script

set -e

COMPOSE_FILE="docker-compose.production.yml"
LOG_FILE="/var/log/labdabbler/monitoring.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check service health
check_service_health() {
    log "Checking service health..."
    
    services=("nginx" "frontend" "backend" "postgres" "redis" "prometheus" "grafana")
    
    for service in "${services[@]}"; do
        if docker compose -f "$COMPOSE_FILE" ps "$service" | grep -q "running"; then
            echo -e "${GREEN}✓${NC} $service: Running"
        else
            echo -e "${RED}✗${NC} $service: Not running"
        fi
    done
}

# Check resource usage
check_resource_usage() {
    log "Checking resource usage..."
    
    echo -e "${BLUE}Container Resource Usage:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    echo
    echo -e "${BLUE}Host System Resources:${NC}"
    echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
    echo "Memory Usage: $(free | grep Mem | awk '{printf("%.2f%%\n", $3/$2 * 100.0)}')"
    echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s\n", $5}')"
}

# Check logs for errors
check_error_logs() {
    log "Checking for errors in logs..."
    
    # Check backend logs for errors
    backend_errors=$(docker compose -f "$COMPOSE_FILE" logs backend --since 1h 2>/dev/null | grep -i error | wc -l)
    if [ "$backend_errors" -gt 0 ]; then
        echo -e "${RED}Backend errors in last hour: $backend_errors${NC}"
    else
        echo -e "${GREEN}✓ No backend errors in last hour${NC}"
    fi
    
    # Check nginx logs for errors
    nginx_errors=$(docker compose -f "$COMPOSE_FILE" logs nginx --since 1h 2>/dev/null | grep -i error | wc -l)
    if [ "$nginx_errors" -gt 0 ]; then
        echo -e "${RED}Nginx errors in last hour: $nginx_errors${NC}"
    else
        echo -e "${GREEN}✓ No nginx errors in last hour${NC}"
    fi
}

# Check database health
check_database_health() {
    log "Checking database health..."
    
    # PostgreSQL health
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U labdabbler_user > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is responding${NC}"
        
        # Check database size
        db_size=$(docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U labdabbler_user -d labdabbler_production -t -c "SELECT pg_size_pretty(pg_database_size('labdabbler_production'));" 2>/dev/null | xargs)
        echo "Database size: $db_size"
        
        # Check connection count
        connections=$(docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U labdabbler_user -d labdabbler_production -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | xargs)
        echo "Active connections: $connections"
    else
        echo -e "${RED}✗ PostgreSQL is not responding${NC}"
    fi
    
    # Redis health
    if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis is responding${NC}"
        
        # Check Redis info
        memory_usage=$(docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        echo "Redis memory usage: $memory_usage"
    else
        echo -e "${RED}✗ Redis is not responding${NC}"
    fi
}

# Check network connectivity
check_network() {
    log "Checking network connectivity..."
    
    # Check if services can reach each other
    if docker compose -f "$COMPOSE_FILE" exec -T backend curl -sf http://postgres:5432 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend can reach database${NC}"
    else
        echo -e "${RED}✗ Backend cannot reach database${NC}"
    fi
    
    if docker compose -f "$COMPOSE_FILE" exec -T backend curl -sf http://redis:6379 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend can reach Redis${NC}"
    else
        echo -e "${RED}✗ Backend cannot reach Redis${NC}"
    fi
}

# Check SSL certificates
check_ssl() {
    log "Checking SSL certificates..."
    
    if [ -f "ssl/labdabbler.crt" ]; then
        expiry_date=$(openssl x509 -in ssl/labdabbler.crt -noout -enddate | cut -d= -f2)
        expiry_timestamp=$(date -d "$expiry_date" +%s)
        current_timestamp=$(date +%s)
        days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [ $days_until_expiry -lt 30 ]; then
            echo -e "${YELLOW}⚠ SSL certificate expires in $days_until_expiry days${NC}"
        else
            echo -e "${GREEN}✓ SSL certificate valid for $days_until_expiry days${NC}"
        fi
    else
        echo -e "${RED}✗ SSL certificate not found${NC}"
    fi
}

# Check disk space
check_disk_space() {
    log "Checking disk space..."
    
    # Check main filesystem
    disk_usage=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 85 ]; then
        echo -e "${RED}⚠ Disk usage is ${disk_usage}% - cleanup may be needed${NC}"
    else
        echo -e "${GREEN}✓ Disk usage is ${disk_usage}%${NC}"
    fi
    
    # Check Docker volumes
    echo "Docker volume sizes:"
    docker system df -v | grep "VOLUME NAME\|labdabbler"
}

# Performance metrics
show_performance_metrics() {
    log "Collecting performance metrics..."
    
    echo -e "${BLUE}Response Time Test:${NC}"
    
    # Test backend API response time
    backend_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost/api/health)
    echo "Backend API response time: ${backend_time}s"
    
    # Test frontend response time
    frontend_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost/health)
    echo "Frontend response time: ${frontend_time}s"
    
    # Show request counts from metrics (if available)
    echo -e "\n${BLUE}Request Metrics (last hour):${NC}"
    docker compose -f "$COMPOSE_FILE" logs nginx --since 1h 2>/dev/null | grep -E "GET|POST|PUT|DELETE" | wc -l | xargs echo "Total requests:"
}

# Generate monitoring report
generate_report() {
    report_file="/tmp/labdabbler_monitoring_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "LabDabbler Monitoring Report"
        echo "Generated: $(date)"
        echo "=========================="
        echo
        
        echo "SERVICE HEALTH:"
        check_service_health
        echo
        
        echo "RESOURCE USAGE:"
        check_resource_usage
        echo
        
        echo "DATABASE HEALTH:"
        check_database_health
        echo
        
        echo "ERROR SUMMARY:"
        check_error_logs
        echo
        
        echo "NETWORK CONNECTIVITY:"
        check_network
        echo
        
        echo "SSL STATUS:"
        check_ssl
        echo
        
        echo "DISK SPACE:"
        check_disk_space
        echo
        
        echo "PERFORMANCE METRICS:"
        show_performance_metrics
        
    } > "$report_file"
    
    echo "Monitoring report saved to: $report_file"
}

# Main monitoring function
monitor() {
    echo -e "${BLUE}LabDabbler Production Monitoring${NC}"
    echo "================================="
    echo
    
    check_service_health
    echo
    check_resource_usage
    echo
    check_database_health
    echo
    check_error_logs
    echo
    check_network
    echo
    check_ssl
    echo
    check_disk_space
    echo
    show_performance_metrics
}

# Watch mode - continuous monitoring
watch_mode() {
    while true; do
        clear
        monitor
        echo
        echo "Press Ctrl+C to stop monitoring"
        sleep 30
    done
}

# Handle script arguments
case "${1:-monitor}" in
    "monitor")
        monitor
        ;;
    "watch")
        watch_mode
        ;;
    "report")
        generate_report
        ;;
    "health")
        check_service_health
        ;;
    "resources")
        check_resource_usage
        ;;
    "logs")
        check_error_logs
        ;;
    "database")
        check_database_health
        ;;
    "network")
        check_network
        ;;
    "ssl")
        check_ssl
        ;;
    "disk")
        check_disk_space
        ;;
    "performance")
        show_performance_metrics
        ;;
    *)
        echo "Usage: $0 {monitor|watch|report|health|resources|logs|database|network|ssl|disk|performance}"
        echo
        echo "Commands:"
        echo "  monitor      - Run all monitoring checks once"
        echo "  watch        - Continuous monitoring (refreshes every 30s)"
        echo "  report       - Generate detailed monitoring report"
        echo "  health       - Check service health only"
        echo "  resources    - Check resource usage only"
        echo "  logs         - Check error logs only"
        echo "  database     - Check database health only"
        echo "  network      - Check network connectivity only"
        echo "  ssl          - Check SSL certificates only"
        echo "  disk         - Check disk space only"
        echo "  performance  - Check performance metrics only"
        exit 1
        ;;
esac
#!/bin/bash
# LabDabbler Production Deployment Test Script

set -e

COMPOSE_FILE="docker-compose.production.yml"
TEST_LOG="/var/log/labdabbler/production-test.log"
TIMEOUT=60

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$TEST_LOG"
}

success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$TEST_LOG"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1" | tee -a "$TEST_LOG"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$1")
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$TEST_LOG"
}

info() {
    echo -e "${BLUE}ℹ${NC} $1" | tee -a "$TEST_LOG"
}

# Wait for service to be ready
wait_for_service() {
    local service_name=$1
    local check_command=$2
    local timeout=${3:-60}
    local count=0
    
    info "Waiting for $service_name to be ready..."
    
    while [ $count -lt $timeout ]; do
        if eval "$check_command" &>/dev/null; then
            return 0
        fi
        sleep 2
        ((count += 2))
    done
    
    return 1
}

# Test 1: Environment Configuration
test_environment() {
    log "Testing environment configuration..."
    
    if [ ! -f ".env.production" ]; then
        fail "Environment file .env.production not found"
        return 1
    fi
    
    # Source environment file
    set -a
    source .env.production
    set +a
    
    # Check required variables
    required_vars=("DATABASE_PASSWORD" "REDIS_PASSWORD" "SECRET_KEY" "JWT_SECRET")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            fail "Required environment variable $var is not set"
        else
            success "Environment variable $var is configured"
        fi
    done
}

# Test 2: Docker Images Build
test_docker_images() {
    log "Testing Docker image build..."
    
    info "Building frontend image..."
    if docker build -t labdabbler-frontend-test ./web/frontend; then
        success "Frontend image builds successfully"
    else
        fail "Frontend image build failed"
    fi
    
    info "Building backend image..."
    if docker build -t labdabbler-backend-test ./web/backend; then
        success "Backend image builds successfully"
    else
        fail "Backend image build failed"
    fi
}

# Test 3: SSL Configuration
test_ssl_configuration() {
    log "Testing SSL configuration..."
    
    if [ -f "ssl/labdabbler.crt" ] && [ -f "ssl/labdabbler.key" ]; then
        success "SSL certificates exist"
        
        # Check certificate validity
        if openssl x509 -in ssl/labdabbler.crt -noout -checkend 86400; then
            success "SSL certificate is valid"
        else
            warning "SSL certificate expires within 24 hours"
        fi
        
        # Check private key
        if openssl rsa -in ssl/labdabbler.key -check -noout; then
            success "SSL private key is valid"
        else
            fail "SSL private key is invalid"
        fi
    else
        warning "SSL certificates not found - generating self-signed certificates"
        if ./ssl/generate-certs.sh; then
            success "SSL certificates generated successfully"
        else
            fail "SSL certificate generation failed"
        fi
    fi
}

# Test 4: Service Startup
test_service_startup() {
    log "Testing service startup..."
    
    # Start services in order
    info "Starting PostgreSQL and Redis..."
    docker compose -f "$COMPOSE_FILE" up -d postgres redis
    
    if wait_for_service "PostgreSQL" "docker compose -f $COMPOSE_FILE exec -T postgres pg_isready -U labdabbler_user" 60; then
        success "PostgreSQL started successfully"
    else
        fail "PostgreSQL failed to start"
        return 1
    fi
    
    if wait_for_service "Redis" "docker compose -f $COMPOSE_FILE exec -T redis redis-cli ping" 30; then
        success "Redis started successfully"
    else
        fail "Redis failed to start"
        return 1
    fi
    
    info "Starting backend service..."
    docker compose -f "$COMPOSE_FILE" up -d backend
    
    if wait_for_service "Backend" "curl -sf http://localhost:8000/api/health" 60; then
        success "Backend started successfully"
    else
        fail "Backend failed to start"
        return 1
    fi
    
    info "Starting frontend service..."
    docker compose -f "$COMPOSE_FILE" up -d frontend
    
    if wait_for_service "Frontend" "docker compose -f $COMPOSE_FILE ps frontend | grep -q 'running'" 30; then
        success "Frontend started successfully"
    else
        fail "Frontend failed to start"
        return 1
    fi
    
    info "Starting nginx proxy..."
    docker compose -f "$COMPOSE_FILE" up -d nginx
    
    if wait_for_service "Nginx" "curl -sf http://localhost/health" 30; then
        success "Nginx proxy started successfully"
    else
        fail "Nginx proxy failed to start"
        return 1
    fi
}

# Test 5: Database Connectivity and Schema
test_database() {
    log "Testing database connectivity and schema..."
    
    # Test connection
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U labdabbler_user; then
        success "Database connection established"
    else
        fail "Database connection failed"
        return 1
    fi
    
    # Check if tables exist
    tables_query="SELECT count(*) FROM information_schema.tables WHERE table_schema = 'labdabbler';"
    table_count=$(docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U labdabbler_user -d labdabbler_production -t -c "$tables_query" | xargs)
    
    if [ "$table_count" -gt 0 ]; then
        success "Database schema initialized ($table_count tables found)"
    else
        fail "Database schema not initialized"
    fi
    
    # Test admin user exists
    user_query="SELECT count(*) FROM labdabbler.users WHERE username = 'admin';"
    user_count=$(docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U labdabbler_user -d labdabbler_production -t -c "$user_query" | xargs)
    
    if [ "$user_count" -eq 1 ]; then
        success "Admin user exists in database"
    else
        fail "Admin user not found in database"
    fi
}

# Test 6: Redis Connectivity
test_redis() {
    log "Testing Redis connectivity..."
    
    if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
        success "Redis is responding to ping"
    else
        fail "Redis is not responding"
        return 1
    fi
    
    # Test set/get operation
    if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli set test_key "test_value" | grep -q "OK"; then
        success "Redis write operation successful"
    else
        fail "Redis write operation failed"
        return 1
    fi
    
    if [ "$(docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli get test_key | tr -d '\r')" = "test_value" ]; then
        success "Redis read operation successful"
    else
        fail "Redis read operation failed"
    fi
    
    # Cleanup test key
    docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli del test_key > /dev/null
}

# Test 7: API Endpoints
test_api_endpoints() {
    log "Testing API endpoints..."
    
    # Test health endpoint
    if curl -sf http://localhost/api/health | grep -q "healthy"; then
        success "Health endpoint responding correctly"
    else
        fail "Health endpoint not responding correctly"
    fi
    
    # Test detailed health endpoint
    if curl -sf http://localhost/api/health/detailed | jq -e '.status' > /dev/null; then
        success "Detailed health endpoint responding correctly"
    else
        fail "Detailed health endpoint not responding correctly"
    fi
    
    # Test labs endpoint
    if curl -sf http://localhost/api/labs | jq -e 'type == "array"' > /dev/null; then
        success "Labs endpoint responding correctly"
    else
        fail "Labs endpoint not responding correctly"
    fi
    
    # Test containers endpoint
    if curl -sf http://localhost/api/containers | jq -e 'type == "object"' > /dev/null; then
        success "Containers endpoint responding correctly"
    else
        fail "Containers endpoint not responding correctly"
    fi
}

# Test 8: Frontend Functionality
test_frontend() {
    log "Testing frontend functionality..."
    
    # Test main page
    if curl -sf http://localhost/ | grep -q "<!DOCTYPE html>"; then
        success "Frontend main page loads"
    else
        fail "Frontend main page not loading"
    fi
    
    # Test static assets
    if curl -sf http://localhost/health | grep -q "healthy"; then
        success "Frontend health endpoint responding"
    else
        fail "Frontend health endpoint not responding"
    fi
}

# Test 9: SSL/HTTPS (if configured)
test_https() {
    log "Testing HTTPS configuration..."
    
    # Skip if SSL not configured
    if [ ! -f "ssl/labdabbler.crt" ]; then
        warning "SSL certificates not found, skipping HTTPS test"
        return 0
    fi
    
    # Test HTTPS endpoint (with self-signed cert)
    if curl -k -sf https://localhost/health | grep -q "healthy"; then
        success "HTTPS endpoint responding"
    else
        warning "HTTPS endpoint not responding (may need proper domain configuration)"
    fi
    
    # Test SSL redirect
    if curl -sf http://localhost/ -I | grep -q "301"; then
        success "HTTP to HTTPS redirect working"
    else
        warning "HTTP to HTTPS redirect not configured"
    fi
}

# Test 10: Security Headers
test_security_headers() {
    log "Testing security headers..."
    
    # Get response headers
    headers=$(curl -sI http://localhost/)
    
    security_headers=("X-Content-Type-Options" "X-Frame-Options" "X-XSS-Protection")
    
    for header in "${security_headers[@]}"; do
        if echo "$headers" | grep -qi "$header"; then
            success "Security header $header present"
        else
            fail "Security header $header missing"
        fi
    done
}

# Test 11: Performance and Caching
test_performance() {
    log "Testing performance and caching..."
    
    # Test response compression
    if curl -H "Accept-Encoding: gzip" -sI http://localhost/api/containers | grep -qi "content-encoding: gzip"; then
        success "Response compression working"
    else
        warning "Response compression not working"
    fi
    
    # Test API response time
    response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost/api/health)
    if (( $(echo "$response_time < 1.0" | bc -l) )); then
        success "API response time acceptable (${response_time}s)"
    else
        warning "API response time slow (${response_time}s)"
    fi
}

# Test 12: Monitoring Services
test_monitoring() {
    log "Testing monitoring services..."
    
    # Start monitoring services
    docker compose -f "$COMPOSE_FILE" up -d prometheus grafana
    
    # Wait for services to start
    sleep 30
    
    # Test Prometheus
    if wait_for_service "Prometheus" "curl -sf http://localhost:9090/-/healthy" 60; then
        success "Prometheus is responding"
    else
        fail "Prometheus is not responding"
    fi
    
    # Test Grafana
    if wait_for_service "Grafana" "curl -sf http://localhost:3000/api/health" 60; then
        success "Grafana is responding"
    else
        fail "Grafana is not responding"
    fi
}

# Test 13: Error Handling
test_error_handling() {
    log "Testing error handling..."
    
    # Test 404 endpoint
    if curl -sf http://localhost/api/nonexistent | grep -q "404"; then
        success "404 error handling working"
    else
        fail "404 error handling not working"
    fi
    
    # Test invalid JSON
    response_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost/api/labs -H "Content-Type: application/json" -d "invalid json")
    if [ "$response_code" = "422" ] || [ "$response_code" = "400" ]; then
        success "Invalid JSON handling working"
    else
        fail "Invalid JSON handling not working (got $response_code)"
    fi
}

# Test 14: Rate Limiting
test_rate_limiting() {
    log "Testing rate limiting..."
    
    # Make multiple rapid requests
    rate_limit_triggered=false
    for i in {1..20}; do
        response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health)
        if [ "$response_code" = "429" ]; then
            rate_limit_triggered=true
            break
        fi
        sleep 0.1
    done
    
    if [ "$rate_limit_triggered" = true ]; then
        success "Rate limiting is working"
    else
        warning "Rate limiting not triggered (may need adjustment or Redis)"
    fi
}

# Test 15: Backup Functionality
test_backup() {
    log "Testing backup functionality..."
    
    # Test backup script exists and is executable
    if [ -x "postgres/backup.sh" ]; then
        success "Backup script is executable"
    else
        fail "Backup script not found or not executable"
        return 1
    fi
    
    # Create test backup
    if docker compose -f "$COMPOSE_FILE" exec postgres /backups/backup.sh > /dev/null 2>&1; then
        success "Database backup completed successfully"
    else
        warning "Database backup failed (may need volume mount configuration)"
    fi
}

# Cleanup function
cleanup() {
    log "Cleaning up test environment..."
    
    # Remove test Docker images
    docker rmi labdabbler-frontend-test labdabbler-backend-test 2>/dev/null || true
    
    # Clean up test keys in Redis
    docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli del test_key 2>/dev/null || true
    
    info "Cleanup completed"
}

# Generate test report
generate_report() {
    log "Generating test report..."
    
    echo "========================================"
    echo "LabDabbler Production Test Report"
    echo "Generated: $(date)"
    echo "========================================"
    echo
    echo "Test Results:"
    echo "  Passed: $TESTS_PASSED"
    echo "  Failed: $TESTS_FAILED"
    echo "  Total:  $((TESTS_PASSED + TESTS_FAILED))"
    echo
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ ALL TESTS PASSED - Production deployment is ready!${NC}"
    else
        echo -e "${RED}✗ Some tests failed. Review the following issues:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}•${NC} $test"
        done
        echo
        echo "Check the detailed log at: $TEST_LOG"
    fi
    
    echo
    echo "Service Status:"
    docker compose -f "$COMPOSE_FILE" ps
}

# Main test execution
main() {
    log "Starting LabDabbler production deployment tests..."
    
    # Create log directory
    mkdir -p "$(dirname "$TEST_LOG")"
    
    # Run tests
    test_environment
    test_docker_images
    test_ssl_configuration
    test_service_startup
    test_database
    test_redis
    test_api_endpoints
    test_frontend
    test_https
    test_security_headers
    test_performance
    test_monitoring
    test_error_handling
    test_rate_limiting
    test_backup
    
    # Generate report
    generate_report
    
    # Cleanup
    cleanup
    
    # Exit with appropriate code
    if [ $TESTS_FAILED -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Handle script arguments
case "${1:-test}" in
    "test")
        main
        ;;
    "quick")
        # Quick test - just essential services
        test_environment
        test_service_startup
        test_api_endpoints
        generate_report
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 {test|quick|cleanup}"
        echo
        echo "Commands:"
        echo "  test    - Run full production test suite"
        echo "  quick   - Run quick essential tests only"
        echo "  cleanup - Clean up test artifacts"
        exit 1
        ;;
esac
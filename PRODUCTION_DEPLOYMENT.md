# LabDabbler Production Deployment Guide

This guide provides comprehensive instructions for deploying LabDabbler in a production environment.

## Overview

LabDabbler production deployment includes:
- Docker containerized services
- Nginx reverse proxy with SSL/HTTPS
- PostgreSQL database with optimization
- Redis caching and session storage
- Monitoring with Prometheus and Grafana
- Centralized logging with Fluentd
- Security hardening and rate limiting
- Automated backup and update procedures

## Prerequisites

### System Requirements

- Linux server (Ubuntu 20.04+ or CentOS 8+ recommended)
- Docker 20.10+
- Docker Compose 2.0+
- Minimum 4GB RAM, 2 CPU cores
- 50GB disk space for initial deployment
- Network connectivity and domain name

### Domain and SSL

- Register a domain name (e.g., labdabbler.com)
- Configure DNS records:
  - A record: labdabbler.com → your-server-ip
  - A record: www.labdabbler.com → your-server-ip
  - A record: api.labdabbler.com → your-server-ip

## Pre-Deployment Setup

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Create application directory
sudo mkdir -p /opt/labdabbler
sudo chown $USER:$USER /opt/labdabbler
cd /opt/labdabbler
```

### 2. Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/your-org/labdabbler.git .

# Create log directories
sudo mkdir -p /var/log/labdabbler
sudo chown $USER:$USER /var/log/labdabbler
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.production.template .env.production

# Edit environment variables
nano .env.production
```

Required environment variables:
```bash
# Database
DATABASE_PASSWORD=your-secure-database-password

# Redis
REDIS_PASSWORD=your-secure-redis-password

# Application Security
SECRET_KEY=your-secret-key-64-chars-long
JWT_SECRET=your-jwt-secret-64-chars-long

# Monitoring
GRAFANA_PASSWORD=your-grafana-password

# Domain Configuration
ALLOWED_HOSTS=labdabbler.com,api.labdabbler.com,www.labdabbler.com
CORS_ORIGINS=https://labdabbler.com,https://www.labdabbler.com
```

Generate secure secrets:
```bash
# Generate random secrets
openssl rand -base64 48  # For SECRET_KEY
openssl rand -base64 48  # For JWT_SECRET
openssl rand -base64 32  # For passwords
```

## Deployment

### 1. SSL Certificate Setup

#### Option A: Self-Signed Certificates (Development/Testing)
```bash
./ssl/generate-certs.sh
```

#### Option B: Let's Encrypt (Production)
```bash
# Install certbot
sudo apt install certbot

# Generate certificates
sudo ./ssl/letsencrypt-setup.sh
```

### 2. Deploy Application

```bash
# Run deployment script
./scripts/deploy.sh
```

The deployment script will:
1. Check prerequisites
2. Validate environment configuration
3. Create backup of existing deployment
4. Pull latest Docker images
5. Setup SSL certificates
6. Start all services in correct order
7. Verify deployment health
8. Display service status

### 3. Verify Deployment

Check service status:
```bash
./scripts/deploy.sh status
```

Expected output:
```
NAME                    IMAGE               STATUS              PORTS
labdabbler-nginx        nginx:1.25-alpine   Up 2 minutes        0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
labdabbler-frontend     labdabbler-frontend Up 2 minutes        
labdabbler-backend      labdabbler-backend  Up 3 minutes        
labdabbler-postgres     postgres:15-alpine  Up 4 minutes        
labdabbler-redis        redis:7-alpine      Up 4 minutes        
```

Test endpoints:
```bash
# Frontend
curl -k https://your-domain.com/health

# Backend API
curl -k https://api.your-domain.com/api/health

# Detailed health check
curl -k https://api.your-domain.com/api/health/detailed
```

## Post-Deployment Configuration

### 1. Database Initialization

The database is automatically initialized with:
- Application schema and tables
- Indexes for optimal performance
- Default admin user (change password immediately)

Change default admin password:
```bash
# Connect to database
docker compose -f docker-compose.production.yml exec postgres psql -U labdabbler_user -d labdabbler_production

# Update admin password (replace with secure password hash)
UPDATE labdabbler.users SET password_hash = '$2b$12$NEW_HASH_HERE' WHERE username = 'admin';
```

### 2. Monitoring Setup

Access monitoring interfaces:
- Grafana: https://your-domain.com:3000/ (admin/your-grafana-password)
- Prometheus: https://your-domain.com:9090/

Configure Grafana dashboards:
1. Login to Grafana
2. Import provided dashboard configurations
3. Set up alerting rules
4. Configure notification channels

### 3. Backup Configuration

Setup automated backups:
```bash
# Add to crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/labdabbler/postgres/backup.sh

# Add weekly cleanup
0 3 * * 0 find /opt/labdabbler/backups -name "*.tar.gz" -mtime +30 -delete
```

## Maintenance and Operations

### 1. Monitoring

Real-time monitoring:
```bash
# Continuous monitoring
./scripts/monitoring.sh watch

# Generate detailed report
./scripts/monitoring.sh report

# Check specific components
./scripts/monitoring.sh database
./scripts/monitoring.sh performance
```

### 2. Log Management

View logs:
```bash
# All services
./scripts/deploy.sh logs

# Specific service
./scripts/deploy.sh logs backend

# Follow live logs
docker compose -f docker-compose.production.yml logs -f backend
```

Log locations:
- Application logs: `/var/log/labdabbler/`
- Nginx logs: Docker volume `nginx_logs`
- Database logs: Docker volume (managed by PostgreSQL)

### 3. Updates

Update to latest version:
```bash
# This creates a backup, pulls new images, and performs rolling update
./scripts/update.sh
```

Rollback if needed:
```bash
# List available backups
ls -la backups/

# Rollback to specific backup
./scripts/update.sh rollback backups/pre_update_backup_20240101_120000.tar.gz
```

### 4. Scaling

#### Horizontal Scaling (Multiple Backend Instances)

Update docker-compose.production.yml:
```yaml
backend:
  # ... existing configuration
  deploy:
    replicas: 3
```

#### Vertical Scaling (Resource Limits)

```yaml
backend:
  # ... existing configuration
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

## Security Best Practices

### 1. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw enable
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
```

### 2. SSL/TLS Hardening

The nginx configuration includes:
- TLS 1.2 and 1.3 only
- Strong cipher suites
- HSTS headers
- Security headers (CSRF, XSS, etc.)

### 3. Database Security

- Encrypted connections
- Strong password policies
- Regular security updates
- Limited network access

### 4. Container Security

- Non-root users in containers
- Read-only file systems where possible
- Security scanning of images
- Regular base image updates

## Troubleshooting

### Common Issues

#### 1. Services Not Starting

```bash
# Check service logs
./scripts/deploy.sh logs [service-name]

# Check system resources
./scripts/monitoring.sh resources

# Check Docker daemon
sudo systemctl status docker
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL health
./scripts/monitoring.sh database

# Test connection manually
docker compose -f docker-compose.production.yml exec postgres pg_isready -U labdabbler_user
```

#### 3. SSL Certificate Issues

```bash
# Check certificate validity
./scripts/monitoring.sh ssl

# Regenerate certificates
./ssl/generate-certs.sh

# For Let's Encrypt renewal
sudo certbot renew --dry-run
```

#### 4. Performance Issues

```bash
# Check resource usage
./scripts/monitoring.sh resources

# Check performance metrics
./scripts/monitoring.sh performance

# Analyze slow queries
docker compose -f docker-compose.production.yml exec postgres psql -U labdabbler_user -d labdabbler_production -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Emergency Procedures

#### Service Recovery

```bash
# Restart all services
./scripts/deploy.sh restart

# Restart specific service
./scripts/deploy.sh restart backend

# Full redeployment
./scripts/deploy.sh stop
./scripts/deploy.sh deploy
```

#### Data Recovery

```bash
# List available backups
ls -la backups/

# Restore from backup
./scripts/update.sh rollback backups/backup_file.tar.gz
```

## Performance Tuning

### Database Optimization

The PostgreSQL configuration includes optimizations for:
- Connection pooling
- Memory allocation
- Query performance
- Autovacuum settings

Monitor and adjust based on usage:
```sql
-- Check query performance
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation FROM pg_stats WHERE tablename = 'your_table';
```

### Caching Strategy

Redis is configured for:
- Session storage
- API response caching
- Rate limiting data
- Application metrics

Monitor cache performance:
```bash
# Redis info
docker compose -f docker-compose.production.yml exec redis redis-cli info

# Cache hit ratio
docker compose -f docker-compose.production.yml exec redis redis-cli info stats | grep keyspace
```

### Network Optimization

- Enable HTTP/2 in nginx
- Use compression for static assets
- CDN integration for static content
- Connection pooling for database

## Disaster Recovery

### Backup Strategy

- Daily automated database backups
- Configuration backups
- Container image backups
- Off-site backup storage

### Recovery Procedures

1. **Complete System Failure**
   ```bash
   # Restore from backup on new server
   scp backups/latest_backup.tar.gz new-server:/opt/labdabbler/
   ./scripts/update.sh rollback backups/latest_backup.tar.gz
   ```

2. **Data Corruption**
   ```bash
   # Stop services
   ./scripts/deploy.sh stop
   
   # Restore data volumes
   docker run --rm -v labdabbler_postgres_data:/data -v $PWD/backups:/backup alpine tar -xzf /backup/backup_file.tar.gz -C /data
   
   # Restart services
   ./scripts/deploy.sh deploy
   ```

## Support and Maintenance Contacts

- **System Administrator**: [admin email]
- **Database Administrator**: [dba email]
- **Security Team**: [security email]
- **On-call Support**: [support phone/pager]

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Nginx Security Headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

**Last Updated**: $(date)
**Version**: 1.0.0
**Environment**: Production
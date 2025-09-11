#!/bin/bash
# PostgreSQL Backup Script for LabDabbler Production

set -e

# Configuration
DB_NAME="labdabbler_production"
DB_USER="labdabbler_user"
DB_HOST="postgres"
BACKUP_DIR="/backups"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Timestamp for backup file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/labdabbler_backup_$TIMESTAMP.sql"
COMPRESSED_BACKUP="$BACKUP_FILE.gz"

echo "Starting database backup..."

# Create database dump
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=plain \
    > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"

echo "Backup completed: $COMPRESSED_BACKUP"

# Calculate backup size
BACKUP_SIZE=$(du -h "$COMPRESSED_BACKUP" | cut -f1)
echo "Backup size: $BACKUP_SIZE"

# Remove old backups (keep only last RETENTION_DAYS days)
find "$BACKUP_DIR" -name "labdabbler_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Old backups cleaned up (retention: $RETENTION_DAYS days)"

# List current backups
echo "Current backups:"
ls -lh "$BACKUP_DIR"/labdabbler_backup_*.sql.gz | tail -10
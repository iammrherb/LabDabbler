#!/bin/bash
# Let's Encrypt SSL Certificate Setup for Production

set -e

DOMAIN="labdabbler.com"
EMAIL="admin@labdabbler.com"
WEBROOT="/var/www/certbot"

echo "Setting up Let's Encrypt certificates for $DOMAIN..."

# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Create webroot directory
mkdir -p "$WEBROOT"

# Generate certificates
certbot certonly \
    --webroot \
    --webroot-path="$WEBROOT" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    -d "api.$DOMAIN"

# Copy certificates to nginx directory
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "/etc/ssl/certs/labdabbler.crt"
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "/etc/ssl/private/labdabbler.key"

# Set proper permissions
chmod 644 "/etc/ssl/certs/labdabbler.crt"
chmod 600 "/etc/ssl/private/labdabbler.key"

echo "Let's Encrypt certificates installed successfully!"

# Setup auto-renewal
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet && docker exec labdabbler-nginx nginx -s reload") | crontab -

echo "Auto-renewal configured via cron job."
#!/bin/bash
# SSL Certificate Generation Script for LabDabbler Production

set -e

# Configuration
DOMAIN="labdabbler.com"
COUNTRY="US"
STATE="CA"
CITY="San Francisco"
ORGANIZATION="LabDabbler"
OU="IT Department"
EMAIL="admin@labdabbler.com"

# Directories
SSL_DIR="/etc/ssl"
CERT_DIR="$SSL_DIR/certs"
KEY_DIR="$SSL_DIR/private"

# Create directories
mkdir -p "$CERT_DIR" "$KEY_DIR"
chmod 700 "$KEY_DIR"

echo "Generating SSL certificates for $DOMAIN..."

# Generate private key
openssl genrsa -out "$KEY_DIR/labdabbler.key" 4096
chmod 600 "$KEY_DIR/labdabbler.key"

# Generate certificate signing request
openssl req -new \
    -key "$KEY_DIR/labdabbler.key" \
    -out "$SSL_DIR/labdabbler.csr" \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORGANIZATION/OU=$OU/CN=$DOMAIN/emailAddress=$EMAIL"

# Generate self-signed certificate (for development/testing)
# In production, replace with proper CA-signed certificate
openssl x509 -req \
    -days 365 \
    -in "$SSL_DIR/labdabbler.csr" \
    -signkey "$KEY_DIR/labdabbler.key" \
    -out "$CERT_DIR/labdabbler.crt" \
    -extensions v3_req \
    -extfile <(cat <<EOF
[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = labdabbler.com
DNS.2 = www.labdabbler.com
DNS.3 = api.labdabbler.com
DNS.4 = localhost
IP.1 = 127.0.0.1
EOF
)

chmod 644 "$CERT_DIR/labdabbler.crt"

# Generate DH parameters for stronger security
openssl dhparam -out "$CERT_DIR/dhparam.pem" 2048
chmod 644 "$CERT_DIR/dhparam.pem"

echo "SSL certificates generated successfully!"
echo "Certificate: $CERT_DIR/labdabbler.crt"
echo "Private key: $KEY_DIR/labdabbler.key"
echo "DH parameters: $CERT_DIR/dhparam.pem"

# Verify certificate
echo -e "\nCertificate verification:"
openssl x509 -in "$CERT_DIR/labdabbler.crt" -text -noout | grep -A 1 "Subject:"
openssl x509 -in "$CERT_DIR/labdabbler.crt" -text -noout | grep -A 3 "Subject Alternative Name"
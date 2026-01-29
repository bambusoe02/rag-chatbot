#!/bin/bash

# Generate secure secrets

echo "🔐 Generating secure secrets..."

mkdir -p secrets

# Generate database password
openssl rand -base64 32 > secrets/db_password.txt
echo "✅ Database password generated"

# Generate JWT secret
openssl rand -hex 64 > secrets/jwt_secret.txt
echo "✅ JWT secret generated"

# Generate API encryption key
openssl rand -hex 32 > secrets/api_key.txt
echo "✅ API key generated"

# Set permissions
chmod 600 secrets/*
echo "✅ Permissions set (600)"

echo ""
echo "⚠️  IMPORTANT: Add secrets/ to .gitignore"
echo "⚠️  Backup these files securely!"
echo ""
echo "Contents:"
ls -lh secrets/


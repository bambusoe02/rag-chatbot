#!/bin/bash

# Setup SSL certificates with Let's Encrypt

echo "🔐 Setting up SSL with Let's Encrypt..."

# Check if domain is provided
if [ -z "$1" ]; then
    echo "Usage: ./setup_ssl.sh your-domain.com"
    exit 1
fi

DOMAIN=$1
EMAIL="admin@${DOMAIN}"

# Install certbot
echo "📦 Installing certbot..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
elif command -v yum &> /dev/null; then
    sudo yum install -y certbot python3-certbot-nginx
else
    echo "❌ Unsupported package manager"
    exit 1
fi

# Stop nginx temporarily
echo "🛑 Stopping nginx..."
docker-compose stop nginx

# Obtain certificate
echo "🔑 Obtaining SSL certificate..."
sudo certbot certonly --standalone \
    -d ${DOMAIN} \
    --email ${EMAIL} \
    --agree-tos \
    --non-interactive

if [ $? -ne 0 ]; then
    echo "❌ Failed to obtain certificate"
    exit 1
fi

# Update nginx config with domain
echo "⚙️  Updating nginx configuration..."
sed -i "s/your-domain.com/${DOMAIN}/g" nginx/ssl.conf

# Start nginx with SSL
echo "🚀 Starting nginx with SSL..."
docker-compose up -d nginx

# Setup auto-renewal
echo "♻️  Setting up auto-renewal..."
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && docker-compose restart nginx") | crontab -

echo ""
echo "✅ SSL setup complete!"
echo "📝 Certificate location: /etc/letsencrypt/live/${DOMAIN}/"
echo "🔄 Auto-renewal: Daily at 3 AM"
echo "🌐 Access your site: https://${DOMAIN}"


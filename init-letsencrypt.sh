#!/bin/bash

# Stop any running containers
docker-compose -f docker-compose.prod.yml down

# Create necessary directories
mkdir -p certs/conf/live/yourdomain.com

# Start Nginx for certificate validation
echo "Starting Nginx for certificate validation..."
docker-compose -f docker-compose.prod.yml up -d nginx

# Wait for Nginx to start
echo "Waiting for Nginx to start..."
sleep 5

# Get certificates using certbot
docker run --rm -it \
  -v "$(pwd)/certs:/etc/letsencrypt" \
  -v "$(pwd)/certs/www:/var/www/certbot" \
  certbot/certbot certonly \
  --webroot -w /var/www/certbot \
  -d yourdomain.com \
  --email your.email@example.com \
  --agree-tos --non-interactive --expand

# Stop Nginx
docker-compose -f docker-compose.prod.yml stop nginx

echo "SSL certificates generated successfully!"

echo "Initial setup complete. You can now start the production stack with:"
echo "docker-compose -f docker-compose.prod.yml up -d

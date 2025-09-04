#!/bin/bash

# Setup script for Digital Ocean droplet
# Run this on your droplet first before deploying

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /opt/pdf-editor/{uploads,outputs}

# Configure firewall
ufw allow 22
ufw allow 8000
ufw --force enable

# Start Docker service
systemctl enable docker
systemctl start docker

echo "✅ Droplet setup completed!"
echo "🔥 Now run the deploy.sh script from your local machine"

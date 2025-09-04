#!/bin/bash

# Deployment script for Digital Ocean droplet
# Usage: ./deploy.sh

set -e

# Configuration
DROPLET_IP="159.223.198.145"
DROPLET_USER="root"
SSH_KEY="~/.ssh/droplet_key"
APP_NAME="pdf-editor"
APP_DIR="/opt/$APP_NAME"

echo "🚀 Starting deployment to Digital Ocean droplet: $DROPLET_IP"

# Create deployment archive
echo "📦 Creating deployment package..."
tar -czf deployment.tar.gz \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='.env' \
    --exclude='*.pyc' \
    --exclude='uploads/*' \
    --exclude='outputs/*' \
    --exclude='.venv' \
    .

# Copy files to droplet
echo "📤 Copying files to droplet..."
scp -i $SSH_KEY deployment.tar.gz $DROPLET_USER@$DROPLET_IP:/tmp/

# Deploy on droplet
echo "🔧 Deploying on droplet..."
ssh -i $SSH_KEY $DROPLET_USER@$DROPLET_IP << 'EOF'
    # Stop existing container if running
    docker-compose -f /opt/pdf-editor/docker-compose.yml down 2>/dev/null || true
    
    # Create app directory
    mkdir -p /opt/pdf-editor
    
    # Extract new files
    cd /opt/pdf-editor
    tar -xzf /tmp/deployment.tar.gz
    
    # Create necessary directories
    mkdir -p uploads outputs
    
    # Build and start the application
    docker-compose up --build -d
    
    # Clean up
    rm /tmp/deployment.tar.gz
    
    # Show status
    docker-compose ps
EOF

# Clean up local files
rm deployment.tar.gz

echo "✅ Deployment completed!"
echo "🌐 Your application should be available at: http://$DROPLET_IP:8000"
echo "📊 Check status with: ssh -i $SSH_KEY $DROPLET_USER@$DROPLET_IP 'docker-compose -f /opt/pdf-editor/docker-compose.yml ps'"

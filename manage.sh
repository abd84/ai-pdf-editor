#!/bin/bash

# Quick management scripts for the droplet
SSH_KEY="~/.ssh/droplet_key"
DROPLET="root@159.223.198.145"

case "$1" in
    "logs")
        echo "📋 Fetching application logs..."
        ssh -i $SSH_KEY $DROPLET "cd /opt/pdf-editor && docker-compose logs --tail=50"
        ;;
    "status")
        echo "📊 Checking application status..."
        ssh -i $SSH_KEY $DROPLET "cd /opt/pdf-editor && docker-compose ps"
        ;;
    "restart")
        echo "🔄 Restarting application..."
        ssh -i $SSH_KEY $DROPLET "cd /opt/pdf-editor && docker-compose restart"
        ;;
    "stop")
        echo "⏹️ Stopping application..."
        ssh -i $SSH_KEY $DROPLET "cd /opt/pdf-editor && docker-compose down"
        ;;
    "start")
        echo "▶️ Starting application..."
        ssh -i $SSH_KEY $DROPLET "cd /opt/pdf-editor && docker-compose up -d"
        ;;
    "shell")
        echo "🐚 Opening SSH shell..."
        ssh -i $SSH_KEY $DROPLET
        ;;
    *)
        echo "Usage: $0 {logs|status|restart|stop|start|shell}"
        echo ""
        echo "Available commands:"
        echo "  logs    - View application logs"
        echo "  status  - Check if application is running"
        echo "  restart - Restart the application"
        echo "  stop    - Stop the application"
        echo "  start   - Start the application"
        echo "  shell   - Open SSH shell to droplet"
        ;;
esac

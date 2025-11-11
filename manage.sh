#!/bin/bash
# ГЛАВНЫЙ СКРИПТ УПРАВЛЕНИЯ RBDNTI

case "$1" in
    dev|develop|development)
        echo "🚀 Starting DEVELOPMENT mode..."
        ./develop.sh
        ;;
        
    build|prepare)
        echo "📦 Preparing OFFLINE package..."
        ./prepare-offline.sh
        ;;
        
    stop)
        echo "🛑 Stopping services..."
        docker compose -f docker-compose.dev.yml down
        ;;
        
    logs)
        echo "📋 Showing logs..."
        docker compose -f docker-compose.dev.yml logs -f web
        ;;
        
    clean)
        echo "🧹 Cleaning up..."
        docker compose -f docker-compose.dev.yml down -v
        docker system prune -f
        ;;
        
    *)
        echo "Usage: $0 {dev|build|stop|logs|clean}"
        echo ""
        echo "Commands:"
        echo "  dev     - Start development mode (build from source)"
        echo "  build   - Prepare offline deployment package"
        echo "  stop    - Stop all services"
        echo "  logs    - Show application logs"
        echo "  clean   - Stop and clean everything"
        exit 1
esac
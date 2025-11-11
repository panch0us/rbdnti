#!/bin/bash
# РЕЖИМ РАЗРАБОТКИ - использует сборку из исходников

echo "=== Starting Development Mode ==="

# Создаем временный docker-compose с build:
cat > docker-compose.dev.yml << 'EOF'
services:
  web:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: rbdnti_web
    env_file: .env
    restart: unless-stopped
    volumes:
      - ./data/db:/app/rbdnti/db
      - ./data/media:/app/rbdnti/media
      - ./data/staticfiles:/app/rbdnti/staticfiles
    expose:
      - "8000"

  nginx:
    image: nginx:1.25-alpine
    container_name: rbdnti_nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./data/staticfiles:/static:ro
      - ./data/media:/media:ro
    depends_on:
      - web
EOF

echo "Starting services in DEVELOPMENT mode..."
docker compose -f docker-compose.dev.yml up -d --build

echo "=== Development mode started ==="
echo "Website: http://localhost/"
echo "Admin: http://localhost/admin/"
#!/bin/bash
set -e

echo "=== Preparing offline deployment package ==="

# Создаем папку для пакета
mkdir -p rbdnti-offline-package

echo "1. Building final production image..."
docker compose -f docker-compose.dev.yml build web

echo "2. Saving Docker images..."
docker save rbdnti-web:latest -o rbdnti-offline-package/web.tar
docker save nginx:1.25-alpine -o rbdnti-offline-package/nginx.tar

echo "3. Creating production docker-compose.yml..."
cat > rbdnti-offline-package/docker-compose.yml << 'EOF'
services:
  web:
    image: rbdnti-web:latest
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

echo "4. Copying configuration files..."
cp -r nginx .env rbdnti-offline-package/

echo "5. Creating deployment script..."
cat > rbdnti-offline-package/deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Deploying RBDNTI Application (PRODUCTION) ==="

echo "Step 1: Loading Docker images..."
docker load -i web.tar
docker load -i nginx.tar

echo "Step 2: Creating data directories..."
mkdir -p data/db data/media data/staticfiles

echo "Step 3: Starting services..."
docker compose up -d

echo "Step 4: Waiting for initialization..."
sleep 30

echo "Step 5: Checking status..."
docker compose ps

echo "=== Production Deployment Completed ==="
echo "Application: http://your-server-ip/"
echo "Admin panel: http://your-server-ip/admin/"
EOF

chmod +x rbdnti-offline-package/deploy.sh

echo "6. Creating archive..."
tar -czf rbdnti-offline-$(date +%Y%m%d).tar.gz rbdnti-offline-package/

echo "7. Cleaning up..."
rm -rf rbdnti-offline-package

echo ""
echo "=== OFFLINE PACKAGE READY ==="
echo "File: rbdnti-offline-$(date +%Y%m%d).tar.gz"
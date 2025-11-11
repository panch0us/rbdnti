#!/bin/bash
set -e

echo "=== Preparing offline deployment package ==="

# Проверки
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env file not found in current directory!"
    exit 1
fi

if [ ! -d "nginx" ]; then
    echo "❌ ERROR: nginx directory not found!"
    exit 1
fi

# Создаем папку для пакета
PACKAGE_DIR="rbdnti-offline-package"
mkdir -p $PACKAGE_DIR

echo "1. Building final production image..."
docker compose -f docker-compose.dev.yml build web

echo "2. Saving Docker images..."
docker save rbdnti-web:latest -o $PACKAGE_DIR/web.tar
docker save nginx:1.25-alpine -o $PACKAGE_DIR/nginx.tar

echo "3. Creating production docker-compose.yml..."
cat > $PACKAGE_DIR/docker-compose.yml << 'EOF'
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
cp -r nginx .env $PACKAGE_DIR/

echo "5. Creating deployment script..."
cat > $PACKAGE_DIR/deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Deploying RBDNTI Application ==="

echo "Step 1: Loading Docker images..."
docker load -i web.tar
docker load -i nginx.tar

echo "Step 2: Creating data directories..."
mkdir -p data/db data/media data/staticfiles

echo "Step 3: Setting permissions..."
chmod 755 data/db data/media data/staticfiles

echo "Step 4: Starting services..."
docker compose up -d

echo "Step 5: Waiting for initialization..."
sleep 30

echo "Step 6: Checking status..."
docker compose ps

echo "=== Deployment Completed ==="
echo "Application: http://your-server-ip/"
echo "Admin: http://your-server-ip/admin/"
echo ""
echo "Next: Create admin user: docker compose exec web python /app/rbdnti/manage.py createsuperuser"
EOF

chmod +x $PACKAGE_DIR/deploy.sh

echo "6. Creating update script..."
cat > $PACKAGE_DIR/update.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Updating RBDNTI Application ==="

echo "Step 1: Creating backup..."
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP_FILE" data/
echo "Backup created: $BACKUP_FILE"

echo "Step 2: Stopping ANY running rbdnti services..."
docker stop rbdnti_web rbdnti_nginx 2>/dev/null || true
docker rm rbdnti_web rbdnti_nginx 2>/dev/null || true

echo "Step 3: Loading new image..."
docker load -i web.tar

echo "Step 4: Starting services..."
docker compose up -d

echo "Step 5: Verification..."
sleep 30
docker compose logs web --tail=5

if curl -s http://localhost/ > /dev/null; then
    echo "✅ Application is accessible"
else
    echo "❌ Application is not accessible - check logs"
    docker compose logs web
    exit 1
fi

echo "=== Update Completed ==="
echo "Backup: $BACKUP_FILE"
echo "Application: http://your-server-ip/"
EOF

chmod +x $PACKAGE_DIR/update.sh

echo "7. Creating archive..."
ARCHIVE_NAME="rbdnti-offline-$(date +%Y%m%d).tar.gz"
tar -czf $ARCHIVE_NAME $PACKAGE_DIR/

echo "8. Cleaning up..."
rm -rf $PACKAGE_DIR

echo ""
echo "=== OFFLINE PACKAGE READY ==="
echo "📦 Archive: $ARCHIVE_NAME"
echo ""
echo "DEPLOYMENT:"
echo "1. tar -xzf $ARCHIVE_NAME"
echo "2. cd rbdnti-offline-package"
echo "3. ./deploy.sh"
echo ""
echo "UPDATE:"
echo "1. Extract new version"
echo "2. Copy data from old version manually: cp -r rbdnti-v1/data rbdnti-v2/"
echo "3. ./update.sh"
#!/bin/bash
set -euo pipefail

# manage.sh - unified control script (dev, migrations, build, offline package, deploy helpers)
ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
RBDNTI="$BACKEND/rbdnti"
DEV_COMPOSE="$ROOT/docker-compose.dev.yml"
IMAGE_NAME="rbdnti-web:latest"
PACKAGE_PREFIX="rbdnti-offline"

info(){ echo "=> $*"; }
err(){ echo "ERROR: $*" >&2; }

# generate development docker-compose (bind-mounts code and data)
generate_dev_compose(){
cat > "$DEV_COMPOSE" <<'YAML'
services:
  web:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: rbdnti_web
    env_file: .env
    restart: unless-stopped
    volumes:
      - ./backend:/app
      - ./backend/rbdnti/data/db:/app/rbdnti/data/db
      - ./backend/rbdnti/data/media:/app/rbdnti/data/media
      - ./backend/rbdnti/data/staticfiles:/app/rbdnti/data/staticfiles
    ports:
      - "8000:8000"
  nginx:
    image: nginx:1.25-alpine
    container_name: rbdnti_nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./backend/rbdnti/data/staticfiles:/static:ro
      - ./backend/rbdnti/data/media:/media:ro
    depends_on:
      - web
YAML
info "Generated $DEV_COMPOSE"
}

ensure_data_dirs(){
  mkdir -p "$RBDNTI/data/db" "$RBDNTI/data/media" "$RBDNTI/data/staticfiles"
}

is_running(){
  if [ -f "$DEV_COMPOSE" ]; then
    docker compose -f "$DEV_COMPOSE" ps -q web 2>/dev/null || true
  fi
}

cmd_dev(){
  info "Start development environment (bind-mount code)"
  ensure_data_dirs
  generate_dev_compose
  docker compose -f "$DEV_COMPOSE" up -d --build
  info "Dev up. App: http://localhost:8000/"
}

cmd_makemigrations(){
  info "Make migrations (containers will be started temporarily if needed)"
  ensure_data_dirs
  generate_dev_compose
  if [ -z "$(is_running)" ]; then
    info "Starting dev containers temporarily..."
    docker compose -f "$DEV_COMPOSE" up -d --build
    TEMP_STARTED=true
    sleep 2
  else
    TEMP_STARTED=false
  fi

  docker compose -f "$DEV_COMPOSE" run --rm web sh -c "cd /app/rbdnti && python manage.py makemigrations"

  info "makemigrations done. Generated migration files (if any) are in backend/rbdnti/*/migrations."
  echo "Don't forget: git add && git commit them."

  if [ "$TEMP_STARTED" = true ]; then
    info "Stopping temporary dev containers..."
    docker compose -f "$DEV_COMPOSE" down
  fi
}

cmd_migrate(){
  info "Apply migrations (will start dev temporarily if necessary)"
  ensure_data_dirs
  generate_dev_compose
  if [ -z "$(is_running)" ]; then
    docker compose -f "$DEV_COMPOSE" up -d --build
    TEMP_STARTED=true
    sleep 2
  else
    TEMP_STARTED=false
  fi

  docker compose -f "$DEV_COMPOSE" exec web sh -c "cd /app/rbdnti && python manage.py migrate --noinput"

  info "migrate finished."
  if [ "$TEMP_STARTED" = true ]; then
    info "Stopping temporary dev containers..."
    docker compose -f "$DEV_COMPOSE" down
  fi
}

cmd_stop(){
  if [ -f "$DEV_COMPOSE" ]; then
    docker compose -f "$DEV_COMPOSE" down
    info "Dev stopped."
  else
    echo "No dev compose found."
  fi
}

cmd_logs(){
  if [ -f "$DEV_COMPOSE" ]; then
    docker compose -f "$DEV_COMPOSE" logs -f web
  else
    echo "No dev compose found."
  fi
}

cmd_clean(){
  if [ -f "$DEV_COMPOSE" ]; then
    docker compose -f "$DEV_COMPOSE" down -v || true
  fi
  docker system prune -f || true
  info "Clean done."
}

# Build production image: IMPORTANT - this build MUST NOT include data (db) by default.
cmd_build(){
  info "Building production image (code + migrations). DATA WILL NOT be embedded into image."

  if [ ! -f "$ROOT/.env" ]; then
    err ".env file missing in project root. Create it before build."
    exit 1
  fi

  # warn if migrations absent for news_site
  if [ ! -d "$RBDNTI/news_site/migrations" ] || [ "$(ls -A "$RBDNTI/news_site/migrations" | wc -l)" -le 1 ]; then
    echo "WARNING: no migrations found for news_site. If you changed models, run './manage.sh makemigrations' and commit migrations."
    read -p "Continue build anyway? (y/N): " yn
    if [ "${yn:-N}" != "y" ]; then
      echo "Aborting build."
      exit 1
    fi
  fi

  info "Building docker image $IMAGE_NAME from backend/ (data excluded via .dockerignore)"
  docker build -f "$BACKEND/Dockerfile" -t "$IMAGE_NAME" "$BACKEND"
  info "Image built: $IMAGE_NAME"
}

# Create offline package: default DOES NOT embed DB into image; you may pass --include-data to copy data into package (not image)
cmd_package_offline(){
  INCLUDE_DATA=false
  while (( "$#" )); do
    case "$1" in
      --include-data) INCLUDE_DATA=true; shift ;;
      -h|--help) echo "Usage: $0 package-offline [--include-data]"; return 0 ;;
      *) shift ;;
    esac
  done

  info "Creating offline package (image + optional data copy). INCLUDE_DATA=$INCLUDE_DATA"
  TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
  PACKAGE_DIR="$(mktemp -d /tmp/rbdnti-package-XXXX)"
  mkdir -p "$PACKAGE_DIR"

  # ensure image exists; if not, build it
  if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    info "Image $IMAGE_NAME not found locally — building first."
    cmd_build
  fi

  info "Saving web image to package..."
  docker save "$IMAGE_NAME" -o "$PACKAGE_DIR/web.tar"

  info "Saving nginx image to package..."
  docker pull nginx:1.25-alpine >/dev/null 2>&1 || true
  docker save nginx:1.25-alpine -o "$PACKAGE_DIR/nginx.tar"

  # optionally copy data into package (for transporting to offline prod)
  if [ "$INCLUDE_DATA" = true ]; then
    info "Copying data into package (this can include db.sqlite3) - USE WITH CARE!"
    mkdir -p "$PACKAGE_DIR/data"
    rsync -a "$RBDNTI/data/" "$PACKAGE_DIR/data/"
  else
    info "Not copying live data into package. On the offline host create data dirs and place db.sqlite3 there before deploy."
  fi

  # produce docker-compose for package
  cat > "$PACKAGE_DIR/docker-compose.yml" <<'YAML'
version: '3.8'
services:
  web:
    image: rbdnti-web:latest
    container_name: rbdnti_web
    env_file: .env
    restart: unless-stopped
    volumes:
      - ./data/db:/app/rbdnti/data/db
      - ./data/media:/app/rbdnti/data/media
      - ./data/staticfiles:/app/rbdnti/data/staticfiles
    ports:
      - "8000:8000"
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
YAML

  cp -r "$ROOT/nginx" "$ROOT/.env" "$PACKAGE_DIR/" 2>/dev/null || true

  # create deploy script
  cat > "$PACKAGE_DIR/deploy.sh" <<'SH'
#!/bin/bash
set -e
echo "Loading images..."
docker load -i web.tar
docker load -i nginx.tar
echo "Creating data dirs..."
mkdir -p data/db data/media data/staticfiles
chmod 755 data/db data/media data/staticfiles || true
echo "Starting services..."
docker compose up -d
sleep 8
docker compose ps
echo "Done."
SH
  chmod +x "$PACKAGE_DIR/deploy.sh"

  # create update script
  cat > "$PACKAGE_DIR/update.sh" <<'SH'
#!/bin/bash
set -e
echo "Backup data..."
BACKUP="backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$BACKUP" data/
echo "Loading new web image..."
docker load -i web.tar
docker compose up -d
docker compose logs web --tail=20
echo "Update done. Backup: $BACKUP"
SH
  chmod +x "$PACKAGE_DIR/update.sh"

  ARCHIVE="${PACKAGE_PREFIX}-${TIMESTAMP}.tar.gz"
  tar -czf "$ROOT/$ARCHIVE" -C "$PACKAGE_DIR" .
  info "Offline package created: $ROOT/$ARCHIVE"

  rm -rf "$PACKAGE_DIR"
}

# Helper: apply migrations on remote/production host using existing volume or data dir.
# Usage suggestion in docs: docker run --rm -v production_data:/app/rbdnti/data IMAGE_NAME python manage.py migrate --noinput
# We'll print recommended commands instead of running them remotely for safety.
cmd_help_deploy(){
  cat <<EOF

DEPLOY / MIGRATIONS ON OFFLINE/PROD (recommended safe workflow)

1) Build image locally (no DB in image):
   ./manage.sh build

2) Create offline package (no DB copied by default):
   ./manage.sh package-offline
   # or include DB (dangerous — will copy your current local DB into the package):
   ./manage.sh package-offline --include-data

3) Transfer the created archive (rbdnti-offline-*.tar.gz) to the offline host & extract.

4) On the offline host: BEFORE starting new containers, ALWAYS backup the live DB:
   cp data/db/db.sqlite3 data/db/db.sqlite3.bak.$(date +%F_%T)

5) Apply migrations on the offline/prod DB (recommended, run once before starting web containers):
   # Option A: using docker compose in the extracted package (preferred)
   docker compose run --rm web sh -c "python /app/rbdnti/manage.py migrate --noinput"

   # Option B: run with specific data volume mount:
   docker run --rm -v /absolute/path/to/extracted/package/data/db:/app/rbdnti/data/db rbdnti-web:latest \
     sh -c "python /app/rbdnti/manage.py migrate --noinput"

6) Start containers:
   docker compose up -d

IMPORTANT:
- Don't overwrite the prod DB by replacing 'data/db/db.sqlite3' with an older copy unless you know you want to restore.
- Always commit migration files to git and include them in the image before deploying.

EOF
}

usage(){
  cat <<EOF
Usage: $0 <command> [options]
Commands:
  dev                      - start dev with bind-mount (docker-compose.dev.yml generated)
  makemigrations           - run makemigrations (dev container)
  migrate                  - run migrate (dev container)
  build                    - build production image (code + migrations). DOES NOT include data.
  package-offline [--include-data] - build offline package (.tar.gz) with web + nginx images; optionally include data/
  help-deploy              - print recommended offline deploy & migrate commands
  stop                     - stop dev compose
  logs                     - follow web logs
  clean                    - down -v and prune
  help                     - show this message
EOF
}

case "${1:-help}" in
  dev) cmd_dev ;;
  makemigrations) cmd_makemigrations ;;
  migrate) cmd_migrate ;;
  build) cmd_build ;;
  package-offline) shift; cmd_package_offline "$@" ;;
  help-deploy) cmd_help_deploy ;;
  stop) cmd_stop ;;
  logs) cmd_logs ;;
  clean) cmd_clean ;;
  help|-h|--help) usage ;;
  *) echo "Unknown command"; usage; exit 1 ;;
esac

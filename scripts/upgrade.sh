#!/usr/bin/env bash
set -euo pipefail

FERRY_HOME="${FERRY_HOME:-/opt/ferry}"
COMPOSE_FILE="${FERRY_HOME}/docker-compose.yml"

# Parse --no-backup flag
SKIP_BACKUP=false
while [ $# -gt 0 ]; do
  case "$1" in
    --no-backup)
      SKIP_BACKUP=true
      shift
      ;;
    -*)
      echo "Usage: $0 [--no-backup]"
      echo ""
      echo "  --no-backup    Skip pre-upgrade backup (not recommended)"
      exit 1
      ;;
    *)
      break
      ;;
  esac
done

echo "=== FERRY Upgrade ==="

if [ ! -d "$FERRY_HOME/.git" ]; then
  echo "Error: $FERRY_HOME is not a git repository."
  echo "Run install.sh first."
  exit 1
fi

cd "$FERRY_HOME"

# Create a pre-upgrade backup unless explicitly skipped
if [ "$SKIP_BACKUP" = false ]; then
  echo "Creating pre-upgrade backup..."
  if ./scripts/backup.sh; then
    echo "Pre-upgrade backup completed."
  else
    echo ""
    echo "ERROR: Pre-upgrade backup failed."
    echo ""
    echo "The upgrade cannot proceed without a recent backup."
    echo "If the database migration fails, there will be no recovery path."
    echo ""
    echo "To create a backup manually and retry:"
    echo "  make backup && make upgrade"
    echo ""
    echo "To bypass this check (not recommended):"
    echo "  make upgrade ARGS=--no-backup"
    exit 1
  fi
else
  echo "Skipping pre-upgrade backup (--no-backup specified)."
fi

# Pull latest code
echo "Pulling latest code..."
git fetch origin
git checkout main
git pull origin main

# Rebuild application images
echo "Rebuilding application images..."
docker compose -f "$COMPOSE_FILE" build

# Rebuild analysis container images
echo "Rebuilding analysis container images..."
for dir in execution-environments/*/; do
    tag="ferry/$(basename "$dir"):latest"
    echo "  Building $tag..."
    docker build -t "$tag" "$dir"
done

# Restart services
echo "Restarting services..."
docker compose -f "$COMPOSE_FILE" up -d

# Wait for database
echo "Waiting for PostgreSQL..."
until docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U ferry 2>/dev/null; do
  sleep 2
done

# Run migrations
echo "Running database migrations..."
docker compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head

# Health check
echo "Running health checks..."
./scripts/healthcheck.sh

echo ""
echo "=== FERRY upgrade complete ==="

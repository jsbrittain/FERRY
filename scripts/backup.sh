#!/usr/bin/env bash
set -euo pipefail

FERRY_HOME="${FERRY_HOME:-/opt/ferry}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/ferry}"
COMPOSE_FILE="${FERRY_HOME}/docker-compose.yml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/ferry_${TIMESTAMP}"

echo "=== FERRY Backup ==="

mkdir -p "$BACKUP_PATH"

# Dump PostgreSQL database
echo "Backing up PostgreSQL..."
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dumpall -U ferry > "${BACKUP_PATH}/postgres.sql"

# Backup environment config
echo "Backing up configuration..."
if [ -f "${FERRY_HOME}/.env" ]; then
  cp "${FERRY_HOME}/.env" "${BACKUP_PATH}/.env"
fi

# Backup persistent volumes (outputs, datasets)
echo "Backing up data volumes..."
if [ -d "/var/lib/ferry" ]; then
  tar czf "${BACKUP_PATH}/data.tar.gz" -C /var/lib/ferry .
fi

# Compress backup
echo "Compressing backup..."
tar czf "${BACKUP_DIR}/ferry_${TIMESTAMP}.tar.gz" -C "$BACKUP_DIR" "ferry_${TIMESTAMP}"
rm -rf "$BACKUP_PATH"

# Keep only last 30 backups
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "ferry_*.tar.gz" -mtime +30 -delete

echo ""
echo "=== Backup complete: ${BACKUP_DIR}/ferry_${TIMESTAMP}.tar.gz ==="

#!/usr/bin/env bash
set -euo pipefail

# seed-developer.sh — seed developer account and test database
#
# Prerequisite: seed-institution.sh must have completed (admin must exist).
# Idempotent: safe to run multiple times.

echo "Seeding developer account..."
docker compose exec -T backend python -m app.cli seed-developer

echo "Creating test database..."
docker compose exec -T postgres psql -U ferry -c "CREATE DATABASE ferry_test;" 2>/dev/null || true

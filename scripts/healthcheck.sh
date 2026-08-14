#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FERRY_HOME="${FERRY_HOME:-$(cd "$SCRIPT_DIR/.." && pwd)}"
COMPOSE_FILE="${FERRY_HOME}/docker-compose.yml"

echo "=== FERRY Health Check ==="

ERRORS=0

# Check Docker is running
if docker info >/dev/null 2>&1; then
  echo "  [PASS] Docker Engine"
else
  echo "  [FAIL] Docker Engine"
  ERRORS=$((ERRORS + 1))
fi

# Check compose file exists
if [ -f "$COMPOSE_FILE" ]; then
  echo "  [PASS] docker-compose.yml found"
else
  echo "  [FAIL] docker-compose.yml not found"
  ERRORS=$((ERRORS + 1))
fi

# Check each service container
for SERVICE in reverse-proxy frontend backend postgres redis worker; do
  STATUS=$(docker compose -f "$COMPOSE_FILE" ps --format json "$SERVICE" 2>/dev/null | grep -c '"State":"running"' || true)
  if [ "$STATUS" -ge 1 ]; then
    echo "  [PASS] $SERVICE"
  else
    echo "  [FAIL] $SERVICE"
    ERRORS=$((ERRORS + 1))
  fi
done

# Resolve the reachable URL: explicit env var > execution context > .env > default
if [ -z "${PUBLIC_URL:-}" ] && [ -f .ferry-context ]; then
  PUBLIC_URL="$(sed -n 's/^FERRY_REACHABLE_URL=//p' .ferry-context 2>/dev/null || true)"
fi
if [ -z "${PUBLIC_URL:-}" ] && [ -f .env ]; then
  PUBLIC_URL="$(sed -n 's/^PUBLIC_URL=//p' .env 2>/dev/null || true)"
fi
DEFAULT_URL="${PUBLIC_URL:-https://localhost}"

# Check API health endpoint through reverse proxy
API_URL="${API_URL:-$DEFAULT_URL}"
if curl -skf --connect-timeout 5 "${API_URL}/api/health" >/dev/null 2>&1; then
  echo "  [PASS] API health endpoint"
else
  echo "  [FAIL] API health endpoint"
  ERRORS=$((ERRORS + 1))
fi

# Check frontend is serving through reverse proxy
FRONTEND_URL="${FRONTEND_URL:-$DEFAULT_URL}"
if curl -skf --connect-timeout 5 "${FRONTEND_URL}/" >/dev/null 2>&1; then
  echo "  [PASS] Frontend"
else
  echo "  [FAIL] Frontend"
  ERRORS=$((ERRORS + 1))
fi

echo ""
if [ "$ERRORS" -eq 0 ]; then
  echo "=== All checks passed ==="
  exit 0
else
  echo "=== ${ERRORS} check(s) failed ==="
  exit 1
fi

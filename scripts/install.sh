#!/usr/bin/env bash
set -euo pipefail

# install.sh — full system installation
#
# Prerequisite: infrastructure provisioning must have completed
# before this script runs — storage directories must exist with
# correct ownership (see vm/runtime.md for the two-phase architecture).
#
# Handles environment setup (clone, directory provisioning) then
# delegates all application-level initialisation to bootstrap.sh.

DEV_MODE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dev) DEV_MODE=true; shift ;;
    *) echo "Usage: $0 [--dev]"; exit 1 ;;
  esac
done

FERRY_HOME="${FERRY_HOME:-/opt/ferry}"
REPO_URL="${REPO_URL:-https://github.com/kraemer-lab/FERRY.git}"
BRANCH="${BRANCH:-main}"

echo "=== FERRY Install ==="

if [ "$DEV_MODE" = true ]; then
  if [ ! -d "$FERRY_HOME" ]; then
    echo "ERROR: $FERRY_HOME does not exist."
    echo "In --dev mode the source tree must be mounted or symlinked before running install.sh."
    exit 1
  fi
else
  if [ ! -d "$FERRY_HOME" ]; then
    echo "Creating $FERRY_HOME"
    mkdir -p "$FERRY_HOME"
  fi

  # Clone or update repository
  if [ -d "$FERRY_HOME/.git" ]; then
    echo "Updating repository..."
    cd "$FERRY_HOME"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
  else
    echo "Cloning repository..."
    git clone --branch "$BRANCH" "$REPO_URL" "$FERRY_HOME"
  fi
fi

cd "$FERRY_HOME"

# Initialise configuration (idempotent — safe if .env already exists)
./scripts/init-config.sh

# Delegate all application-level bootstrapping
./scripts/bootstrap.sh


#!/usr/bin/env bash
set -euo pipefail

# setup-certs.sh — generate TLS certificates for local HTTPS
#
# If mkcert is available, generates a locally-trusted certificate.
# Otherwise, falls back to a self-signed certificate with a clear
# message explaining how to enable trusted local HTTPS later.
#
# Idempotent: if a certificate already exists and mkcert is not
# available (so no upgrade is possible), exits without regenerating.
# If mkcert becomes available later, re-running upgrades to trusted.
#
# Reads PUBLIC_URL from .env (defaults to https://localhost).
#
# Output: certs/<hostname>.pem, certs/<hostname>-key.pem

if [ -z "${PUBLIC_URL:-}" ] && [ -f .ferry-context ]; then
    PUBLIC_URL="$(sed -n 's/^FERRY_REACHABLE_URL=//p' .ferry-context 2>/dev/null || true)"
fi
PUBLIC_URL="${PUBLIC_URL:-$(sed -n 's/^PUBLIC_URL=//p' .env 2>/dev/null || true)}"
PUBLIC_URL="${PUBLIC_URL:-https://localhost}"

HOSTNAME="${PUBLIC_URL#https://}"
HOSTNAME="${HOSTNAME#http://}"
HOSTNAME="${HOSTNAME%:*}"

if [ -f "certs/${HOSTNAME}.pem" ]; then
  if command -v mkcert &>/dev/null; then
    echo "Upgrading to trusted certificate for ${HOSTNAME}..."
    mkcert -install
    mkcert \
      -cert-file "certs/${HOSTNAME}.pem" \
      -key-file "certs/${HOSTNAME}-key.pem" \
      "$HOSTNAME" 2>/dev/null
    echo "Trusted certificate: certs/${HOSTNAME}.pem"
  else
    echo "Certificate already exists for ${HOSTNAME}."
    echo "Install mkcert to upgrade to a trusted certificate."
  fi
  exit 0
fi

if command -v mkcert &>/dev/null; then
  echo "Generating trusted certificate for: ${HOSTNAME}"
  mkcert -install
  mkdir -p certs
  mkcert \
    -cert-file "certs/${HOSTNAME}.pem" \
    -key-file "certs/${HOSTNAME}-key.pem" \
    "$HOSTNAME"
  echo "Trusted certificate generated: certs/${HOSTNAME}.pem"
else
  echo ""
  echo "mkcert was not found."
  echo ""
  echo "Continuing with a self-signed certificate."
  echo ""
  echo "Your browser will display a certificate warning when"
  echo "connecting to:"
  echo ""
  echo "    ${PUBLIC_URL}"
  echo ""
  echo "To enable trusted local HTTPS:"
  echo ""
  echo "    brew install mkcert"
  echo ""
  echo "Then run:"
  echo ""
  echo "    make certs"
  echo ""
  mkdir -p certs
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "certs/${HOSTNAME}-key.pem" \
    -out "certs/${HOSTNAME}.pem" \
    -subj "/CN=${HOSTNAME}" 2>/dev/null
  echo "Self-signed certificate generated: certs/${HOSTNAME}.pem"
fi

#!/usr/bin/env bash
set -euo pipefail

# prepare-env.sh — materialise runtime environment from execution context
#
# Reads .ferry-context and generates .ferry-compose.env for
# Docker Compose variable substitution.  Run before any compose
# invocation that needs runtime variables.
#
# This is a materialisation step, not a configuration source.
# The generated file should never be edited manually.
#
# Usage: ./scripts/prepare-env.sh

OUTPUT=".ferry-compose.env"

# Start fresh
: > "$OUTPUT"

if [ -f .ferry-context ]; then
    reachable="$(sed -n 's/^FERRY_REACHABLE_URL=//p' .ferry-context 2>/dev/null || true)"
    if [ -n "$reachable" ]; then
        host="${reachable#https://}"
        host="${host#http://}"
        host="${host%%:*}"
        echo "PUBLIC_URL_HOST=$host" >> "$OUTPUT"
    fi
fi

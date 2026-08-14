#!/usr/bin/env bash
set -euo pipefail

# platform.sh — execution-environment abstraction for FERRY
#
# Reads .ferry-context to determine the execution target, then
# dispatches platform operations to the appropriate backend.
#
# Usage: ./scripts/platform.sh <command> [args...]
#
# Commands:
#   compose <args>    Run docker compose on the platform host
#   exec <svc> <cmd>  Run a command in a container (non-TTY)
#   logs [args]       Tail compose logs
#   shell             Interactive session on the platform host
#   restart <svc>     Restart a compose service
#   run <script>      Execute a script from the repo on the platform host
#   cp <src> <dst>    Copy files to/from the platform host

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load execution context.  An explicit FERRY_TARGET environment
# variable takes precedence — this supports make uninstall TARGET=...
# when the execution context is missing or stale.
if [ -z "${FERRY_TARGET:-}" ] && [ -f "$REPO_ROOT/.ferry-context" ]; then
    . "$REPO_ROOT/.ferry-context"
fi
FERRY_TARGET="${FERRY_TARGET:-native}"

# — helpers -----------------------------------------------------------------------

_q() {
    printf '%q ' "$@"
}

# _run <shell-command-string>
#   Execute an arbitrary shell command on the platform host.
_run() {
    case "$FERRY_TARGET" in
        native)
            cd "$REPO_ROOT" && eval "$*"
            ;;
        orbstack)
            VM_DIR="${FERRY_VM_DIR:-/opt/ferry}"
            ssh -q root@ferry@orb "cd $VM_DIR && $*"
            ;;
        multipass)
            VM_DIR="${FERRY_VM_DIR:-/opt/ferry}"
            FERRY_VM="${FERRY_VM:-ferry}"
            multipass exec "$FERRY_VM" -- sudo -u ferry bash -c "cd $VM_DIR && $*"
            ;;
        remote)
            local host="${FERRY_HOST:?FERRY_HOST not set}"
            local user="${FERRY_USER:-ferry}"
            local dir="${FERRY_DIR:-/opt/ferry}"
            ssh -q "$user@$host" "cd $dir && $*"
            ;;
        *)
            echo "Unknown FERRY_TARGET: $FERRY_TARGET" >&2
            exit 1
            ;;
    esac
}

# _compose <args...>
#   Run docker compose on the platform host.
#   Materialises the runtime environment from execution context
#   before every invocation so that variables like PUBLIC_URL_HOST
#   are available regardless of how services were started.
_compose() {
    "$SCRIPT_DIR/prepare-env.sh" 2>/dev/null || true
    _run "docker compose --env-file ./.env --env-file ./.ferry-compose.env $(_q "$@")"
}

# — subcommands -------------------------------------------------------------------

case "${1:-help}" in
    compose)
        shift
        _compose "$@"
        ;;

    start)
        case "$FERRY_TARGET" in
            native|remote)
                echo "No VM to start for $FERRY_TARGET target."
                ;;
            orbstack)
                "$SCRIPT_DIR/orbstack.sh" start
                ;;
            multipass)
                "$SCRIPT_DIR/multipass.sh" start
                ;;
            *)
                echo "Don't know how to start $FERRY_TARGET environment." >&2
                exit 1
                ;;
        esac
        ;;

    exec)
        shift
        _compose exec -T "$@"
        ;;

    logs)
        shift
        _compose logs "$@"
        ;;

    shell)
        case "$FERRY_TARGET" in
            native)
                echo "Already on the platform host." >&2
                exec "${SHELL:-/bin/sh}"
                ;;
            orbstack)
                exec ssh -q root@ferry@orb
                ;;
            multipass)
                FERRY_VM="${FERRY_VM:-ferry}"
                exec multipass exec "$FERRY_VM" -- sudo -u ferry -s
                ;;
            remote)
                local host="${FERRY_HOST:?FERRY_HOST not set}"
                local user="${FERRY_USER:-ferry}"
                exec ssh -q "$user@$host"
                ;;
        esac
        ;;

    destroy)
        case "$FERRY_TARGET" in
            native|remote)
                echo "No environment teardown required for $FERRY_TARGET target."
                ;;
            orbstack)
                echo "Deleting OrbStack VM (ferry)..."
                "$SCRIPT_DIR/orbstack.sh" delete
                ;;
            multipass)
                echo "Deleting Multipass VM (ferry)..."
                "$SCRIPT_DIR/multipass.sh" delete
                ;;
            *)
                echo "Don't know how to destroy $(FERRY_TARGET) environment." >&2
                exit 1
                ;;
        esac
        ;;

    restart)
        shift
        _compose restart "$@"
        ;;

    run)
        shift
        _run "bash $*"
        ;;

    cp)
        shift
        case "$FERRY_TARGET" in
            native)
                cp "$@"
                ;;
            orbstack)
                # The repo is symlinked at /opt/ferry inside the VM,
                # so files are already shared. This subcommand is a no-op
                # for OrbStack; use scp if cross-VM copies are needed.
                echo "Files are shared via the mounted repo. Use scp for explicit copies." >&2
                ;;
            multipass)
                # The repo is mounted at /opt/ferry inside the VM,
                # so files are already shared. This subcommand is a no-op
                # for Multipass; use multipass transfer for explicit copies.
                echo "Files are shared via the mounted repo. Use multipass transfer for explicit copies." >&2
                ;;
            remote)
                local host="${FERRY_HOST:?FERRY_HOST not set}"
                local user="${FERRY_USER:-ferry}"
                scp "$user@$host:$1" "${2:-.}" 2>/dev/null || \
                scp "$1" "$user@$host:${2:-.}"
                ;;
        esac
        ;;

    help|*)
        echo "Usage: $0 <command> [args...]"
        echo ""
        echo "Commands:"
        echo "  compose <args>    Run docker compose on the platform host"
        echo "  destroy           Teardown the execution environment (VM, etc.)"
        echo "  start             Start the execution environment (VM, etc.)"
        echo "  exec <svc> <cmd>  Run a command in a container (non-TTY)"
        echo "  logs [args]       Tail container logs"
        echo "  shell             Interactive session on the platform host"
        echo "  restart <svc>     Restart a compose service"
        echo "  run <script>      Execute a script on the platform host"
        echo "  cp <src> <dst>    Copy files to/from the platform host"
        ;;
esac

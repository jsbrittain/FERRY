#!/usr/bin/env bash
set -euo pipefail

# multipass.sh — Multipass VM helper for FERRY
#
# Provides VM lifecycle operations through the same interface as
# orbstack.sh, enabling the platform.sh abstraction layer to manage
# a Multipass-backed execution environment.

MACHINE="ferry"
CLOUD_INIT="vm/cloud-init.yaml"

# VM resource defaults — overridable via environment variables.
# The platform runs Docker Engine, PostgreSQL, Redis, backend,
# frontend, worker, Caddy, BuildKit, and optionally Ollama
# simultaneously.  These defaults provide comfortable headroom
# for the full stack plus Docker image builds.
# 60G disk accommodates the Docker image cache plus the Ollama
# model (~4GB) with room to spare.
MULTIPASS_CPUS="${MULTIPASS_CPUS:-2}"
MULTIPASS_MEMORY="${MULTIPASS_MEMORY:-4G}"
MULTIPASS_DISK="${MULTIPASS_DISK:-60G}"

# Validate that the required runtime is available before any operation.
if ! command -v multipass &>/dev/null; then
    echo "ERROR: multipass is not installed." >&2
    echo "Install it from https://multipass.run or via your package manager." >&2
    exit 1
fi

case "${1:-help}" in
  create)
    shift
    if multipass info "$MACHINE" >/dev/null 2>&1; then
      echo "ERROR: An FERRY VM named \"$MACHINE\" already exists." >&2
      echo "" >&2
      echo "make install provisions a new platform into a fresh execution" >&2
      echo "environment.  If you intended to reinstall FERRY, first run:" >&2
      echo "" >&2
      echo "    make uninstall" >&2
      echo "" >&2
      echo "and then rerun:" >&2
      echo "" >&2
      echo "    make install" >&2
      exit 1
    else
      echo "Launching FERRY VM \"$MACHINE\" (Ubuntu 24.04, ${MULTIPASS_CPUS} CPU, ${MULTIPASS_MEMORY} RAM, ${MULTIPASS_DISK} disk)..."
      if ! multipass launch --cpus "$MULTIPASS_CPUS" --memory "$MULTIPASS_MEMORY" --disk "$MULTIPASS_DISK" --cloud-init "$CLOUD_INIT" 24.04 --name "$MACHINE" "$@"; then
        # Launch may time out while cloud-init provisions the VM.
        # Check whether the VM exists before deciding how to handle this.
        if ! multipass info "$MACHINE" >/dev/null 2>&1; then
          echo "ERROR: Failed to create VM $MACHINE." >&2
          exit 1
        fi
        echo "VM $MACHINE was created."
      fi
    fi
    echo "Waiting for cloud-init to complete..."
    echo "  (Installing Docker Engine, configuring firewall, creating directories)"
    # Cloud-init may report status: error for transient issues
    # (e.g., network blips during package downloads) that do not
    # affect platform operation.  The readiness gate is whether
    # the services FERRY depends on are actually available.
    # Use || rc=$? to capture the exit code without triggering
    # set -e, which would otherwise abort before we can inspect it.
    rc=0
    multipass exec "$MACHINE" -- cloud-init status --wait || rc=$?
    if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
        echo "cloud-init completed with warnings (exit $rc)."
    fi
    echo "Cloud-init finished."
    echo "Verifying Docker is available..."
    # Host-side redirection of multipass exec can hang when the
    # command produces output.  Redirect stdout/stderr inside the
    # guest to avoid this behaviour.
    multipass exec "$MACHINE" -- sh -c 'sudo -u ferry docker info >/dev/null 2>&1'
    echo "Docker Engine is running."
    echo "VM $MACHINE ready."
    ;;
  mount)
    # Native mount (9p/virtio) provides a live shared filesystem suitable
    # for development. Unlike the default SSHFS mount on macOS, native
    # mounts support full file read/write access.
    # Requires the VM to be stopped, then started after mounting.
    multipass umount "$MACHINE:/opt/ferry" 2>/dev/null || true
    multipass stop "$MACHINE" 2>/dev/null || true
    multipass mount -t native "$(pwd)" "$MACHINE:/opt/ferry"
    multipass start "$MACHINE"
    echo "Waiting for cloud-init to complete after restart..."
    # Cloud-init may report warnings after a restart — the readiness
    # gate is whether Docker is actually available.
    # Use || rc=$? to capture the exit code without triggering
    # set -e, which would otherwise abort before we can inspect it.
    rc=0
    multipass exec "$MACHINE" -- cloud-init status --wait || rc=$?
    if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
        echo "cloud-init completed with warnings (exit $rc)."
    fi
    echo "Cloud-init finished."
    echo "Verifying Docker is available..."
    # Host-side redirection of multipass exec can hang when the
    # command produces output.  Redirect stdout/stderr inside the
    # guest to avoid this behaviour.
    multipass exec "$MACHINE" -- sh -c 'sudo -u ferry docker info >/dev/null 2>&1'
    echo "Docker Engine is running."
    echo "Mounted $(pwd) at /opt/ferry (native 9p)"
    ;;
  start)
    shift
    echo "Starting VM $MACHINE..."
    multipass start "$MACHINE"
    echo "Waiting for cloud-init to complete..."
    rc=0
    multipass exec "$MACHINE" -- cloud-init status --wait || rc=$?
    if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
        echo "cloud-init completed with warnings (exit $rc)."
    fi
    echo "Cloud-init finished."
    echo "Verifying Docker is available..."
    multipass exec "$MACHINE" -- sh -c 'sudo -u ferry docker info >/dev/null 2>&1'
    echo "Docker Engine is running."
    echo "VM $MACHINE ready."
    ;;

  exec)
    shift
    multipass exec "$MACHINE" -- sudo -u ferry "$@"
    ;;
  shell)
    exec multipass exec "$MACHINE" -- sudo -u ferry -s
    ;;
  ip)
    multipass info "$MACHINE" --format json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['$MACHINE']['ipv4'][0])"
    ;;
  delete)
    echo "Deleting VM $MACHINE..."
    multipass delete --purge "$MACHINE"
    ;;
  help|*)
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  create           Create the installation VM"
    echo "  delete           Delete the installation VM
  start            Start the installation VM"
    echo "  mount            Mount repo into /opt/ferry (native 9p)"
    echo "  exec <cmd>       Run command inside the VM (as ferry user)"
    echo "  shell            Interactive shell inside the VM (as ferry user)"
    echo "  ip               Show VM IP address"
    ;;
esac

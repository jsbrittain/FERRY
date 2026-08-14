#!/usr/bin/env bash
set -euo pipefail

MACHINE="ferry"
CLOUD_INIT="vm/cloud-init.yaml"

# Validate that the required runtime is available before any operation.
if ! command -v orbctl &>/dev/null; then
    echo "ERROR: orbctl (OrbStack) is not installed." >&2
    echo "Install it from https://orbstack.dev." >&2
    exit 1
fi

case "${1:-help}" in
  create)
    shift
    if orbctl info "$MACHINE" >/dev/null 2>&1; then
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
        echo "Launching FERRY VM \"$MACHINE\" (Ubuntu 24.04)..."
        orbctl create --user-data "$CLOUD_INIT" ubuntu:24.04 "$MACHINE" "$@"
    fi
    echo "Waiting for cloud-init provisioning to complete..."
    echo "  (Installing Docker Engine, configuring firewall, creating directories)"
    # Cloud-init may report status: error for transient issues
    # (e.g., network blips during package downloads) that do not
    # affect platform operation.  The readiness gate is whether
    # the services FERRY depends on are actually available.
    # Use || rc=$? to capture the exit code without triggering
    # set -e, which would otherwise abort before we can inspect it.
    rc=0
    ssh root@"$MACHINE"@orb "cloud-init status --wait" || rc=$?
    if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then
        echo "cloud-init completed with warnings (exit $rc)."
    fi
    echo "Cloud-init finished."
    echo "Verifying Docker is available..."
    ssh root@"$MACHINE"@orb "docker info >/dev/null 2>&1"
    echo "Docker Engine is running."
    echo "VM $MACHINE ready."
    ;;
  mount)
    # OrbStack auto-shares the host filesystem.
    # Replace /opt/ferry (empty dir from cloud-init) with a symlink to the repo.
    ssh root@"$MACHINE"@orb "rm -rf /opt/ferry && ln -sfn $(pwd) /opt/ferry"
    echo "Mounted $(pwd) at /opt/ferry"
    ;;
  start)
    shift
    echo "Verifying OrbStack VM $MACHINE is running..."
    orbctl info "$MACHINE" >/dev/null 2>&1
    echo "VM $MACHINE is running."
    echo "Verifying Docker is available..."
    ssh root@"$MACHINE"@orb "docker info >/dev/null 2>&1"
    echo "Docker Engine is running."
    echo "VM $MACHINE ready."
    ;;

  ssh)
    shift
    ssh root@"$MACHINE"@orb "$@"
    ;;
  ip)
    orbctl info "$MACHINE" | grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' | head -1
    ;;
  delete)
    echo "Deleting VM $MACHINE..."
    orbctl delete --force "$MACHINE"
    ;;
  help|*)
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  create           Create the installation VM"
    echo "  delete           Delete the installation VM
  start            Verify the installation VM is running"
    echo "  mount            Symlink repo into /opt/ferry"
    echo "  ssh [cmd]        Run command in the VM (or start a shell)"
    echo "  ip               Show VM IP address"
    ;;
esac

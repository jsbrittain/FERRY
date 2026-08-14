# Backup & Recovery

Backing up and restoring FERRY institutional state.

## What constitutes an FERRY installation

An FERRY installation consists of several categories of state, each with
different backup requirements:

| Category | Example | Can be recreated? | Must be backed up? |
|----------|---------|-------------------|--------------------|
| Source code | Repository contents | Yes — from Git | No |
| Configuration | `.env` | Partially — secrets are unique | **Yes** |
| Database | Users, projects, bundles, audit events | No | **Yes** |
| Release packages | Delivered output ZIPs | Possibly — from source + data | **Yes** (compliance) |
| Bundle archives | Uploaded analysis files | Yes — re-uploaded by researchers | Optional |
| Execution images | Cached build artefacts | Yes — rebuilt on demand | No |
| Host data resources | Institutional datasets | N/A — managed by institution | Handled separately |
| Platform binary state | Redis queue, Docker build cache | Yes — ephemeral | No |
| Resource/EE manifests | YAML definitions in repository | Yes — from Git (re-registered on startup) | No |

The overall message is:

> The execution environment is disposable. Institutional state is not.

> **Important:** A backup stored on the same VM is not a disaster recovery
> strategy. If the VM is destroyed, the backup is destroyed with it. Always
> transfer backup archives to external or off-site storage immediately after
> creation.

## Backup responsibilities

The backup boundary follows the same architectural distinction used throughout
the platform.

### Platform-owned (included in the backup)

| State | Stored in | Backed up by |
|-------|-----------|--------------|
| PostgreSQL database | `pgdata` Docker volume | `backup.sh` — full `pg_dumpall` |
| Uploaded bundle archives | `/var/lib/ferry/bundles` | `backup.sh` — tarball |
| Execution outputs | `/var/lib/ferry/outputs` | `backup.sh` — tarball |
| Release packages | `/var/lib/ferry/releases` | `backup.sh` — tarball |
| Platform configuration | `.env` in repository root | `backup.sh` — file copy |

### Institution-owned (outside FERRY)

| State | Managed by | Backed up by |
|-------|------------|--------------|
| Institutional datasets | Institution's storage infrastructure | Institution's existing backup process |
| Execution environment base images | Institution's image registry | Institution's registry backup |
| Resource manifests | Git repository | Git hosting provider |
| Execution environment manifests | Git repository | Git hosting provider |

### Audit history

Audit events are stored in the `audit_events` table within the PostgreSQL
database. This means:

- Audit history is **automatically included** in every database backup.
- No separate audit log export or log file backup is required.
- When the database is restored, the full audit history is restored with it.

The audit trail covers all governance-significant actions: project creation,
bundle submission and review, execution requests, output releases, user
administration, and terms publication.

## Backup

### Automated backup

Run the backup script from the repository root:

```bash
./scripts/backup.sh
```

This creates a compressed archive containing:
- A full PostgreSQL dump (`pg_dumpall`) — all database state
- Application data files — bundle store, execution outputs, release packages
- Application configuration (`.env`)

The backup is saved to `/var/backups/ferry/` by default. Backups older
than 30 days are automatically removed.

### Transfer backup off the VM

After running the backup, copy the archive to external storage:

```bash
# From the VM, push to external storage
scp /var/backups/ferry/ferry_20250101_120000.tar.gz backup-server:/archive/

# Or pull from your workstation
scp ferry@vm-ip:/var/backups/ferry/ferry_20250101_120000.tar.gz ./
```

### What is backed up

#### 1. Configuration (`.env`)

The `.env` file contains secrets (database passwords, signing key, SMTP
credentials) that are generated during installation. If lost, these cannot be
recovered.

**Restore**: Place the backed-up `.env` in the repository root before starting
the platform. The same `SECRET_KEY` must be used so that existing session
cookies can be validated — sessions will expire naturally within their TTL if
the key changes.

#### 2. Database (PostgreSQL)

The database is the authoritative store for:
- User accounts and capabilities
- Projects and project membership
- Analysis bundles and their metadata
- Execution requests and validation requests
- Output sets and release package metadata
- Audit events
- Terms of service and acceptance records

This data **cannot be recreated** from any other source.

#### 3. Filesystem state

The following directories are captured in the backup tarball:

| Directory | Content | Criticality |
|-----------|---------|-------------|
| `/var/lib/ferry/bundles` | Uploaded analysis archives | Medium — researchers can re-upload |
| `/var/lib/ferry/outputs` | Execution output files | High — execution results |
| `/var/lib/ferry/releases` | Release package ZIPs | High — compliance records |

### What is not backed up

| Component | Reason |
|-----------|--------|
| Docker images (application + EE base) | Rebuildable from Dockerfiles |
| Cached build images | Rebuilt on demand by the worker |
| Resource manifests (`./resources/`) | Managed in Git repository |
| EE manifests (`./execution-environments/`) | Managed in Git repository |
| TLS certificates (`./certs/`) | Regenerated by `setup-certs.sh` |
| Execution context (`.ferry-context`) | Generated, disposable metadata |

## Restoring onto a new installation

Restoring FERRY after complete VM loss requires rebuilding the platform
and restoring state from backup. Restoring the platform is only half of the
process — you must also verify that institutional data mounts are available
before declaring recovery complete.

### Prerequisites

Before beginning, ensure you have:
- The latest backup archive stored off the failed VM
- Access to the Git repository for the platform code
- Access to the institutional data storage to be mounted

### Step-by-step recovery

#### Step 1 — Provision the new server

Set up a new VM following the [Deployment Guide](deployment.md). Ensure the
host meets the minimum requirements and has Docker Engine and Docker Compose
installed.

#### Step 2 — Clone the repository

```bash
git clone <repository-url> /opt/ferry
cd /opt/ferry
```

#### Step 3 — Restore configuration

Place the backed-up `.env` into the repository root:

```bash
cp /path/to/backup/.env /opt/ferry/.env
```

Do not skip this step — a fresh `.env` with new secrets will invalidate all
existing session cookies and lose access to the database.

#### Step 4 — Configure institutional data mounts

Mount the institutional data resources at the paths expected by the deployment
configuration. This is the same process as the initial deployment — see the
[Data Resources](data-resources.md) guide and [Runtime
Specification](../../vm/runtime.md) for details.

If data mounts are not available at this point, make a note to verify them
during the recovery verification step below. The platform may start without
them, but analysis executions will fail.

#### Step 5 — Build and start services

```bash
./scripts/bootstrap.sh
```

This builds all Docker images, creates storage directories, and starts the
platform services. The platform will register execution environments and data
resources from the manifests in the repository.

#### Step 6 — Restore from backup

Run the restore script with the backup archive:

```bash
./scripts/restore.sh /path/to/ferry_20250101_120000.tar.gz
```

The restore script:
1. Stops all services
2. Restores `.env` from the backup if present in the archive
3. Starts PostgreSQL only
4. Restores the database from the SQL dump
5. Restores filesystem state (bundles, outputs, releases) from the tarball
6. Starts all services
7. Runs Alembic migrations
8. Runs health checks

#### Step 7 — Run migrations

The restore script runs `alembic upgrade head` automatically. If the
restoration was from an older backup into a newer version of the platform,
this ensures the schema is up to date.

## Recovery verification

After the platform is running, confirm that recovery is complete:

### Platform health

- [ ] `./scripts/healthcheck.sh` reports all services operational
- [ ] Administrator can log in at the platform URL
- [ ] The `.env` used is the restored copy (not a freshly generated one)

### Database state

- [ ] All expected users are present
- [ ] Projects and their memberships are intact
- [ ] Analysis bundles are visible with correct status
- [ ] Audit events from before the backup are present and correctly attributed
- [ ] New audit events can be generated (e.g., log in and perform an action)
- [ ] Terms of service records are present

### Institutional data

- [ ] Data resource mounts are accessible at `/read-only-data`
- [ ] Data resources are registered and `active` in the admin UI
- [ ] Execution environments are registered and `active` in the admin UI

### Operational verification

- [ ] A simple validation or execution completes successfully
- [ ] Release packages are accessible for download

## Host-managed resources

Institutional data resources live **outside** FERRY (see [Data
Resources](data-resources.md)). They are backed up through the institution's
existing storage infrastructure. FERRY's backup script does not include
them.

When restoring onto a new installation, ensure the host-managed data
directories are mounted at the same paths expected by the deployment
configuration. The platform will not fail to start without them, but analysis
executions that reference those resources will fail.

## Next steps

- [Deployment](deployment.md) — production setup
- [Configuration](configuration.md) — environment settings
- [Data Resources](data-resources.md) — understanding the data boundary

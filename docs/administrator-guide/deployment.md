# Deployment

Deploying FERRY for institutional use.

## Supported installation targets

### OrbStack VM (development and evaluation)

The default installation creates a dedicated Linux virtual machine via OrbStack. This is the recommended path for evaluation and local development because it provides a clean, isolated environment that mirrors production.

The VM contains:
- All FERRY services (frontend, backend, worker, PostgreSQL, Redis)
- Docker Engine for analysis container execution
- The resource registry (database index of registered assets)
- A well-known location for institutional data: `/read-only-data`

The OrbStack VM is a **development convenience**, not a production requirement. The same Docker Compose configuration works on any Linux host.

### Native Docker

For CI environments or when a VM is impractical, FERRY runs directly on the host:

```bash
make install TARGET=native
```

This uses the host's Docker Engine directly. All services run as regular containers.

### Production

For production deployment, FERRY runs on a Linux server with Docker Engine. The reference deployment uses:
- Docker Compose for service orchestration
- Caddy as the reverse proxy (TLS termination, security headers, request size limits)
- PostgreSQL for the application database
- Redis for cache and rate limiting
- Docker Engine for analysis container execution

Production deployment is not automated by `make install`. You will need to:

1. Provision a Linux server with Docker Engine 24+ and Docker Compose v2.
2. Clone the repository.
3. Configure `.env` with production values.
4. Set up TLS certificates for the public domain.
5. Configure the reverse proxy.
6. Run `docker compose up -d`.

The platform handles database migrations automatically on startup.

## Separation of concerns

FERRY distinguishes between two categories of runtime configuration:

### Application configuration (`.env`)

`.env` contains FERRY's own settings: secrets, database credentials, SMTP relay details, the public URL, and application-level toggles. This is the configuration that FERRY needs to run.

`.env` is preserved across installations. It is created once and updated manually when settings change.

### Execution context (`.ferry-context`)

The execution context describes the institutional environment in which FERRY operates — specifically, where authoritative data resources live on the host filesystem.

The context file tells FERRY:
- Which host directories contain institutional data
- How those directories should be mounted (read-only) into the platform VM
- What paths correspond to which resource aliases

The execution context is separate from `.env` because it is deployment-specific. A cloud deployment may mount NFS shares; an on-premise deployment may use local disk. The context file captures this topology without coupling it to application secrets.

This separation means:
- An operator can update the execution context without touching application secrets
- The `.env` can be backed up and restored independently of host storage configuration
- Different deployments (staging, production) can share the same `.env` values but different context files

## What the platform needs from the host

FERRY requires:

| Resource | Purpose |
|----------|---------|
| Docker Engine | Execute analysis containers |
| Persistent volume | PostgreSQL data directory |
| Persistent volume | Redis data directory |
| Persistent volume | Bundle store (uploaded analysis archives) |
| Persistent volume | Output store (execution results and release packages) |
| Host storage | Institutional data resources (read-only mount) |
| Network | SMTP relay access for email notifications |

All persistent data is managed through Docker volumes. The host paths for institutional data are configured through the deployment context, not through application configuration.

### Data resource provisioning

Data resources are registered from YAML manifests and served from a
well-known location. Provisioning a new data resource follows the
four-step workflow:

1. **Provision data** — using your institution's preferred storage approach
   (NFS, local disk, cloud object storage, etc.)
2. **Mount at `/read-only-data`** — make the data available at the platform's
   well-known location
3. **Register with FERRY** — scaffold the resource skeleton and register
   it through the platform
4. **Publish terms** — publish dataset terms through the admin UI (optional)

The [Data Resources guide](data-resources.md) covers the full workflow and
helper commands.

## Next steps

- [Configuration](configuration.md) — environment settings reference
- [Data Resources](data-resources.md) — managing institutional datasets
- [Backup & Recovery](backup-and-recovery.md) — protecting institutional state

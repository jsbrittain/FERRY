# Configuration

Configuring FERRY for your institution.

## The `.env` file

FERRY is configured through a single `.env` file at the repository root. It is created automatically during installation and preserved across re-installations.

### Required settings

| Variable | Description | Notes |
|----------|-------------|-------|
| `SECRET_KEY` | Application signing key | Minimum 32 characters. Generate with `openssl rand -base64 32`. Shared across all services. |
| `ADMIN_PASSWORD` | Administrator account password | Used only during initial seeding. Can be changed later through the admin UI. |
| `PUBLIC_URL` | Canonical external URL | Used in notification email links and browser redirects. Must include protocol and port if non-standard. |

### Public URL

`PUBLIC_URL` must be the address at which users reach FERRY in their browser. Examples:

| Deployment | `PUBLIC_URL` |
|------------|--------------|
| Local evaluation | `https://localhost` |
| Production (standard port) | `https://ferry.institution.edu` |
| Production (non-standard port) | `https://ferry.institution.edu:8443` |

This value is used in email notification links. If it is wrong, users will receive emails with unreachable links.

### Database credentials

| Variable | Generated | Purpose |
|----------|-----------|---------|
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password for the application user |
| `REDIS_PASSWORD` | Yes | Redis password for authentication |

These are generated automatically during installation. Regenerate them by deleting `.env` and re-installing.

### SMTP (email notifications)

Email notifications are optional. Without SMTP configuration, the platform functions normally but does not send responsibility-transfer notifications.

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | — | SMTP relay hostname |
| `SMTP_PORT` | 587 | SMTP relay port |
| `SMTP_USERNAME` | — | SMTP authentication username |
| `SMTP_PASSWORD` | — | SMTP authentication password |
| `SMTP_TLS` | `true` | Enable STARTTLS |
| `SMTP_FROM` | `noreply@example.org` | Notification sender address |
| `SMTP_FROM_NAME` | `FERRY` | Notification sender display name |

When configuring SMTP:

- Email is sent asynchronously via `BackgroundTasks` — it never blocks API responses.
- If the SMTP relay is unreachable, notification failures are logged but do not affect platform operation.

### HTTPS and certificates

FERRY requires HTTPS for secure session cookies. In development, trusted certificates are generated automatically using mkcert.

**Regenerate certificates:**

```bash
make certs
```

In production, configure TLS at the reverse proxy level. The Docker Compose deployment includes a Caddy reverse proxy that handles TLS termination. Configure your domain's DNS to point to the FERRY server, and Caddy will obtain Let's Encrypt certificates automatically.

### Security settings

| Variable | Default | Description |
|----------|---------|-------------|
| `session_ttl_seconds` | 86400 (24h) | Per-session time-to-live. Active sessions expire after this duration of inactivity. |
| `max_session_ttl_seconds` | 604800 (7d) | Absolute maximum session lifetime. Sessions are destroyed after this time regardless of activity. |
| `secure_cookie` | `false` | Set to `true` when deploying behind TLS. Ensures cookies are only transmitted over HTTPS. |
| `rate_limit_max_attempts` | 10 | Maximum failed login attempts within the rate limit window before the client is temporarily blocked. |
| `rate_limit_window_seconds` | 300 (5min) | Duration of the rate limit window. |

### Execution resource limits

| Variable | Default | Description |
|----------|---------|-------------|
| `execution_mem_limit` | `4g` | Maximum memory per analysis container |
| `execution_cpu_limit` | `2.0` | Maximum CPU cores per analysis container |
| `execution_pids_limit` | `256` | Maximum process count per analysis container |
| `max_output_size_mb` | `1024` | Maximum total output size before the execution is terminated |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level. Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |

Logs are written to stderr in a structured format with UTC timestamps. Module loggers for Alembic, SQLAlchemy engine, and Uvicorn default to `WARN` to reduce noise.

### AI assistance

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | URL of the Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.2` | AI model to use for analysis summaries |

AI-assisted review is controlled through the admin settings page (Admin → Settings → Enable AI-assisted bundle review), not by an environment variable.

The Ollama service runs behind a Docker Compose profile and must be started separately:

```bash
docker compose --profile ai up -d
```

See [AI Assistance](../architecture-and-reference/ai-assistance.md) for setup instructions and behaviour details.

### Manifest directories

| Variable | Default | Description |
|----------|---------|-------------|
| `RESOURCE_MANIFEST_DIR` | (deployment-specific) | Container-side path to data resource manifest directory |
| `HOST_RESOURCE_MANIFEST_DIR` | (deployment-specific) | Host-side equivalent for Docker-outside-of-Docker bind mounts |
| `ENVIRONMENT_MANIFEST_DIR` | (deployment-specific) | Container-side path to execution environment manifest directory |
| `AUTO_REGISTER_RESOURCES` | `true` | Automatically register resource manifests on startup. Set to `false` to require explicit `make register-resources` calls. |

In development, `RESOURCE_MANIFEST_DIR` points to `/resources` (mapped from
`./resources/` in the repository). `HOST_RESOURCE_MANIFEST_DIR` is the same
path on the host filesystem — used by the worker's Docker executor when
mounting resources into analysis containers.

In production, both should point to the same host directory:

```
RESOURCE_MANIFEST_DIR: /resources
HOST_RESOURCE_MANIFEST_DIR: /var/lib/ferry/resources
```

The `HOST_RESOURCE_MANIFEST_DIR` must match the path on the host running
Docker Engine, not the container-internal path.

## Next steps

- [Deployment](deployment.md) — production setup
- [Data Resources](data-resources.md) — managing data resource manifests
- [Backup & Recovery](backup-and-recovery.md) — protecting configuration

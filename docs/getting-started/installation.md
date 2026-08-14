# Installation

How to install FERRY for evaluation or production use.

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Git | any | Clone the repository |
| Multipass | latest | Linux VM for FERRY services (recommended on macOS) |
| OrbStack | latest | Alternative VM provider (macOS only) |
| Make | any | Convenience wrapper for installation commands |
| mkcert | latest | Trusted local HTTPS certificates |

[mkcert](https://github.com/FiloSottile/mkcert) is required only for local HTTPS. Install it before running `make install`:

```bash
brew install mkcert
```

No other host dependencies are required. Python, Node.js, PostgreSQL, and Redis all run inside the platform environment.

## Installation targets

FERRY supports two installation modes:

### Multipass VM (recommended on macOS)

The default installation mode. Creates a dedicated Linux virtual machine via Multipass, mounts the repository, and runs all services inside it. The VM provides a clean, isolated environment that mirrors a production deployment.

Prerequisites: [Multipass](https://multipass.run) must be installed.

```bash
make install
```

### OrbStack VM (alternative)

Uses OrbStack to create a Linux VM. Available on macOS only. Use this target when you prefer OrbStack over Multipass.

Prerequisites: [OrbStack](https://orbstack.dev) must be installed.

```bash
make install TARGET=orbstack
```

## The installation lifecycle

`make install` performs these steps:

1. **Create VM** — provisions the Linux VM if it does not already exist.
2. **Generate `.env`** — creates the configuration file with secure defaults if one does not exist. Existing `.env` is preserved across re-installation.
3. **Build images** — builds the Docker images for frontend, backend, worker, and supporting services.
4. **Start services** — starts all containers: reverse proxy, frontend, backend, PostgreSQL, Redis, worker.
5. **Apply migrations** — runs Alembic database migrations to bring the schema up to date.
6. **Seed institutional state** — registers execution environments and data resources from manifests, seeds the auth framework (roles, capabilities), and creates the administrator account.
7. **Health check** — verifies all services are operational.

After installation, the platform is running and accessible at `https://localhost`.

## Administrator credentials

The administrator account is created during installation with these defaults:

| Field | Value |
|-------|-------|
| Email | `admin@ferry.local` |
| Password | Stored in `.env` as `ADMIN_PASSWORD` |

The password is generated automatically and saved to `.env`. It is never displayed in the terminal. To retrieve it:

```bash
grep ADMIN_PASSWORD .env
```

For evaluation environments, you can create additional accounts:

```bash
make seed-demo
```

This creates three evaluation persona accounts (researcher, moderator, maintainer) and prints their credentials. See the [Quick Start](quick-start.md) for the guided tutorial.

## Configuration file

`.env` is created automatically at the repository root. It contains:

| Variable | Purpose | Generated |
|----------|---------|-----------|
| `ADMIN_PASSWORD` | Administrator account password | Yes, if not set |
| `POSTGRES_PASSWORD` | Database credential | Yes |
| `REDIS_PASSWORD` | Redis credential | Yes |
| `SECRET_KEY` | Application signing key (min 32 chars) | Yes, if not set |
| `PUBLIC_URL` | Canonical external URL | Default: `https://localhost` |
| `SMTP_HOST` | SMTP relay for email notifications | Optional |
| `SMTP_PORT` | SMTP port | Default: 587 |
| `SMTP_USER` | SMTP username | Optional |
| `SMTP_PASSWORD` | SMTP password | Optional |
| `SMTP_USE_TLS` | TLS for SMTP | Default: true |

To regenerate all secrets, delete `.env` and run `make install` again.

## Public URL

`PUBLIC_URL` is the canonical external URL for the FERRY installation. It is used in email notification links and browser-facing redirects.

For local evaluation, the default (`https://localhost`) works. For production deployments, set this to the institution's domain:

```
PUBLIC_URL=https://ferry.institution.edu
```

## Local HTTPS

FERRY requires HTTPS for secure cookie-based sessions. During local evaluation, trusted HTTPS certificates are generated automatically using mkcert.

To regenerate certificates:

```bash
make certs
```

This is also useful if certificates expire or if you need to trust them on a new machine.

## Uninstalling

To remove the local FERRY installation:

```bash
make uninstall
```

This stops the platform, deletes the VM (OrbStack, Multipass) or tears down Docker resources, and preserves the repository and `.env`. To fully reset:

```bash
rm .env
make uninstall
```

Then reinstall with `make install`.

## Next steps

- [Quick Start](quick-start.md) — guided tutorial through the institutional workflow
- [Configuration](../administrator-guide/configuration.md) — detailed configuration reference
- [Deployment](../administrator-guide/deployment.md) — production deployment guide

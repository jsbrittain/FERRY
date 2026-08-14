# FERRY
[![FERRY](https://github.com/kraemer-lab/FERRY/actions/workflows/ferry.yml/badge.svg)](https://github.com/kraemer-lab/FERRY/actions/workflows/ferry.yml) [![Documentation Status](https://readthedocs.org/projects/ferry/badge/?version=latest)](https://ferry.readthedocs.io/en/latest/?badge=latest)

Documentation: [ReadTheDocs](https://ferry.readthedocs.io/en/latest)

Secure remote analysis for sensitive epidemiological data.

FERRY is an institutional platform for secure execution of approved analyses against institution-managed Data Resources, governed by a two-stage human approval workflow. Sensitive data never leaves the host institution.

Researchers develop analyses locally using schema documentation and synthetic datasets, submit analysis bundles to FERRY, and receive approved outputs after execution within a secure environment.

**Move the computation to the data, not the data to the computation.**

---

## Quick Start

Install FERRY as an institutional platform.

**Requirements**: Git, a container runtime, Make, [mkcert](https://github.com/FiloSottile/mkcert).

No other host dependencies are required. Python, Node.js, and PostgreSQL all run inside the platform.

[mkcert](https://github.com/FiloSottile/mkcert) provides trusted local HTTPS certificates so that browsers do not show security warnings when accessing `https://localhost`. Install it before running `make install`:

```bash
brew install mkcert
```

### Installation

```bash
git clone https://github.com/kraemer-lab/FERRY.git

cd FERRY

make install
```

This creates your FERRY installation, generates trusted local HTTPS certificates, creates the administrator account, publishes institutional assets, and leaves the platform running.

On the first installation, `.env` is created automatically with secure defaults. The administrator password is stored as `ADMIN_PASSWORD` in this file and is never displayed in the terminal. Subsequent installations reuse the existing configuration.

The default installation uses OrbStack (macOS VM). To deploy with native Docker instead:

```bash
make install TARGET=native    # native Docker deployment
```

### Evaluation

```bash
make seed-demo
```

This creates evaluation accounts (researcher, moderator, maintainer) and prints a welcome message with credentials and next steps.

Once evaluation accounts are ready, follow the guided tutorial:

```
docs/getting-started/quick-start.md
```

---

## Configuration

The only user-facing configuration file is `.env`, created automatically by `make install`. It contains installation-specific settings:

- `ADMIN_PASSWORD` — the administrator account password (generated)
- `POSTGRES_PASSWORD` and `REDIS_PASSWORD` — database credentials (generated)
- `SECRET_KEY` — application signing key (generated)
- `PUBLIC_URL` — canonical external URL (default: `https://localhost`)
- Optional SMTP configuration for email notifications

To regenerate all secrets, delete `.env` and run `make install` again.

---

## Public lifecycle

| Command | Purpose |
|---------|---------|
| `make install` | Install FERRY (default: OrbStack; use `TARGET=native` for Docker-native deployment) |
| `make seed-demo` | Seed evaluation personas and print welcome message |
| `make dev` | Daily development workflow |
| `make uninstall` | Remove the local FERRY installation |

`make uninstall` stops the platform services, removes the installation environment, and preserves the repository and `.env`. To fully reset, delete `.env` before reinstalling.

---

## Development

After installation, `make dev` is the normal edit–build–run workflow for contributors. It rebuilds and restarts application services without reseeding users or institutional state.

```bash
make dev
```

See `vm/runtime.md` for the development environment reference.

---

## Where next?

| Document | Purpose |
|----------|---------|
| `docs/getting-started/quick-start.md` | Guided tutorial through the institutional workflow |
| `docs/architecture-and-reference/architecture.md` | System architecture and trust boundaries |
| `docs/architecture-and-reference/security.md` | Security model and threat analysis |
| `docs/architecture-and-reference/api.md` | API reference |
| `docs/architecture-and-reference/testing.md` | Testing strategy and test runner reference |
| `vm/runtime.md` | Deployment runtime specification |

---

## Features

* Secure user authentication
* Project-based access control
* Analysis job submission
* Human approval before execution
* Isolated container execution
* Human approval before output release
* Complete audit trail

## Repository Structure

The repository layout is primarily relevant for contributors and operators.

```
frontend/    Next.js application
backend/     FastAPI application
worker/      Python job executor
execution-environments/  Base images and execution contracts
scripts/     Orchestration scripts
docs/        Documentation (Getting Started, User Guides, Administrator Guide, Architecture & Reference)
examples/    Synthetic datasets, analysis templates, and environment definitions
vm/          Cloud-init configuration and runtime specification
resources/   Institutional resource publications
```

## Technology

* Frontend: Next.js + React + TypeScript
* Backend: FastAPI
* Database: PostgreSQL
* Queue: Redis
* Worker: Python
* Execution: Docker
* Authentication: Local Identity Provider (Argon2, server-side sessions)

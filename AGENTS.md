# AGENTS.md

## Project status — Milestone 24 (Explicit Lifecycle, Multipass Backend, Platform.sh Abstraction)

### Exists and functional

```
backend/         FastAPI: identity model (User, Role, Capability,
                 ProjectMembership), capability-based policy, SQLAlchemy,
                 Alembic, config, Local Identity Provider auth,
                 CLI seed-admin/seed-maintainer/seed-researcher/seed-demo/seed-terms,
                 bundle store, worker execution, Environment Builder subsystem,
                 auth framework seeder, user management API (create/list/get/users),
                 email validation, email notification service (SMTP),
                 responsibility-transfer notifications (bundle submitted,
                 output released),
                 terms of service model (TermsOfService, TermsAcceptance),
                 terms service (publish, accept, query), terms API routes,
                 platform terms enforcement (dependency-based),
                 dataset terms enforcement (resource attach, bundle submit),
                 audit event model (AuditEvent, AuditEventType), audit service,
                 audit query API,
                 ValidationRequest model, validation API, execution fingerprint,
                 representative dataset mounting
frontend/        Next.js + React + TypeScript: login, projects, admin pages,
                 user management UI, project members UI, audit log tab,
                 per-project and per-resource audit views,
                 responsibility-oriented homepage (role-based quick actions),
                 responsibility-oriented Projects list (filters by role),
                 platform terms interstitial (/terms), terms admin page,
                 dataset terms dialog during resource attach and bundle submit,
                 Bundle Workspace (bundle detail page with file management,
                 environment selection, resource declaration, validation run,
                 build status indicator),
                 validation result display, bundle consistency indicators,
                 persona-based UI (header shows institutional role)
execution-environments/      Execution Environment artefacts (base images, manifests,
                              execution contracts, acceptance test suites)
examples/        Example analyses, bundle templates, environment definitions,
                 resource publication manifests
vm/              cloud-init.yaml, Caddyfile (HTTPS, HSTS, compression,
                 security headers, request size limits), runtime spec
scripts/
  init-config.sh    Application configuration (.env, secrets)
  setup-certs.sh    TLS certificate generation
  bootstrap.sh      Platform bootstrap (build, start, health)
  install.sh        Full system installation
  upgrade.sh        Application upgrade
  backup.sh         Database backup
  restore.sh        Restore from backup
  healthcheck.sh    Service health verification
  platform.sh       Execution-environment abstraction layer
  orbstack.sh       OrbStack VM helpers
  multipass.sh      Multipass VM helpers
  seed-*.sh         Institutional seeding (admin, terms, personas, developer, demo)
  setup-ai.sh       AI deployment configuration
  setup-certs.sh    Certificate generation
docker-compose.yml  6 services + optional ollama (--profile ai),
                     internal + frontend + external networks,
                     email configuration (SMTP relay support)
frontend/e2e/
  acceptance/        4 persona acceptance tests (administrator, maintainer,
                      moderator, researcher)
  institution/       1 institutional acceptance test (canonical workflow)
  execution-environment-acceptance/
                     3 execution environment acceptance tests
                     (python-3.13, python-3.14, conda)
  helpers/           Shared auth, network, and environment helpers
tests/           Unit (375), integration (identity validation, user management,
                 project membership, audit, terms governance, validation),
                 smoke,
                 e2e (canonical workflow, custom build workflow, validation workflow)
docs/            Architecture (current state), security, API, vision, AI assistance,
                 testing
```

### Still needs creating

```
shared/          Shared schemas and types (not started)
```

### Intended architecture (from docs/)

```
frontend/    Next.js + React + TypeScript
backend/     FastAPI + SQLAlchemy + Alembic + PostgreSQL
worker/      Python job executor
shared/      Shared schemas and types across packages
execution-environments/  Execution Environment artefacts
examples/    Synthetic datasets and analysis templates
docs/        Architecture, security, API, roadmap, vision
```

Single monorepo. Do not add top-level directories without justification.

## Installation lifecycle

The installation lifecycle consists of four explicit phases, each with a single-responsibility script:

```
init-config.sh
        ↓
setup-certs.sh
        ↓
bootstrap.sh
        ↓
seed-*.sh
```

| Script | Responsibility | Runs on | Produces |
|--------|---------------|---------|----------|
| `init-config.sh` | Application configuration (`.env`, secrets) | Host | `.env` |
| `setup-certs.sh` | TLS certificates | Host | `certs/` |
| `bootstrap.sh` | Platform bootstrap (build, start, health) | VM / host | containers, images |
| `seed-*.sh` | Institutional state | VM / host | database records |

The Makefile orchestrates these phases. It does not implement them.

Each script is independently runnable and idempotent.

## Public Make interface

The Makefile is the supported administration interface. Public targets describe platform operations rather than execution details.

```text
make install       Full installation (target-specific)
make uninstall     Stop and remove the environment
make restart       Stop then start services; preserve state
make start         Start all services
make stop          Stop all services
make logs          Tail container logs
make shell         Interactive session on the platform host
make certs         Regenerate TLS certificates
make enable-ai     Enable AI assistance
make seed-demo     Seed evaluation personas
make dev           Restart + seed development data
make dev-drop-db   Drop and recreate database schema (development only; destructive)
make test          Run unit, integration, and smoke tests
```

The Makefile delegates all execution-backend-specific operations to `scripts/platform.sh`. Backend-specific logic is never added to public Make targets.

## Execution abstraction (`scripts/platform.sh`)

`platform.sh` translates platform operations into execution-backend-specific implementations.

It reads `.ferry-context` to determine the execution target:

```text
FERRY_TARGET    — one of: native, orbstack, multipass, remote
FERRY_VM        — VM name (orbstack, multipass)
FERRY_HOST      — remote hostname (remote)
FERRY_USER      — remote SSH user (remote)
FERRY_DIR       — remote directory (remote)
```

Supported commands:

| Command | Purpose |
|---------|---------|
| `compose <args>` | Run docker compose on the platform host |
| `exec <svc> <cmd>` | Run a command in a container |
| `logs [args]` | Tail container logs |
| `shell` | Interactive session on the platform host |
| `restart <svc>` | Restart a compose service |
| `run <script>` | Execute a script on the platform host (via `bash`) |
| `cp <src> <dst>` | Copy files to/from the platform host |
| `destroy` | Teardown the execution environment |

New execution backends are implemented by extending `platform.sh`, not by modifying public Make targets.

## Execution identity

Each execution backend selects its own orchestration identity. This is an implementation detail hidden behind `platform.sh`.

| Backend | Orchestration user | Mechanism |
|---------|-------------------|-----------|
| native | current host user | direct execution |
| orbstack | root | SSH as root |
| multipass | ferry | `sudo -u ferry` via `multipass exec` |
| remote | configured SSH user | SSH as user |

The rest of the platform must never assume a particular orchestration user. Scripts executed via `platform.sh run` run as the backend's orchestration user.

## Configuration ownership (`scripts/init-config.sh`)

`init-config.sh` owns application configuration:

- Creates `.env` from `.env.example` with generated secrets.
- Accepts initial configuration values through environment variables.
- Applies overrides only when creating a fresh `.env`.
- Existing `.env` files are never modified (administrator configuration is authoritative).

Supported overrides (passed as environment variables):

| Variable | Purpose |
|----------|---------|
| `PUBLIC_URL` | Canonical external URL for this installation |

Adding a new override is an explicit design decision — add an `_apply_override`

call inside `init-config.sh`.

## PUBLIC_URL

`PUBLIC_URL` is the canonical external address of an installation.

- Established during installation by `init-config.sh`.
- The default is `https://localhost`, which is correct for OrbStack and native Docker.
- Execution backends **never** silently mutate `PUBLIC_URL` in `.env`. Administrator configuration is authoritative.
- Used by the backend for user-facing links (email notifications).
- Derived at runtime by `bootstrap.sh` into `PUBLIC_URL_HOST` for Caddy configuration.

## URL resolution

Operator-facing components (certificate generation, bootstrap, health checks) resolve addresses through a hierarchy rather than reading `.env` directly:

```
$PUBLIC_URL env var              explicit override (any caller)
        ↓
FERRY_REACHABLE_URL         execution context (.ferry-context)
        ↓
PUBLIC_URL (.env)               application configuration
        ↓
https://localhost               platform default
```

`FERRY_REACHABLE_URL` is the address through which the current execution environment is externally reachable. It is:

- Backend-owned (set by the Makefile during installation).
- Stored in `.ferry-context` — generated, disposable, never application configuration.
- Used by: `setup-certs.sh`, `bootstrap.sh`, `healthcheck.sh` for operator-facing operations.
- Distinguished from `PUBLIC_URL`: `PUBLIC_URL` is administrator-owned application configuration; `FERRY_REACHABLE_URL` is backend-owned execution metadata.

For backends that produce a context (OrbStack, Multipass), operator components use the reachable URL from context. For backends that do not (native Docker, remote SSH), resolution falls through to `.env`'s `PUBLIC_URL`.

## Runtime materialisation

Docker Compose consumes runtime variables through a materialisation layer rather than reading execution metadata directly.

```
.ferry-context (execution metadata)          .env (application configuration)
        ↓                                                  │
prepare-env.sh (materialisation)                           │
        ↓                                                  │
.ferry-compose.env (runtime overrides)                 │
        ↓                                                  │
        └──────────────────┬───────────────────────────────┘
                           ▼
          docker compose --env-file ./.env \
                         --env-file ./.ferry-compose.env
```

`prepare-env.sh` reads `.ferry-context` and generates `.ferry-compose.env` with variables such as `PUBLIC_URL_HOST` for Docker Compose substitution. This file is:

- Generated automatically by `platform.sh compose` and `bootstrap.sh`.
- Never edited manually.
- Listed in `.gitignore`.
- Regenerated on every compose invocation.

The `PUBLIC_URL_HOST` variable is derived from `FERRY_REACHABLE_URL` at runtime and passed to the Caddy container so that TLS certificates match the address through which the platform is reachable.

### Security constraints (must preserve in implementation)

- Researchers never get direct dataset access
- All analysis executes through the Worker in isolated Docker containers
- Datasets mounted read-only in containers
- Two-stage approval: execution approval then output approval
- Never bypass the approval workflow
- Use `Storage` and `Executor` interfaces (not coupling directly to Docker)
- Only the optional AI service (Ollama) has outbound network access, and only for model downloads
- IdentityProvider abstraction for auth, internal PostgreSQL for authorisation
- **Capability-based authorisation**: policy checks `require_capability()`, not roles
- **Project Membership scoping**: access requires membership + capability
- Audit trail required for all actions
- Execution containers run with: `cap_drop=["ALL"]`, read-only rootfs, `no-new-privileges`,
  tmpfs for `/tmp` and `/output`, disabled networking, and configurable resource limits
  (`execution_mem_limit`, `execution_cpu_limit`, `execution_pids_limit`, `max_output_size_mb`)
- All archives (bundle uploads, container outputs) are treated as untrusted:
  symlinks rejected, path traversal blocked, decompression size limited

### Identity model

There are four independent concepts:

#### User

A User represents an authenticated person. Users may belong to zero or more Projects via ProjectMembership. Users possess a `role` (metadata / seeding hint) and a list of `capabilities` (authoritative).

#### Role

A Role is a descriptive label with a default capability template. Roles seed capabilities at user creation time. After that, capabilities become the source of truth — changing a role does **not** silently change existing users.

Four roles exist: `researcher`, `moderator`, `maintainer`, `admin`.

Roles and role–capability mappings are stored in the database (`roles`, `role_capabilities` tables) and seeded by `auth_framework_seeder.seed_auth_framework()`.

#### Capability

Capabilities are authoritative. The policy layer authorises capabilities, not roles.

Capability vocabulary (defined in `app.models.capability.Capability` enum):

| Capability | Purpose |
|------------|---------|
| `project.manage` | Create and manage projects |
| `project.members.manage` | Add/remove project members |
| `project.resources.manage` | Attach/detach data resources |
| `bundle.create` | Create and edit analysis bundles |
| `bundle.submit` | Submit bundles for review |
| `bundle.review` | Approve/reject/supersede bundles |
| `execution.run` | Request execution of approved bundles |
| `execution.read` | View execution requests and their status (admin) |
| `execution.cancel` | Cancel pending or running executions |
| `output.review` | Approve/reject output sets |
| `output.release` | Release output sets to researchers |
| `environment.manage` | Manage execution environments |
| `data.manage` | Manage data resources |
| `user.manage` | Manage user accounts (create, update, delete) |
| `user.read` | List and view user accounts (read-only) |
| `terms.manage` | Publish and manage terms of service |
| `settings.manage` | View and update platform settings |
| `audit.read` | Query the audit ledger |
| `validation.run` | Run validation against representative datasets |
| `build.customize` | Use Custom Build strategy for analysis bundles |
| `governance.self_regulate` | Bypass self-moderation prevention |

The `capabilities` table is materialised from the enum during seeding (the enum is authoritative). `UserCapability` records are copied from role templates at user creation and become independent thereafter.

#### Project Membership

ProjectMembership answers one question only: does this User participate in this Project?

- Membership is **scope**, not authorisation.
- No roles, capabilities, or permissions are stored on membership.
- The project creator becomes the first member automatically.
- Access requires: (1) membership in the project, (2) the required capability.

### Governance Provenance

Governance state is stored directly on governed entities (AnalysisBundle, OutputSet)
as explicit provenance, not inferred from audit history. The audit trail records
*that* a governance action occurred; the governed entity records the current
state and *why*.

Explicit provenance is added to a governed entity where it contributes state that
downstream behaviour depends on. At present:

- **Submission provenance** (`submitted_by_id`, `submitted_at`) — governance
  independence (self-moderation guard) checks who submitted.
- **Rejection provenance** (`rejection_reason`, `rejected_by_id`, `rejected_at`) —
  the rejection reason is part of the current governance state and must be
  visible to researchers without an audit join.
- **Execution provenance** (`requested_by` on ExecutionRequest) — truthfully
  records who initiated execution.

Approval currently introduces no additional domain state beyond the approval
event itself — no explanatory payload is needed, and no downstream behaviour
depends on knowing the approver without consulting the audit trail. The audit
record is therefore sufficient. If a future requirement demands querying "who
approved this entity" without an audit join, explicit approval provenance can
be added following the same pattern.

### Audit Event Model

Audit Events record institutional decisions and governance-significant outcomes.

- Immutable and append-only
- Attributable to an actor (authenticated user or seeded system user)
- Associated with a Project and a governed resource
- Accompanied by structured metadata

The model and service are defined in `app.models.audit_event` and `app.services.audit_service`.

### System Actors

Autonomous platform components are represented by seeded `User` records with well-known UUIDs.

These accounts have no password (`password_hash=""`) and cannot authenticate through the API. They exist solely as accountable actors referenced by Audit Events.

| Actor | UUID | Email | Role |
|---|---|---|---|
| System | `00000000-0000-0000-0000-000000000001` | `system@ferry.internal` | `maintainer` |
| Execution Worker | `00000000-0000-0000-0000-000000000002` | `execution_worker@ferry.internal` | `maintainer` |

A `role` value is required by the schema; `maintainer` is used as the closest semantic match to a platform operator. No capabilities are assigned — these are audit identities, not RBAC participants.

System users are seeded idempotently by `seed_auth_framework()` (`auth_framework_seeder._seed_system_users()`).

### Audit Query API

The audit ledger is exposed through a single read-only query endpoint:

```
GET /api/admin/audit-events
```

Supports filtering by: `project_id`, `actor_id`, `resource_type`, `resource_id`, `event_type`, `date_from`, `date_to`.

Supports pagination via `limit` (max 200) and `offset`, and ordering via `order` (`asc`/`desc`, default `desc`).

Returns actor details (display name, email) alongside each event via a join to the `users` table.

Access requires the `audit.read` capability.

Defined in `app.api.routes.admin` and `app.services.audit_service`.

### Audit Event Taxonomy

The canonical audit vocabulary for Milestone 17.

Audit Events record either:

- institutional decisions; or
- externally significant outcomes.

#### Project

Project events record the creation, membership, and resource allocation lifecycle. These are deliberate governance actions that establish the institutional scope of research.

- `project.created`
- `project.member.added`
- `project.member.removed`
- `project.resource.allocated`
- `project.resource.deallocated`

#### Bundle

Bundle events record the two-stage approval workflow for analysis code. Every transition is an institutional choice about what analysis is permitted to run.

- `bundle.created`
- `bundle.submitted`
- `bundle.approved`
- `bundle.rejected`
- `bundle.superseded`

#### Execution

Execution events record the externally significant outcomes of running approved analysis. The start, completion, and failure of an execution are visible consequences of earlier governance decisions — a human acts on these outcomes.

- `execution.requested`
- `execution.started`
- `execution.completed`
- `execution.failed`
- `execution.cancelled`

#### Output

Output events record the governance lifecycle of execution results, mirroring the two-stage approval pattern. The release of an output set is the terminal governance decision that makes results available to researchers.

- `output_set.created`
- `output_set.approved`
- `output_set.rejected`
- `output_set.released`

#### User Administration

User creation is an institutional act with security implications. User administration events are not project-scoped.

- `user.created`

#### Terms

Terms events record the publication of institutional governance documents and their acknowledgement by researchers. Publication events are not project-scoped.

- `platform_terms.published`
- `dataset_terms.published`
- `platform_terms.accepted`
- `dataset_terms.accepted`

#### Validation

Validation events record the outcome of operational verification runs against representative datasets. These are operational events only — validation does not participate in governance workflows.

- `validation.completed`
- `validation.failed`

### Policy layer

The policy layer (`app.auth.policy`) exposes three functions:

| Function | Purpose |
|----------|---------|
| `require_capability(user, capability)` | Raise `PolicyError` if user lacks the capability |
| `require_project_membership(db, user, project_id)` | Raise 404 if user is not a project member; returns the Project |
| `require_owner(user, resource)` | Raise `PolicyError` if user is not the resource owner/creator |

Policy is entirely capability-based. Roles are never consulted by the policy layer.

### Admin endpoint capability requirements (enforced server-side)

Every `/api/admin/*` endpoint enforces a capability check. The requirements are:

| Endpoint | Required Capability |
|---|---|
| `GET /admin/resources`, `GET /admin/resources/{id}` | `data.manage` |
| `GET /admin/execution-environments`, `GET /admin/execution-environments/{id}` | `environment.manage` |
| `GET /admin/bundles`, `GET /admin/bundles/{id}` | Tiered: `bundle.review` / `output.review` / `user.manage` |
| `GET /admin/execution-requests`, `GET /admin/execution-requests/{id}` | Tiered: `bundle.review` / `output.review` / `user.manage` |
| `GET /admin/output-sets`, `GET /admin/output-sets/{id}` | `output.review` |
| `GET /admin/execution-requests/{id}/outputs` | `output.review` |
| `GET /admin/outputs/{id}` | `output.review` |
| `GET /admin/users`, `GET /admin/users/{id}` | `user.manage` or `user.read` |
| `POST /admin/users`, `PUT /admin/users/{id}` | `user.manage` |
| `GET /admin/audit-events` | `audit.read` |
| `POST /admin/terms/platform` | `terms.manage` |
| `POST /admin/resources/{id}/terms/publish` | `terms.manage` |
| `GET /admin/terms/status` | `terms.manage` |
| `POST /admin/bundles/{id}/approve`, `/reject` | `bundle.review` |
| `POST /admin/bundles/{id}/supersede` | `bundle.review` (unless owner) |
| `POST /admin/output-sets/{id}/approve`, `/reject` | `output.review` |
| `POST /admin/output-sets/{id}/release` | `output.release` |

All project-scoped endpoints additionally enforce `require_project_membership` and appropriate capabilities (`project.manage`, `bundle.create`, `bundle.submit`, `execution.run`, `project.members.manage`, `project.resources.manage`).

### Database Migrations (Alembic)

Alembic is the single authoritative mechanism for database schema management.

**Migration workflow:**

- **SQLAlchemy models remain the source of truth** — models define the schema, Alembic generates migrations from them.
- The initial migration (`alembic/versions/`) represents the current schema and was generated from model metadata with schema comparison verification against the prior migration chain.
- All future schema changes require a new Alembic migration, never manual DDL or `create_all()`.

> **Migration history reset (Milestone 24.4):** The development migration chain was
> squashed to a single baseline. Existing local development databases created
> before this squash must be recreated. Run `make dev-drop-db` or `make install` to
> initialise a fresh database using the new baseline.

**Developer workflow for schema changes:**

1. Modify the SQLAlchemy model class.
2. Run `alembic revision --autogenerate -m "Description of change"` from `backend/`.
3. Review the generated migration file in `alembic/versions/`.
4. Run `alembic upgrade head` to apply it.
5. Verify with unit and integration tests.

**Startup behaviour:**

- On startup, the backend runs `alembic upgrade head` to ensure the database is at the current migration revision.
- If the database is empty, all migrations are applied (fresh install).
- If the database has tables but no `alembic_version` table (legacy `create_all`-generated schema), startup fails with a clear error. The operator must manually verify schema compatability and run `alembic stamp head`.

**Deployment expectations:**

- `upgrade.sh` and `restore.sh` run `alembic upgrade head` as part of their workflow.
- Docker Compose does not run migrations explicitly; the application handles them at startup via the lifespan.
- Always run `alembic upgrade head` before starting the application against a new database.

**Migration policy:**

During active development, the migration history is regularly squashed so that the repository contains a single migration representing the current schema.

Once a version is released, migrations become part of the supported upgrade path between released versions.

Migration history may be squashed again at a future major release when upgrades from earlier releases are no longer supported.

### Logging

Logging is configured centrally at startup via `app.core.logging.configure_logging()`.

- **Log level** is controlled by the `LOG_LEVEL` environment variable (default `INFO`). Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- **Format**: `%(asctime)s [%(levelname)s] %(name)s: %(message)s` with UTC timestamps.
- **Output**: stderr via Python's `StreamHandler` (compatible with container logging).
- **Module loggers**: Alembic, `asyncio`, SQLAlchemy engine, Uvicorn, and Uvicorn access logs default to `WARN` to reduce noise.

### Exception Handling

Three global exception handlers provide a safety net for unhandled exceptions:

| Exception | HTTP Status | Response Body |
|---|---|---|
| `PolicyError` | 403 | `{"detail": "Forbidden"}` |
| `ValueError` | 422 | `{"detail": "Invalid request."}` (logged at WARNING) |
| `Exception` (fallback) | 500 | `{"detail": "Internal Server Error"}` (logged at ERROR) |

These are fallback handlers. Route-specific error handling (404s, 401s, 422s from service-layer `ValueError` catch blocks) takes precedence. The global `ValueError` handler returns a generic message to avoid leaking internal implementation details. The global `Exception` handler ensures no unhandled exception leaks internal details to the client.

### Terms Governance

Versioned institutional Terms of Service with backend-authoritative enforcement.

#### Platform Terms

- Versioned Terms of Service governing platform access.
- Published by administrators via `POST /api/admin/terms/platform` (requires `terms.manage`).
- Presented immediately after authentication when the current version has not been accepted.
- Acceptance is mandatory before platform access is granted.
- Refusal or dismissal logs the user out.
- Acceptance is permanently recorded in `terms_acceptance` and audited as `platform_terms.accepted`.
- The publishing administrator is automatically recorded as having accepted (act of publication implies institutional understanding).

#### Dataset Terms

Each Data Resource may define its own versioned Terms of Service.

- Published by administrators via `POST /api/admin/resources/{id}/terms/publish` (requires `terms.manage`).
- Researchers must accept the latest version before: attaching the resource to a Project, or submitting an Analysis Bundle referencing that resource.
- Enforcement occurs at the API layer — resource attachment and bundle submission endpoints check acceptance before proceeding.
- If Dataset Terms are updated (new version published), researchers must accept the latest version before further use.

#### Models

`TermsOfService` (`terms_of_service` table): Immutable institutional artefact. Each row is a specific published version for a specific scope.

`TermsAcceptance` (`terms_acceptance` table): Immutable append-only record of a user accepting a specific terms version. Acceptance state is always derived from these records — never from mutable boolean flags.

#### Enforcement

- Platform terms: `require_platform_terms_accepted()` FastAPI dependency, applied at the router level on `projects`, `admin`, `environments` routers. No-op when no terms are published (upgrade-safe).
- Dataset terms: checked inline in `post_project_resources()` and `post_submit_bundle()` route handlers.

#### Audit Events

| Event | Trigger |
|---|---|
| `platform_terms.published` | Platform terms published |
| `dataset_terms.published` | Data resource terms published |
| `platform_terms.accepted` | User accepts platform terms |
| `dataset_terms.accepted` | User accepts dataset terms |

#### User-Facing API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/terms/platform/current` | Current platform terms |
| `POST` | `/api/terms/platform/accept` | Accept platform terms |
| `GET` | `/api/terms/resources/{id}/current` | Current resource terms |
| `POST` | `/api/terms/resources/{id}/accept` | Accept resource terms |
| `GET` | `/api/terms/status` | All terms acceptance status |
| `GET` | `/api/terms/check?resource_ids=...` | Check specific resources |

#### Seeding

`ferry seed-terms` publishes default platform terms (Markdown) for development environments. Idempotent — skips if terms already exist.

### Health Check

`GET /api/health` returns platform operational status:

```json
{"status": "ok", "database": "connected", "redis": "connected"}
```

- **`status`**: `"ok"` when all dependencies are healthy, `"degraded"` otherwise.
- **`database`**: `"connected"` or `"disconnected"` based on a live `SELECT 1` query.
- **`redis`**: `"connected"` or `"disconnected"` based on a `PING` command.
- No authentication required. No internal implementation details exposed.

### Request Logging

An HTTP middleware logs each request after completion:

- Method, path, response status code, and duration in milliseconds.
- Request bodies and query parameters are never logged (sensitive data).
- Logged at `INFO` level via the `ferry` logger.

### Domain model boundary

- **Institutional assets** (Data Resources, Execution Environments) are registered automatically via lifespan startup from YAML manifests.
- **Researcher artefacts** (Projects, Analysis Bundles, Execution Requests) are created by users through the application. Projects have members (ProjectMembership) in addition to the owner/creator.
- **Internal system artefacts** (AIBundleReview, BuildRequest, ExecutionImage, OutputSet) are created by background tasks and workers during platform operation.
- **Environment Builder subsystem** transforms Analysis Bundle dependency specifications into reusable Execution Images via curated Dockerfile templates. Builds are driven by `BuildRequest` work items processed by the worker alongside execution requests. `ExecutionImage` records serve as a content-addressable cache keyed by `(execution_environment_id, dependency_hash)`.
- **Auth framework** (capabilities, roles, role–capability mappings) is seeded by `auth_framework_seeder.seed_auth_framework()` on first use (idempotent).
- **Demo workspace** (optional) can be created by `seed-demo` CLI command — a development tool, not application startup logic.
- **Manifest directories** (`RESOURCE_MANIFEST_DIR`, `ENVIRONMENT_MANIFEST_DIR`) are deployment configuration, not application defaults. Docker Compose sets them for development; production points them elsewhere.

### Institutional Personas

FERRY defines four institutional personas, each with a distinct scope of responsibility. The persona is derived from the user's role and is surfaced in the UI (header, homepage quick actions, Projects list filtering).

| Persona | Role | Responsibilities |
|---------|------|------------------|
| **Researcher** | `researcher` | Create projects, create analysis bundles, run validation, submit for review, request execution |
| **Moderator** | `moderator` | All researcher capabilities plus: review and approve/reject bundles, review and approve/reject output sets |
| **Maintainer** | `maintainer` | All moderator capabilities plus: release outputs, manage execution environments, manage data resources, use Custom Build |
| **Administrator** | `admin` | All capabilities including: user management, terms management, full audit access |

The persona is a UI concept derived from the role. The policy layer never consults personas or roles — it only checks capabilities.

#### Responsibility-Oriented UI

The homepage and navigation surface are organised around institutional responsibility rather than technical implementation details:

- **Homepage**: Shows role-based quick actions. A researcher sees "Create Project", "View Bundles"; an administrator sees "Manage Users", "Audit Log".
- **Projects list**: Filters by the user's role in each project. Researchers see projects they created or were added to; moderators see all projects with bundles pending review.
- **Header**: Displays the user's persona (derived from role) for self-identification.

### Runtime Capability Derivation

Capabilities are assigned at user creation time by copying from the role's capability template:

```python
for cap in role.default_capabilities:
    user_capabilities.append(UserCapability(user=user, capability=cap))
```

After creation, capabilities become independent of the role. Changing a user's role does **not** alter existing capabilities. An administrator must explicitly add or remove capabilities through the user management UI.

This design means:
- Role templates are a **seeding convenience**, not an authorisation mechanism.
- The `UserCapability` records in the database are the source of truth for what a user can do.
- An administrator can grant individual capabilities beyond the role template (e.g., giving a researcher `build.customize` for a specific project).

### Advanced Permissions

The `build.customize` capability is a separate, grantable permission that controls access to the Custom Build strategy. It is:

- Assigned to `maintainer` and `admin` roles by default.
- Grantable to individual users (including researchers) through the user management UI.
- Enforced at the API layer — users without it see only "Institutional Build" in the UI and receive a policy error if they attempt to submit a Custom Build bundle.

This pattern (a capability that is not part of the standard role template) establishes the model for future advanced permissions.

### Three Distinct Workflows

The platform supports three distinct execution workflows, each with different governance requirements:

#### 1. Validation Workflow

Researchers run advisory operational checks against representative datasets. No governance is involved — outputs are transient and researcher-visible only.

```
DRAFT bundle → Run Validation → Results displayed → (optional) Modify → Re-validate
```

#### 2. Build Workflow

Analysis Bundle dependency specifications are transformed into reusable Docker images. The build is driven by the declared Build Strategy (Institutional or Custom):

```
Bundle submitted → BuildRequest created → Worker builds image → ExecutionImage cached
```

The build is part of the submission-to-execution pipeline and is invisible to researchers.

#### 3. Governed Execution Workflow

Approved bundles execute against governed data resources in isolated containers. Outputs pass through two-stage human review before release.

```
Bundle approved → Execution requested → Worker executes → Output Set → Review → Release
```

### Notification Architecture

The platform sends responsibility-transfer email notifications to keep the right people informed at the right time. Notifications are triggered by governance actions, not by every data change.

#### Events

| Event | Recipients | Content |
|-------|------------|---------|
| `bundle.submitted` | Project members with `bundle.review` capability (excluding the submitter) | Project name, bundle name, submitter, review link |
| `output.released` | Execution requester and bundle creator (excluding the releaser) | Project name, bundle name, results link |

#### Design Principles

- **Recipient scoping**: Recipients are project members who possess the relevant capability. This avoids spamming unrelated users.
- **Self-exclusion**: The acting user never receives a notification about their own action.
- **Deduplication**: Duplicate recipients are collapsed into a single email.
- **Data minimisation**: Email bodies do not contain sensitive data, analysis code, or output files. They contain only metadata (names, links) sufficient to direct the recipient to the platform.
- **Asynchronous**: Notifications are sent via `BackgroundTasks` — they never block the API response.
- **Configurable**: SMTP settings (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS`) and the deployment domain (`PUBLIC_URL`) are configured through environment variables.

#### Implementation

- `app/services/email_service.py` — low-level SMTP sending
- `app/services/email_templates.py` — templated email bodies
- `app/services/notification_triggers.py` — trigger functions called from route handlers
- Requires no additional infrastructure beyond an SMTP relay

### Seeded development accounts

The following personas are seeded during `make install` (via `seed-institution.sh` and `seed-personas.sh`) and are available for manual validation:

| Persona | Email | Password | Role |
|---------|-------|----------|------|
| Administrator | `admin@ferry.local` | From `ADMIN_PASSWORD` in `.env` (generated) | admin |
| Maintainer | `maintainer@ferry.local` | `maintainer` | maintainer |
| Researcher | `researcher@ferry.local` | `researcher` | researcher |

All three are created idempotently — re-running bootstrap does not duplicate them.

### Developer commands

The standard development workflow:

```bash
make restart      # rebuild and restart development services (current backend)
make dev          # restart + seed development data (after schema reset)
make format       # auto-format code
make lint         # static analysis
make test         # run tests
```

**Backend** (from `backend/`):
- `pip install -e ".[dev]"` — install dependencies (including dev tools)
- `uvicorn app.main:app --reload` — dev server (applies pending Alembic migrations on startup)
- `python -m app.cli seed-admin` — seed admin user
- `python -m app.cli seed-maintainer` — seed maintainer user
- `python -m app.cli seed-researcher` — seed researcher user
- `python -m app.cli seed-terms` — seed default platform terms (dev debugging tool)
- `python -m app.cli seed-demo` — seed demo workspace (dev debugging tool)
- `alembic upgrade head` — apply pending migrations
- `alembic revision --autogenerate -m "description"` — generate a new migration from model changes

**Infrastructure** (from repo root):
- `./scripts/init-config.sh` — initialise application configuration (`.env`, secrets)
- `./scripts/setup-certs.sh` — generate TLS certificates
- `./scripts/bootstrap.sh` — platform boot only (build, start, wait, health)
- `./scripts/install.sh` — first-time install (clone repo + bootstrap)
- `./scripts/upgrade.sh` — application upgrade
- `./scripts/backup.sh` — database + data backup
- `./scripts/restore.sh <file>` — restore from backup
- `./scripts/healthcheck.sh` — verify services

**Makefile targets** (portable, delegates execution to `platform.sh`):
- `make deploy` — production install (SSH)
- `make install` — local installation (defaults to Multipass VM)
- `make start` — bring an existing installation online
- `make stop` — shut down gracefully
- `make upgrade` — run upgrade.sh
- `make backup` — run backup.sh
- `make restore FILE=<file>` — restore from backup

**Code quality** (from repo root):
- `make format` — auto-format code (ruff for Python)
- `make lint` — static analysis (ruff check)
- `make fix` — auto-fix all fixable issues (run this most often)

**Testing** (from repo root):
- `make test` — run the complete platform test suite.  Unit tests execute
  natively for speed.  Integration and smoke tests execute through the
  current execution backend so they always target the active platform.
  Execution-environment transparent (Native, OrbStack, Multipass, Remote).
- `make test-backend` — run full suite inside the backend container (useful
  for debugging without native Python setup).
- `make playwright` — run acceptance tests through Playwright.  The target
  URL is derived from the standard resolution hierarchy:
  `PLAYWRIGHT_BASE_URL > FERRY_REACHABLE_URL > PUBLIC_URL > https://localhost`
- `make playwright CMD=e2e/acceptance/researcher.spec.ts` — run researcher persona acceptance test
- `make playwright CMD=e2e/acceptance/administrator.spec.ts` — run administrator persona acceptance test
- `make playwright CMD=e2e/acceptance/moderator.spec.ts` — run moderator persona acceptance test
- `make playwright CMD=e2e/acceptance/maintainer.spec.ts` — run maintainer persona acceptance test
- `make playwright CMD=e2e/execution-environment-acceptance/python-3.14.spec.ts` — run python-3.14 EE acceptance test
- `make playwright CMD=e2e/execution-environment-acceptance/python-3.13.spec.ts` — run python-3.13 EE acceptance test
- `make playwright CMD=e2e/execution-environment-acceptance/conda.spec.ts` — run conda EE acceptance test
- `python -m pytest backend/tests/unit -v` — unit tests only (no database required)
- `python -m pytest backend/tests/integration -v` — integration tests (requires full stack running for non-native targets)
- `python -m pytest backend/tests/smoke -v` — smoke tests (requires full stack running)

### Authentication configuration

Key settings for deployment:

| Setting | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | (required) | Must be at least 32 characters. Generate with `openssl rand -base64 32`. |
| `session_ttl_seconds` | 86400 (24h) | Per-session time-to-live. |
| `max_session_ttl_seconds` | 604800 (7d) | Absolute maximum session lifetime (hard upper bound). |
| `secure_cookie` | False | Set `true` when deploying behind TLS. |
| `rate_limit_max_attempts` | 10 | Login attempts per window before rate limiting. |
| `rate_limit_window_seconds` | 300 (5min) | Rate limit window. |
The `seed-developer.sh` script (run by `make dev` and `make ci`) creates this database automatically.
For local native runs, create it manually:
```
createdb ferry_test
```

**CI** (from repo root, requires Docker):
- `make ci` — bootstrap full stack (build, start, seed)
- `make ci-clean` — tear down all Docker resources and remove `.env`
- `make playwright` — run canonical workflow e2e test (must be run after `make ci`)
- `make playwright CMD=e2e/custom-build-workflow.spec.ts` — run custom build workflow e2e test
- `make playwright CMD=e2e/validation-workflow.spec.ts` — run validation workflow e2e test

**Shared bootstrap** (from repo root, requires Docker):
- `make install` — canonical first-run installation (defaults to Multipass VM).
  Generates `.env` if missing, builds images, starts services, seeds admin.
  Safe to run multiple times.

**Makefile dev targets** (Multipass/OrbStack-specific, uses `scripts/platform.sh` under the hood):
- `make install` — first-run: create VM, mount repo, bootstrap, seed
- `make restart` — rebuild and restart code containers (backend, frontend, worker); preserves all state
- `make dev` — restart + re-seed development data (idempotent seeding, safe to run repeatedly)
- `make enable-ai` — enable AI assistance
- `make start` — bring an existing installation online (individual step)
- `make stop` — shut down gracefully (individual step)
- `make shell` — interactive VM shell (individual step)
- `make logs` — tail container logs (individual step)
- `make dev-destroy` — factory reset (remove containers, volumes, VM, .env)
- `make dev-drop-db` — reset database (all researcher artefacts dropped, schema recreated on next startup)
- `make build SVC=frontend` — rebuild and restart a single service (fastest iteration)

**VM / Dev environment** (see `vm/runtime.md`):
- `scripts/orbstack.sh` — OrbStack-specific helpers (create, mount, ssh, ip)
- `scripts/multipass.sh` — Multipass-specific helpers (create, mount, exec, shell, ip, delete)

### Acceptance Test Architecture

Milestone 23 introduces a three-tier acceptance test framework, organised under `frontend/e2e/`:

```
frontend/e2e/
├── acceptance/                    # Tier 1: Persona Acceptance
│   ├── administrator.spec.ts      Proves the admin can manage users, terms, etc.
│   ├── maintainer.spec.ts         Proves the maintainer can manage environments, release outputs
│   ├── moderator.spec.ts          Proves the moderator can review bundles and outputs
│   └── researcher.spec.ts         Proves the researcher can create projects, bundles, run analyses
├── institution/                   # Tier 2: Institutional Acceptance
│   └── canonical.spec.ts          Proves the full canonical workflow end-to-end
├── execution-environment-acceptance/  # Tier 3: Execution Environment Acceptance
│   ├── python-3.13.spec.ts        Proves python-3.13 honours its execution contract
│   ├── python-3.14.spec.ts        Proves python-3.14 honours its execution contract
│   └── conda.spec.ts              Proves the conda environment honours its execution contract
└── helpers/                       Shared test infrastructure
```

#### Tier 1 — Persona Acceptance

Each persona test validates that a specific institutional role can complete its assigned responsibilities through the UI. These tests do not re-validate the full pipeline — they prove capability boundaries are correctly enforced.

- **Administrator**: create users, publish terms, view audit log
- **Maintainer**: manage environments, create projects with custom builds, release outputs
- **Moderator**: review and approve/reject bundles and output sets
- **Researcher**: create projects, create bundles, run validation, submit for review

```bash
make playwright CMD=e2e/acceptance/researcher.spec.ts
make playwright CMD=e2e/acceptance/administrator.spec.ts
make playwright CMD=e2e/acceptance/moderator.spec.ts
make playwright CMD=e2e/acceptance/maintainer.spec.ts
```

#### Tier 2 — Institutional Acceptance

The institutional acceptance test (`frontend/e2e/institution/canonical.spec.ts`) proves the entire platform works as an institutional system. It exercises the complete canonical workflow:

1. Opening FERRY
2. Login with admin credentials
3. Publishing platform terms via the admin API
4. Creating a project
5. Attaching a data resource to the project
6. Creating an analysis and uploading a bundle
7. Submitting the bundle (DRAFT → SUBMITTED)
8. Approving the bundle (SUBMITTED → APPROVED_FOR_EXECUTION)
9. Running the analysis
10. Waiting for PENDING → RUNNING → COMPLETED status transition
11. Approving the Output Set (PENDING_REVIEW → APPROVED)
12. Releasing the Output Set (APPROVED → RELEASED), creating the Release Package ZIP
13. Downloading the Release Package
14. Verifying the ZIP contains the expected output file (`summary.csv`) and execution metadata (`execution_metadata.json`)
15. Verifying audit events are visible in the admin Audit Log for each governance action

This is a system test — not UI, not API — covering frontend, backend, database, worker, Docker executor, provider abstraction, runtime contract, output registration, download endpoint, and audit ledger.

```bash
make dev           # bootstrap the full stack (OrbStack VM)
make playwright    # run the institutional acceptance test
```

#### Tier 3 — Execution Environment Acceptance

Each execution environment acceptance test verifies that a published EE honours its execution contract. These tests validate that the environment can install declared dependencies, build a runnable execution image, and produce expected outputs under governed execution conditions. Institutional workflow (project provisioning, bundle creation, submission, approval, output release) is handled by helpers and is not under test here.

```bash
make playwright CMD=e2e/execution-environment-acceptance/python-3.14.spec.ts
make playwright CMD=e2e/execution-environment-acceptance/python-3.13.spec.ts
make playwright CMD=e2e/execution-environment-acceptance/conda.spec.ts
```

### Deployment user

Platform services (backend, worker) run as the non-root `ferry` user. The reference
deployment provisions matching ownership: `cloud-init.yaml` creates `/var/lib/ferry/`
owned by UID 1000, and `scripts/bootstrap.sh` applies the same ownership at setup time.
The container's `ferry` user uses a matching UID (1000) so that volume-mounted storage
directories are writable without runtime permission workarounds or world-writable fallbacks.

### Worker resilience

The worker (`worker/worker/main.py`) runs as a single-threaded infinite polling loop. Three resilience mechanisms are built in:

- **Database connection backoff**: On connection failure, the worker retries with exponential backoff (1s, 2s, 4s, ..., max 60s). Backoff resets to 1s on successful connection.
- **Outer catch-all**: Any unexpected exception during polling is logged with a full traceback; the loop continues.
- **Graceful shutdown**: `SIGTERM` and `SIGINT` are handled. The current iteration completes (including any in-flight build or execution), then the loop exits. In-flight containers are left for Docker to manage.

The worker polls `ValidationRequest` (PENDING) first, then `BuildRequest` (PENDING), then `ExecutionRequest` (PENDING), within each poll cycle.

### Future refactoring — Authentication flow

The frontend `request()` helper currently combines transport responsibilities
(HTTP requests, timeout handling, response parsing) with application navigation
(session-expiry redirect).

A future refactoring should move session-expiry handling into the authentication
layer (e.g. `AuthProvider` or a central authentication/session manager), leaving
`request()` responsible only for transport concerns.

At that point the API helper would report authentication failures, while the
authentication layer would decide whether to redirect, re-authenticate or present
an appropriate user experience. This would eliminate the need for route-specific
guards such as the current `/login` pathname check.

### Stack dependencies

Backend requires Python 3.11+. No other language runtimes or build tools have been installed. Stand up each package independently before wiring integration tests.

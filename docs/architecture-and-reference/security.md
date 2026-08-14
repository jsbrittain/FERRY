# Security Model

## Trust Boundary

Each institution deploys FERRY inside a restricted Linux virtual machine.

The VM contains:

* frontend
* backend
* database
* worker
* audit logs
* Docker Engine
* local datasets

Sensitive data never leaves this environment except through approved outputs.

---

## Execution

Each submitted analysis executes inside an ephemeral Docker container with:

* non-root user
* no external network access
* read-only dataset mounts
* temporary writable storage (`/work`, `/output`)
* configurable CPU, memory, and PIDs limits
* configurable execution timeouts
* container destroyed after completion
* no access to the host's full `/read-only-data` — only authorised subset

---

## Authentication

Authentication uses the **IdentityProvider** abstraction.

The first implementation (`LocalIdentityProvider`) provides:

* email/password authentication
* Argon2 password hashing
* server-side sessions backed by PostgreSQL
* HTTP-only secure cookies
* configurable session TTL and absolute maximum lifetime
* rate-limited login attempts (configurable window and threshold)

Additional identity providers may be implemented behind the same
abstraction without changing application code.

---

## Authorisation

Authorisation is **capability-based**, not role-based.

The policy layer (`app.auth.policy`) provides three functions:

| Function | Purpose |
|----------|---------|
| `require_capability(user, capability)` | Raise `PolicyError` if user lacks the capability |
| `require_project_membership(db, user, project_id)` | Raise 404 if user is not a project member |
| `require_owner(user, resource)` | Raise `PolicyError` if user is not the resource owner |

### Runtime Capability Derivation

Capabilities are assigned at user creation time by copying from the role's
capability template. After creation, capabilities become independent of the
role. Changing a user's role does **not** alter existing capabilities.

This means:

- Role templates are a **seeding convenience**, not an authorisation mechanism.
- The `UserCapability` records in the database are the source of truth.
- An administrator can grant individual capabilities beyond the role template
  (e.g., giving a researcher `build.customize` for a specific project).

### Advanced Permissions

The `build.customize` capability is a separately grantable permission that
controls access to the Custom Build strategy. It is:

- Assigned to `maintainer` and `admin` roles by default.
- Grantable to individual users through the user management UI.
- Enforced at the API layer — users without it see only "Institutional Build"
  in the UI and receive a policy error if they attempt to submit a Custom
  Build bundle.

### Capability Enforcement

Capabilities are authoritative. Roles seed capabilities at user creation
time, after which capabilities are independent. The policy layer never
consults roles.

For a task-oriented guide to user and capability management, see the
[Users & Roles](../administrator-guide/users-and-roles.md) administrator guide.

Project Membership is **scope only** — it answers "does this user
participate in this project?" without storing roles or capabilities.

Access requires both:
1. membership in the project
2. the relevant capability for the action

The capability vocabulary includes 21 capabilities defined in
`app.models.capability.Capability`:

`project.manage`, `project.members.manage`, `project.resources.manage`,
`bundle.create`, `bundle.submit`, `bundle.review`, `execution.run`,
`execution.read`, `execution.cancel`, `output.review`, `output.release`,
`environment.manage`, `data.manage`, `user.manage`, `user.read`,
`terms.manage`, `settings.manage`, `audit.read`, `validation.run`,
`build.customize`, `governance.self_regulate`

---

## Approval Workflow

The platform has a two-stage approval gate. Each gate governs a
different artefact and requires moderator (or above) review.

### Stage 1: Execution Approval

```
Researcher creates bundle → SUBMITTED
Moderator reviews → APPROVED_FOR_EXECUTION or REJECTED
```

Only bundles in `APPROVED_FOR_EXECUTION` status may be used to create
execution requests.

### Stage 2: Output Approval

```
Execution completes → Output Set PENDING_REVIEW
Moderator approves → APPROVED
Moderator releases → RELEASED (ZIP package created)
Researcher downloads ZIP
```

---

## Audit

All governance-significant actions are recorded in an append-only audit
ledger:

* user creation
* project creation and membership changes
* resource allocation and deallocation
* bundle lifecycle transitions (created, submitted, approved, rejected, superseded)
* execution lifecycle transitions (requested, started, completed, failed, cancelled)
* output set lifecycle transitions (created, approved, rejected, released)

Audit events are immutable, attributable to an authenticated actor
(or system user), associated with a project and governed resource, and
accompanied by structured metadata.

---

## Email Notifications

The platform sends responsibility-transfer email notifications triggered by
governance actions. These have specific security properties:

- **Recipient scoping**: Recipients are project members who possess the
  relevant capability. This prevents information disclosure to unrelated users.
- **Self-exclusion**: The acting user never receives a notification about
  their own action.
- **Deduplication**: Duplicate recipients are collapsed into a single email.
- **Data minimisation**: Email bodies contain only metadata (names, links)
  sufficient to direct the recipient to the platform. Analysis code, output
  files, and sensitive data are never included.
- **No sensitive data in transit**: Notification emails are sent via SMTP,
  which should be configured with TLS (`SMTP_USE_TLS=true`).
- **Authentication required**: The SMTP relay credentials are stored in
  environment variables and are never exposed through the application API.

---

## Container Hardening

Analysis containers are configured with:

* `cap_drop=["ALL"]` — no Linux capabilities
* read-only root filesystem
* `no-new-privileges` — prevents privilege escalation
* tmpfs for `/tmp` and `/output` (process-local, no persistence)
* disabled networking
* configurable resource limits (`execution_mem_limit`, `execution_cpu_limit`,
  `execution_pids_limit`, `max_output_size_mb`)
* `SecurityOpt=no-new-privileges:true`

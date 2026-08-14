# Users & Roles

Managing users, roles, and capabilities in FERRY.

## Overview

FERRY uses a **capability-based** authorisation model. Users are assigned a role at creation, which seeds their initial capabilities. After creation, capabilities become independent of the role — changing a user's role does **not** alter existing capabilities.

This design means:

- **Role templates are a seeding convenience**, not an authorisation mechanism. They determine what capabilities a new user starts with.
- **UserCapability records in the database are the source of truth** for what a user can do.
- **An administrator can grant individual capabilities beyond the role template** (for example, giving a researcher the `build.customize` capability without changing their role).

## Institutional personas

FERRY defines four personas, each mapped to a role with a distinct scope of responsibility:

| Persona | Role | Responsibilities |
|---------|------|------------------|
| **Researcher** | `researcher` | Create projects, create and edit analysis bundles, run validation, submit bundles for review, request execution of approved bundles, download released outputs |
| **Moderator** | `moderator` | All researcher capabilities plus: review and approve/reject bundles, review and approve/reject output sets |
| **Maintainer** | `maintainer` | All moderator capabilities plus: release outputs, manage execution environments, manage data resources, use Custom Build |
| **Administrator** | `admin` | All capabilities including: user management, terms management, full audit access |

The persona is surfaced in the UI (homepage quick actions, Projects list filtering, header) but the policy layer never consults roles — it checks capabilities only.

## Capability vocabulary

The platform defines the following capabilities:

| Capability | Purpose | Default roles |
|------------|---------|---------------|
| `project.manage` | Create and manage projects | Researcher, Moderator, Maintainer, Admin |
| `project.members.manage` | Add/remove project members | Maintainer, Admin |
| `project.resources.manage` | Attach/detach data resources | Maintainer, Admin |
| `bundle.create` | Create and edit analysis bundles | Researcher, Moderator, Maintainer, Admin |
| `bundle.submit` | Submit bundles for review | Researcher, Moderator, Maintainer, Admin |
| `bundle.review` | Approve/reject/supersede bundles | Moderator, Maintainer, Admin |
| `execution.run` | Request execution of approved bundles | Researcher, Moderator, Maintainer, Admin |
| `execution.read` | View execution requests and their status (admin) | Admin |
| `execution.cancel` | Cancel pending or running executions | Maintainer, Admin |
| `output.review` | Approve/reject output sets | Moderator, Maintainer, Admin |
| `output.release` | Release output sets to researchers | Maintainer, Admin |
| `environment.manage` | Manage execution environments | Maintainer, Admin |
| `data.manage` | Manage data resources | Maintainer, Admin |
| `user.manage` | Manage user accounts (create, update, delete) | Admin |
| `user.read` | List and view user accounts (read-only) | Maintainer, Admin |
| `terms.manage` | Publish and manage terms of service | Admin |
| `settings.manage` | View and update platform settings | Admin |
| `audit.read` | Query the audit ledger | Admin |
| `validation.run` | Run validation against representative datasets | Researcher, Moderator, Maintainer, Admin |
| `build.customize` | Use Custom Build strategy | Maintainer, Admin |
| `governance.self_regulate` | Bypass self-moderation prevention | (grantable via advanced capabilities) |

## Creating users

Users are created through the admin user management UI (requires `user.manage` capability).

To create a user, provide:
- Display name
- Email address
- Role (determines initial capabilities)
- Password

The user is created with capabilities copied from the role's template. If you later change the user's role, their capabilities remain unchanged — you must explicitly add or remove them.

## Managing capabilities post-creation

After a user is created, you can:
- **Add capabilities**: grant a capability the user does not currently have (for example, giving a researcher `build.customize`).
- **Remove capabilities**: revoke a capability from a user (for example, removing `project.members.manage` from a maintainer).

Capability changes take effect immediately. The next request the user makes will be evaluated against the updated capability set.

> Changing a user's role does **not** change their capabilities. Role changes update the display label only.

## Project membership

Project membership is separate from roles and capabilities. A user must be a member of a project to access it, regardless of their capabilities. Conversely, membership alone does not grant any authority — the user must also possess the relevant capability for the action they want to perform.

Members are added and removed by users with the `project.members.manage` capability.

## See also

- [Terms](terms.md) — platform and dataset terms management
- [Architecture](../architecture-and-reference/architecture.md) — identity model design and capability derivation
- [Security Model](../architecture-and-reference/security.md) — authorisation architecture

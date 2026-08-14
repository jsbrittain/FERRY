## Governance Overview

FERRY enforces institutional governance through capability-based access control, approval workflows, and a complete audit trail.

### Capability-Based Access

Every action in the platform requires a specific capability:

| Capability | Purpose |
|---|---|
| `project.manage` | Create and manage projects |
| `project.members.manage` | Add or remove project members |
| `project.resources.manage` | Attach or detach data resources |
| `bundle.create` | Create and edit Analysis Bundles |
| `bundle.submit` | Submit bundles for review |
| `bundle.review` | Approve, reject, or supersede bundles |
| `execution.run` | Request execution of approved bundles |
| `output.review` | Approve or reject output sets |
| `output.release` | Release approved outputs to researchers |
| `validation.run` | Run advisory validation against representative datasets |
| `environment.manage` | Manage execution environments |
| `data.manage` | Manage data resources |
| `user.manage` | Manage user accounts |
| `terms.manage` | Publish and manage terms of service |
| `build.customize` | Use Custom Build strategy for bundles |

Your account's capabilities depend on your role. Researchers typically have
`project.manage`, `bundle.create`, `bundle.submit`, `execution.run`, and
`validation.run`.

### Two-Stage Approval

All analyses pass through two independent approval stages:

1. **Bundle Approval** — A reviewer checks the analysis code before it can run.
2. **Output Approval** — A reviewer checks the results before they can be released.

This ensures no code executes and no data leaves without human oversight.

### Terms of Service

The institution publishes:

- **Platform Terms** — governing overall platform access.
- **Dataset Terms** — governing use of specific data resources.

You must accept the latest version of each before use.

### Audit Trail

Every governance action generates an audit event. Events are:

- Immutable and append-only
- Attributable to the authenticated user
- Project-scoped for privacy
- Visible in the Audit Log

### Institutional Publications

The institution publishes:

- [Execution Environments](/environments) — approved runtimes
- [Data Resources](/resources) — curated datasets
- [Example Analyses](/examples) — educational analysis code
- [Bundle Templates](/templates) — downloadable starting points

These publications are authoritative and maintained by the institution.

# Moderator Guide

Task-oriented documentation for moderators using FERRY.

## Who is a Moderator?

A moderator has all researcher capabilities plus the authority to review and approve or reject analysis bundles and output sets. Moderators serve as the human governance layer — they decide what analysis is permitted to execute and what results are permitted to leave the institution.

## Capabilities

All researcher capabilities, plus:
- **Bundle review**: approve, reject, or supersede submitted bundles
- **Output review**: approve or reject output sets pending release

Moderators cannot release outputs (that requires the `output.release` capability, held by maintainers and administrators).

## Reviewing bundles

When a researcher submits a bundle, it enters **SUBMITTED** status and becomes visible to moderators.

### Finding bundles to review

From the homepage, moderators see **Bundles Pending Review** as a quick action. The Projects list also surfaces projects with bundles awaiting review.

### The review process

1. Open the bundle from the review queue.
2. Inspect the bundle details:
   - **Execution environment** — which runtime will be used
   - **Data resources** — what data the analysis will access
   - **Entry point and arguments** — how the analysis is invoked
   - **Build strategy** — Institutional or Custom Build
   - **Uploaded files** — the analysis code
3. Review the validation results if the researcher ran validation.
4. Decide the outcome.

### Approving a bundle

Approval transitions the bundle to **APPROVED_FOR_EXECUTION** status. This authorises the researcher to create execution requests against it.

Approval means: *this analysis is appropriate to execute against governed data*.

### Rejecting a bundle

Rejection returns the bundle to the researcher. Provide a reason so the researcher can address the issue and resubmit.

### Superseding a bundle

When a researcher submits a new version of an already-approved bundle, the previous version can be **superseded**. This keeps the provenance chain intact — the old version is marked as SUPERSEDED rather than deleted.

## Reviewing output sets

When an execution completes, an Output Set is created in **PENDING_REVIEW** status. Researchers cannot access outputs at this stage — moderators must review them first.

### Finding output sets to review

From the homepage, moderators see **Output Sets Pending Review** as a quick action.

### The review process

1. Open the Output Set from the review queue.
2. Inspect individual output files and execution metadata through the admin interface.
3. Verify the outputs are appropriate for release.
4. Decide the outcome.

### Approving an output set

Approval transitions the Output Set to **APPROVED** status. This means: *these outputs are safe to release*. The outputs are still not visible to the researcher — a maintainer or administrator must perform the Release action.

### Rejecting an output set

Rejection returns the Output Set to **REJECTED** status. The researcher is notified that the outputs were not approved, and the execution may need to be repeated.

## Audit trail

All review actions are recorded in the audit ledger:

| Action | Audit event |
|--------|-------------|
| Bundle approved | `bundle.approved` |
| Bundle rejected | `bundle.rejected` |
| Bundle superseded | `bundle.superseded` |
| Output set approved | `output_set.approved` |
| Output set rejected | `output_set.rejected` |

Audit events include the actor (you), the governed resource, and a timestamp. They are immutable and append-only.

## See also

- [Researcher Guide](researcher.md) — how bundles and outputs look from the researcher side
- [Maintainer Guide](maintainer.md) — output release and beyond
- [Architecture](../architecture-and-reference/architecture.md) — governance lifecycle
- [Audit Events](../architecture-and-reference/architecture.md#output-set-governance) — audit event taxonomy

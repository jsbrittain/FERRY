# Terms

Managing platform and dataset terms of service.

## Overview

FERRY supports versioned institutional terms of service at two levels:

**Platform terms** govern access to the FERRY platform itself. All users must accept the current version before they can use the platform. If updated terms are published, users must accept the new version before continuing.

**Dataset terms** govern access to specific data resources. Researchers must accept the latest version before they can attach the resource to a project or submit a bundle that references it. If dataset terms are updated, researchers must accept the new version before further use.

Terms are **versioned institutional artefacts**. Each published version is immutable — it represents the exact text that was in effect at a particular time. Acceptance records are also immutable, providing a complete audit trail of who accepted what and when.

## Publishing platform terms

To publish platform terms:

1. Navigate to **Admin → Terms** in the UI.
2. Create the terms content (Markdown is supported).
3. **Publish**.

The publishing administrator is automatically recorded as having accepted the new version — the act of publication implies institutional understanding.

Publishing new platform terms:
- Creates an immutable `TermsOfService` record.
- Generates an audit event (`platform_terms.published`).
- Does **not** invalidate existing sessions immediately — users are prompted to accept on their next action.

If no platform terms have been published, the platform operates without terms enforcement. Publishing the first version activates the terms requirement for all users.

## Publishing dataset terms

To publish dataset terms for a specific data resource:

1. Navigate to **Admin → Data Resources** in the UI.
2. Select the resource.
3. Create the terms content (Markdown is supported).
4. **Publish**.

This creates a new version of the dataset terms for that resource. Previous versions remain accessible in the database for audit purposes.

## Acceptance workflow

When a user accesses the platform after terms are published:

1. The platform checks whether the user has accepted the current version.
2. If not, the user is redirected to the terms page.
3. The user reads the terms and clicks **Accept**.
4. The acceptance is permanently recorded (audit event: `platform_terms.accepted`).
5. The user proceeds to the platform.

The same workflow applies to dataset terms, triggered when the user attempts to attach a resource or submit a bundle referencing it.

## Audit trail

All terms actions are recorded in the audit ledger:

| Event | Trigger |
|-------|---------|
| `platform_terms.published` | Platform terms published |
| `dataset_terms.published` | Dataset terms published for a resource |
| `platform_terms.accepted` | User accepts platform terms |
| `dataset_terms.accepted` | User accepts dataset terms |

## See also

- [Users & Roles](users-and-roles.md) — user management
- [Data Resources](data-resources.md) — resource-specific terms
- [Architecture](../architecture-and-reference/architecture.md) — terms governance model

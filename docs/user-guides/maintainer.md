# Maintainer Guide

Task-oriented documentation for maintainers using FERRY.

## Who is a Maintainer?

A maintainer has all moderator capabilities plus the authority to release output sets, manage execution environments, manage data resources, and use the Custom Build strategy for analysis bundles.

Maintainers bridge the gap between institutional governance and platform operations. They can perform every action in the research lifecycle except user management and terms management (which require administrator-level capabilities).

## Capabilities

All moderator capabilities, plus:
- **Release outputs**: transition output sets from APPROVED to RELEASED, creating the downloadable Release Package
- **Manage execution environments**: view and oversee the environment catalogue
- **Manage data resources**: view and oversee the resource catalogue
- **Custom Build**: create analysis bundles using the Custom Build strategy

## Releasing output sets

After a moderator has approved an Output Set (transitioned to **APPROVED**), it is ready for release.

### The release process

1. Navigate to the approved Output Set.
2. Click **Release**.
3. The platform creates a Release Package ZIP containing the output files and execution metadata.
4. The Output Set transitions to **RELEASED** status.
5. The Release Package becomes available for researcher download.
6. The researcher receives an email notification that results are available.

Release is a terminal action. Once released, the Output Set cannot be modified or retracted. If the outputs are later found to be inappropriate, the Release Package can be removed from the researcher download (but the audit record remains).

### Release considerations

- Releasing is an **irreversible** governance action. Only release when you are certain the outputs are appropriate.
- The Release Package is the sole delivery mechanism for research results.
- Released output sets should be archived externally for compliance (see [Backup & Recovery](../administrator-guide/backup-and-recovery.md)).

## Custom Build

The **Custom Build** strategy allows a researcher to provide a custom `Dockerfile` that extends the institutional execution environment. This is useful when an analysis has specific system-level dependencies not covered by the curated environment.

Custom Build requires the `build.customize` capability. Maintainers and administrators have this by default. It can be granted to individual researchers through the user management UI.

When using Custom Build, the researcher provides a Dockerfile in the root of the bundle archive. The platform uses this Dockerfile instead of the curated institutional template when building the execution image.

## Viewing the audit log

Maintainers have access to the audit ledger. Use the **Audit Log** page to review all governance-significant events across the platform.

The audit log is read-only. It provides a permanent record of who did what and when.

## See also

- [Moderator Guide](moderator.md) — review and governance tasks
- [Researcher Guide](researcher.md) — bundle creation and submission
- [Administrator Guide](../administrator-guide/configuration.md) — platform management

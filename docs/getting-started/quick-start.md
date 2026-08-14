# Quick Start

A guided tutorial through the FERRY institutional workflow.

This tutorial walks through the complete lifecycle of an analysis: from installation through to downloading results. It is designed for someone evaluating FERRY for the first time.

## Before you begin

1. [Install FERRY](installation.md).
2. Verify the platform is running and accessible at `https://localhost`.
3. Ensure at least one data resource is registered. The [Data Resources
   administrator guide](../administrator-guide/data-resources.md) covers the
   full workflow. For evaluation, the `demo-surveillance` resource is
   registered automatically during installation.
4. Create evaluation persona accounts:

```bash
make seed-demo
```

This creates three accounts and prints their credentials. You will need all three to complete the tutorial.

## Step 1 — Log in as the Researcher

Open `https://localhost` in your browser and log in with the **Researcher** credentials printed by `make seed-demo`.

The Researcher is the person who creates analyses. A researcher does not have the authority to approve bundles, release outputs, or manage the platform — they can create projects, build analysis bundles, run validation, and submit work for review.

When you log in, the homepage displays quick actions relevant to a researcher: **Create Project** and **View Bundles**. This is the responsibility-oriented UI — what you see depends on your role.

## Step 2 — Accept Platform Terms

Before you can use the platform, you must accept the current version of the platform terms of service.

If terms have been published by the administrator, you will be redirected to the terms page on your first action. Read the terms and click **Accept**.

Acceptance is permanently recorded. You will not be asked again unless the institution publishes an updated version.

## Step 3 — Create a Project

A **Project** is a permission boundary and collaboration space. It groups related analyses and controls which data resources they may access.

Click **Create Project**, give it a name (for example, "COVID-19 Seroprevalence Analysis"), and add a brief description. You are automatically added as the first project member.

The project appears in your Projects list. Other users can be added later by someone with the `project.members.manage` capability.

## Step 4 — Configure Project Resources

A project needs data resources to analyse. Click into your project and navigate to the **Resources** tab.

The platform has pre-seeded data resources from manifests. Select the one that matches your intended analysis and attach it to the project.

Before attaching, you may be prompted to accept the dataset terms of service if the resource has published terms. Dataset terms are set by the data owner and are separate from the platform terms you accepted earlier.

Attaching a resource tells the platform: "this project is authorised to analyse this dataset." The actual data never leaves the institution's secure storage — the platform records the authorisation, not the data itself.

## Step 5 — Import the Example Analysis

Navigate to the **Bundles** tab and click **Create Bundle**.

An **Analysis Bundle** describes what to run, which execution environment to use, and which resources to access. It is a researcher artefact — you own it and control it until you submit for review.

Select an execution environment from the catalogue. The available environments (Python 3.13, Python 3.14, Conda) are curated by the institution. Each represents a guaranteed runtime contract.

Upload the example analysis files. You can use an analysis template from `examples/analyses/` if one is available, or prepare your own ZIP archive with an entry point script.

Configure the entry point, interpreter, and CLI arguments. The bundle workspace saves your progress automatically.

## Step 6 — Run Validation (Advisory)

Before submitting for review, you can run an operational **Validation** check.

Validation executes your bundle against **representative datasets** — structurally identical to the governed data but containing no sensitive information. It answers one question: *does the analysis code execute successfully?*

Click **Run Validation** in the bundle workspace. The worker polls for pending validation requests, launches an isolated container, runs your analysis against representative data, and reports the results.

Validation is advisory. You can submit without validating. But if validation succeeds, you have confidence the analysis will run in production.

A **Validated** indicator appears on the bundle to record this check. If you modify the bundle after validation, the indicator changes to warn that the bundle has changed.

## Step 7 — Submit for Review

When you are ready, click **Submit for Review**.

Submission transitions the bundle from **DRAFT** to **SUBMITTED** status. No further edits are permitted — the bundle is now an immutable artefact awaiting institutional governance.

Submission triggers a **Build**. The worker processes the bundle: if the build strategy is Institutional, it uses the curated template for the selected execution environment; if Custom Build, it uses the Dockerfile in your bundle. The resulting Execution Image is cached for reuse.

Submitting also sends an email notification to project members with review capability, alerting them that a bundle is waiting.

## Step 8 — Log in as the Moderator

Log out of the Researcher account and log in with the **Moderator** credentials.

The Moderator is the person who governs what enters and leaves the institution. A moderator can review bundles and output sets but cannot release outputs or manage the platform.

The homepage now shows different quick actions: review-related tasks take priority.

## Step 9 — Review and Approve the Bundle

Navigate to the project and find the submitted bundle under **Bundles Pending Review**.

Inspect the bundle details: the declared execution environment, the data resources it requests, the entry point, and the build strategy. The bundle is immutable at this point — what you see is exactly what will execute.

Click **Approve** to transition the bundle to **APPROVED_FOR_EXECUTION** status. This is the first stage of the two-stage governance gate. It means: *this analysis is authorised to execute against governed data*.

You may also **Reject** a bundle (with a reason) or **Supersede** it (when a newer version replaces an older approved one).

## Step 10 — Log in as the Researcher and Request Execution

Log out of the Moderator and log back in as the **Researcher**.

Navigate to your approved bundle. You can now create an **Execution Request** — an instruction to execute this specific bundle with specific parameters.

Click **Request Execution**. This creates a PENDING execution request. The worker picks it up, resolves the data resource endpoints, launches an isolated container, executes the analysis, and captures the outputs.

The execution status progresses: **PENDING → RUNNING → COMPLETED** (or FAILED). During execution, the analysis runs in a container with:
- no network access
- read-only data mounts
- non-root user
- configurable timeout

After completion, an **Output Set** is created in **PENDING_REVIEW** status. The researcher cannot access the outputs yet — they must pass governance first.

## Step 11 — Review and Approve the Output Set

Log in as the **Moderator** again.

Navigate to the **Output Sets Pending Review** section. You can inspect individual output files and execution metadata to verify the results are appropriate for release.

Click **Approve** to transition the Output Set to **APPROVED** status. This is the second governance gate: *these outputs are safe to release*.

## Step 12 — Release the Output

Still as the Moderator (or as a Maintainer, who has additional release capability), click **Release**.

Release transitions the Output Set to **RELEASED** status and creates a **Release Package** — a ZIP archive containing the output files and execution metadata. This is the sole delivery mechanism for research results.

The researcher is notified by email that results are available.

## Step 13 — Download the Results

Log in as the **Researcher** for the final step.

Navigate to the execution request. The **Download** button is now active. Download the Release Package ZIP.

The ZIP contains:
- All output files from the analysis
- `execution_metadata.json` — metadata about the execution (request details, file listing)

## Summary

You have completed the full FERRY institutional workflow:

```
Prepare → Validate → Submit → Review → Execute → Review → Release → Download
```

This is the governed research pipeline. Every transition is recorded in the audit ledger, attributable to the authenticated actor who performed it.

## Next steps

- [Researcher Guide](../user-guides/researcher.md) — detailed researcher workflows
- [Moderator Guide](../user-guides/moderator.md) — review and governance tasks
- [Architecture](../architecture-and-reference/architecture.md) — system design and concepts

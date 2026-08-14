# Researcher Guide

Task-oriented documentation for researchers using FERRY.

## Who is a Researcher?

A researcher creates projects, builds analysis bundles, runs validation, submits analyses for review, and downloads released results. Researchers do not approve bundles, release outputs, or manage the platform.

## Capabilities

- **Projects**: create projects, view project details, browse project members
- **Analysis Bundles**: create, edit, upload files, configure execution environments
- **Validation**: run advisory operational checks against representative data
- **Submission**: submit bundles for institutional review
- **Execution**: request execution of approved bundles
- **Outputs**: download released output packages

## Projects

A **Project** is a permission boundary and collaboration space. Projects group related analyses and control which data resources they may access.

### Creating a project

1. From the homepage, click **Create Project**.
2. Enter a name and optional description.
3. Click **Create**.

You are automatically added as the first project member. The project appears in your project list immediately.

### Browsing projects

The Projects list shows projects relevant to you:
- Projects you created.
- Projects you were added to by another member.

### Project details

Inside a project, you will find:
- **Bundles tab** — analysis bundles associated with this project
- **Resources tab** — data resources attached to the project
- **Members tab** — people who can access this project
- **Execution Requests tab** — execution requests and their output sets

## Analysis Bundles

An **Analysis Bundle** describes what to run and how to run it. It captures: the analysis code, the execution environment, the data resources it needs, and how to invoke it.

### Creating a bundle

1. Inside your project, navigate to the **Bundles** tab.
2. Click **Create Bundle**.
3. Give the bundle a name, version, and optional description.
4. Select an **Execution Environment** from the institutional catalogue.
5. Choose a **Build Strategy** (Institutional Build is the default).
6. Click **Create**.

The bundle is created in **DRAFT** status. You can edit it freely.

### Uploading analysis code

1. Inside the bundle workspace, use the file manager to upload your analysis ZIP archive.
2. Alternatively, upload individual files.
3. Set the **entry point** (the script that starts your analysis).
4. Choose the **interpreter** (python, shell, or r).
5. Add any **CLI arguments** your script expects.

### Declaring data resources

1. In the bundle workspace, open the **Resources** section.
2. Select the data resources your analysis needs from those attached to the project.
3. Your analysis will access them at `/data/{alias}`. For example, a resource with alias `demo-surveillance` is available at `/data/demo-surveillance/demo.csv`. The alias is displayed in the resource catalogue when you select it.

The same path works in both validation (representative data) and governed execution (production data) — your code does not need to change between environments. The path also works locally during development if you use the execution environment's base image.

### Saving your work

The bundle workspace saves pending changes automatically before submitting or validating. You can also save explicitly at any point.

## Validation

**Validation** is an advisory operational check. It runs your bundle against representative datasets (structurally identical to the governed data but containing no sensitive information) to verify that the code executes successfully.

### Running validation

1. Inside the bundle workspace, click **Run Validation**.
2. The worker picks up the request, builds an execution image, launches a container, and runs your analysis against representative data.
3. Results appear in the bundle workspace: execution logs, output files, and a pass/fail indicator.

### Interpreting results

- **Validated** — The bundle executed successfully against representative data. This does not guarantee scientific correctness, only that the code runs.
- **Bundle has changed since validation** — The bundle was modified after the last validation. Run validation again to confirm it still works.
- **No validation run** — The bundle has not been validated. Validation is optional.

### Important

- Validation is **advisory**. You can submit for review without validating.
- Validation runs against **representative datasets only** — governed data is never accessed during validation.
- A successful validation means your analysis code is likely to work in production, but the execution environment and resource mounts may differ slightly.

## Submission

When you are ready for institutional review, **submit** your bundle.

### Submitting

1. Ensure the bundle is complete (entry point, files, execution environment, data resources declared).
2. Click **Submit for Review**.
3. If the bundle references data resources with active dataset terms, you will be prompted to accept them before submission proceeds.

After submission:
- The bundle transitions from **DRAFT** to **SUBMITTED** status.
- No further edits are permitted. The bundle is an immutable artefact.
- The build process begins automatically (image construction).
- Project members with `bundle.review` capability receive an email notification.

You cannot edit a submitted bundle. To make changes, create a new bundle version.

## Execution

Once a bundle is approved (transitioned to **APPROVED_FOR_EXECUTION** by a moderator), you can request execution.

### Requesting execution

1. Find the approved bundle in your project.
2. Click **Request Execution**.
3. The execution request enters **PENDING** status.

The worker picks up the request and progresses through:
- **RUNNING** — container launched, analysis executing
- **COMPLETED** — analysis finished successfully
- **FAILED** — analysis encountered an error

During execution, your analysis runs in an isolated container with:
- No network access
- Read-only data mounts at `/data/{alias}`
- A writable output directory at `/output`
- A configurable timeout

You can view the execution log during and after execution.

## Outputs

After execution completes, an **Output Set** is created in **PENDING_REVIEW** status. You cannot access the outputs yet — they must pass institutional governance first.

### The approval pipeline

1. **PENDING_REVIEW** — Execution completed. Moderators inspect the outputs.
2. **APPROVED** — Moderator has determined the outputs are safe to release.
3. **RELEASED** — A Release Package ZIP has been created and is available for download.

### Downloading outputs

Once the output set reaches **RELEASED** status:

1. Navigate to the execution request in your project.
2. Click **Download**.
3. The Release Package ZIP contains:
   - All output files from the analysis
   - `execution_metadata.json` — execution metadata (request details, file listing)

The Release Package is the sole delivery mechanism for research results.

## See also

- [Quick Start](../getting-started/quick-start.md) — guided tutorial through the full workflow
- [Moderator Guide](moderator.md) — how bundles and outputs are reviewed
- [Architecture](../architecture-and-reference/architecture.md) — bundle lifecycle and governance model

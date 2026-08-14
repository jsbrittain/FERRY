# Execution Environments

Managing execution environments in FERRY.

## What is an Execution Environment?

An **Execution Environment** is part of the platform's execution infrastructure. It represents an approved runtime for analysis execution and defines the **institutional execution contract** — a guarantee about the runtime, filesystem layout, and security context that every analysis can rely on.

Researchers select from the curated catalogue of available environments when creating an analysis bundle. They do not specify arbitrary runtime strings; the institution controls which runtimes are available.

An execution environment is more than a language runtime. It represents an institutional commitment that analyses targeting that environment will execute correctly, securely, and consistently.

## Adding a new execution environment

```
1. Define the runtime     →  Dockerfile and package list (outside FERRY)
2. Build and publish      →  docker build + docker push (outside FERRY)
3. Register with FERRY →  place manifest — auto-discovered on next startup
4. Add acceptance test    →  optional, under frontend/e2e/
```

### Step 1 — Define the runtime (outside FERRY)

Create a Dockerfile that defines the base image, language runtime, and
pre-installed packages. The builder template (Python or Conda) will add the
bundle's own dependencies at build time.

Copy from an existing environment as a starting point:

```bash
mkdir -p execution-environments/my-env/
cp execution-environments/python-3.14/manifest.yaml execution-environments/my-env/
cp execution-environments/python-3.14/Dockerfile execution-environments/my-env/
# Edit manifest.yaml and Dockerfile to match the new runtime
```

### Step 2 — Build and publish the base image (outside FERRY)

Build the image and push it to a registry accessible to the platform:

```bash
docker build -t registry.example.com/ferry/my-env:latest .
docker push registry.example.com/ferry/my-env:latest
```

The `image_reference` in the manifest must match the published image tag.
The platform does not build or publish base images — it only references them.

### Step 3 — Register with FERRY

On startup, the platform automatically scans `execution-environments/` for
manifests and updates the registered definitions. No explicit registration
step is required:

```bash
make restart
```

Startup registration is idempotent. New manifests create new records; updated
manifests update existing records. This is intentional — unlike data resources,
where the manifest is a one-shot registration artefact, execution environments
are platform infrastructure whose authoritative definition lives in the
manifest file.

### Step 4 — Add an acceptance test (optional)

Add an execution environment acceptance test under
`frontend/e2e/execution-environment-acceptance/` to validate the runtime
contract. See the acceptance test documentation for the expected pattern.

## The execution contract

Every execution environment guarantees the following runtime contract inside an
analysis container:

| Path / property | Purpose |
|-----------------|---------|
| `/analysis` | Bundle injection target — analysis code is placed here |
| `/data` | Resource mount namespace — authorised data appears at `/data/{alias}` |
| `/output` | Writable results directory — analysis outputs go here |
| `/work` | Temporary scratch space |
| `nobody` user | Least-privilege execution identity |

This contract is validated by **Execution Environment Acceptance Tests** —
automated tests that verify a published environment can install declared
dependencies, build a runnable execution image, and produce expected outputs
under governed conditions. Each environment must pass its acceptance test
before it can be considered production-ready.

For details of how data resources are mapped to mount paths inside containers,
see the [Data Resources guide](data-resources.md#runtime-access-contract).

## Currently supported environments

| Name | Runtime | Base image |
|------|---------|------------|
| Python 3.13 | `python-3.13` | `python:3.13-slim` with NumPy, Pandas |
| Python 3.14 | `python-3.14` | `python:3.14-slim` with NumPy, Pandas |
| Conda | `conda` | `mambaorg/micromamba:2.8.1` |

## Registration

Execution environments are defined by YAML manifests and supporting artefacts
in the `execution-environments/` directory:

```
execution-environments/
├── python-3.13/
│   ├── Dockerfile           # Base image definition
│   ├── manifest.yaml        # Registration manifest (name, runtime, image reference)
│   └── ...
├── python-3.14/
│   └── ...
└── conda/
    └── ...
```

Manifests are discovered automatically at startup. Unlike data resources, where
the database is authoritative after registration, execution environment
manifests remain the authoritative definition — startup updates the database
from the manifest. This is the correct behaviour because execution environments
are platform infrastructure, not institutional assets.

## Researcher discovery

Researchers discover execution environments through the application UI:
- **List page** — all active environments with runtime, description, and image
  reference
- **Detail page** — full environment details including the curated Dockerfile,
  local development commands, and published artefact downloads
- **During bundle creation** — environment selector with display names and
  linked detail pages

Each environment detail page shows the configured runtime image and how to
build it locally from the Dockerfile. The `image_reference` is an
institution-specified runtime image — during development it may be built
locally; in production it refers to an image published to a registry chosen
by the institution.

This enables researchers to prepare their analysis locally against the
institutional runtime before uploading a bundle.

## See also

- [Data Resources](data-resources.md) — how data is mounted during execution
- [Architecture](../architecture-and-reference/architecture.md) — environment
  builder and execution model
- [Testing](../architecture-and-reference/testing.md) — acceptance test
  framework

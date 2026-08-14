# Testing

## Philosophy

FERRY's testing strategy follows a layered approach. Each layer validates a different concern, from individual function correctness through to end-to-end institutional workflow.

The layers are:

```
Unit tests          — individual functions, models, and utilities
Integration tests   — service-layer behaviour against a real database
Smoke tests         — API-level "is the stack alive" checks
e2e acceptance      — browser-based system validation
```

## Unit Tests

Unit tests cover individual functions, utility code, model validation, and workflow state machines. They require no database and no running services.

```
python -m pytest backend/tests/unit -v
```

Key areas:

- Workflow state transitions (`backend/app/workflow/`)
- Capability model and vocabulary
- Email template rendering
- Bundle fingerprint computation
- ZIP extraction and security validation (symlink rejection, path traversal blocking)

## Integration Tests

Integration tests validate service-layer behaviour against a real PostgreSQL database and Redis instance. They use a dedicated `ferry_test` database for isolation.

```
python -m pytest backend/tests/integration -v
```

Key areas:

- Identity validation (capability boundaries for each role)
- User management CRUD
- Project membership lifecycle
- Audit event recording and query
- Terms governance (publish, accept, enforce)
- Validation request lifecycle

Integration tests require PostgreSQL + Redis running on localhost with the `ferry_test` database created:

```
createdb ferry_test
```

## Smoke Tests

Smoke tests verify that the full API stack is alive and responding:

```
python -m pytest backend/tests/smoke -v
```

Smoke tests auto-skip if the full stack is not available. They are intended for deployment verification.

## e2e Acceptance Tests

Acceptance tests are organised under `frontend/e2e/` in a three-tier hierarchy:

```
frontend/e2e/
├── acceptance/                    # Tier 1: Persona Acceptance
├── institution/                   # Tier 2: Institutional Acceptance
├── execution-environment-acceptance/  # Tier 3: Execution Environment Acceptance
└── helpers/                       Shared test infrastructure
```

All acceptance tests require the full stack to be running. They are executed with Playwright:

```bash
make playwright              # run Tier 2 (institutional acceptance)
make playwright CMD=e2e/acceptance/researcher.spec.ts
```

### Shared Helpers

`frontend/e2e/helpers/` contains reusable test infrastructure:

- `auth.ts` — login helper
- `setup.ts` — test data provisioning (users, projects, bundles, terms)
- `zip.ts` — in-memory ZIP archive creation
- `ee-helpers.ts` — execution-environment-specific helpers (provision project, create bundle, poll build/execution, approve outputs, verify archives)

### Tier 1 — Persona Acceptance

Four persona acceptance tests, one per institutional role. Each validates that a specific role can complete its assigned responsibilities through the UI.

| Test | Role | What it proves |
|------|------|----------------|
| `researcher.spec.ts` | researcher | Can create projects, create bundles, run validation, submit for review |
| `moderator.spec.ts` | moderator | Can review and approve/reject bundles and output sets |
| `maintainer.spec.ts` | maintainer | Can manage environments, create projects with custom builds, release outputs |
| `administrator.spec.ts` | admin | Can create users, publish terms, view audit log |

These tests do not re-validate the full pipeline. They prove capability boundaries are correctly enforced and the UI surfaces the right actions for each role.

### Tier 2 — Institutional Acceptance

A single test (`frontend/e2e/institution/canonical.spec.ts`) that proves the entire platform works as an institutional system. It exercises the complete canonical workflow:

1. Login with admin credentials
2. Publish platform terms
3. Create a project
4. Attach a data resource to the project
5. Create an analysis and upload a bundle
6. Submit the bundle (DRAFT → SUBMITTED)
7. Approve the bundle (SUBMITTED → APPROVED_FOR_EXECUTION)
8. Run the analysis (PENDING → RUNNING → COMPLETED)
9. Approve the Output Set (PENDING_REVIEW → APPROVED)
10. Release the Output Set (APPROVED → RELEASED)
11. Download the Release Package
12. Verify the ZIP contains expected output + execution metadata
13. Verify audit events are visible in the admin Audit Log

This is a system test covering frontend, backend, database, worker, Docker executor, provider abstraction, runtime contract, output registration, download endpoint, and audit ledger.

### Tier 3 — Execution Environment Acceptance

Three execution environment acceptance tests, one per published environment. Each verifies that the environment honours its execution contract.

| Test | Environment | What it proves |
|------|-------------|----------------|
| `python-3.13.spec.ts` | Python 3.13 | Can install pip dependencies, build image, execute, produce outputs |
| `python-3.14.spec.ts` | Python 3.14 | Can install pip dependencies, build image, execute, produce outputs |
| `conda.spec.ts` | Conda | Can install conda dependencies, build image, execute, produce outputs |

Institutional workflow (project provisioning, bundle creation, submission, approval, output release) is handled by helpers and is not under test here. Each test focuses on the environment's runtime contract.

### Legacy e2e Tests

The following e2e tests continue to run in CI and validate specific feature areas:

- `frontend/e2e/custom-build-workflow.spec.ts` — validates the Custom Build strategy end-to-end
- `frontend/e2e/validation-workflow.spec.ts` — validates the validation run lifecycle end-to-end

## Quick Reference

| Command | What it runs | Prerequisites |
|---------|-------------|---------------|
| `python -m pytest backend/tests/unit -v` | Unit tests | None |
| `python -m pytest backend/tests/integration -v` | Integration tests | PostgreSQL + Redis + `ferry_test` |
| `python -m pytest backend/tests/smoke -v` | Smoke tests | Full running stack |
| `make test` | Unit + integration + smoke (native) | PostgreSQL + Redis + `ferry_test` |
| `make test-backend` | Full suite (in container via SSH) | OrbStack VM + Docker stack |
| `make playwright` | Institutional acceptance | Full running stack |
| `make playwright CMD=e2e/acceptance/researcher.spec.ts` | Researcher persona acceptance | Full running stack |
| `make playwright CMD=e2e/acceptance/moderator.spec.ts` | Moderator persona acceptance | Full running stack |
| `make playwright CMD=e2e/acceptance/maintainer.spec.ts` | Maintainer persona acceptance | Full running stack |
| `make playwright CMD=e2e/acceptance/administrator.spec.ts` | Administrator persona acceptance | Full running stack |
| `make playwright CMD=e2e/execution-environment-acceptance/python-3.14.spec.ts` | Python 3.14 EE acceptance | Full running stack |
| `make playwright CMD=e2e/execution-environment-acceptance/python-3.13.spec.ts` | Python 3.13 EE acceptance | Full running stack |
| `make playwright CMD=e2e/execution-environment-acceptance/conda.spec.ts` | Conda EE acceptance | Full running stack |

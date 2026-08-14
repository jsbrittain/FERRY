VM_HOST      ?= ferry.local
VM_USER      ?= ferry
VM_DIR       ?= /opt/ferry
SSH          ?= ssh $(VM_USER)@$(VM_HOST)
PYTHON       ?= python3

# Load execution context (silent if absent — defaults to native Docker).
-include .ferry-context
FERRY_TARGET ?= native

.PHONY: install uninstall start stop restart build upgrade backup restore certs enable-ai seed-demo logs shell register-resources register-resource dev-prune-resources dev test-backend test-execution dev-destroy dev-drop-db deploy deploy-dev ci ci-clean test format lint fix playwright new-data-resource

# --- Installation ----------------------------------------------------------------
# install is the canonical first-run experience.  Accepts an optional TARGET
# parameter:
#
#   TARGET=multipass (default)   — Multipass VM installation
#   TARGET=orbstack              — OrbStack VM installation
#   TARGET=native                — native Docker installation (no VM)
#
# Installs the platform, seeds the institution, and writes the execution context.
# Idempotent — safe to run repeatedly.

TARGET ?= multipass

install:
	$(eval ENV_FRESH := $(shell [ -f .env ] && echo "no" || echo "yes"))
ifeq ($(TARGET),orbstack)
	./scripts/orbstack.sh create
	./scripts/orbstack.sh mount
	@echo "FERRY_TARGET=$(TARGET)" > .ferry-context
	@echo "FERRY_VM=ferry" >> .ferry-context
	@echo "FERRY_REACHABLE_URL=https://localhost" >> .ferry-context
	./scripts/init-config.sh
	./scripts/setup-certs.sh
	./scripts/platform.sh run ./scripts/install.sh --dev
	./scripts/platform.sh run ./scripts/seed-institution.sh
else ifeq ($(TARGET),multipass)
	./scripts/multipass.sh create
	./scripts/multipass.sh mount
	@echo "FERRY_TARGET=$(TARGET)" > .ferry-context
	@echo "FERRY_VM=ferry" >> .ferry-context
	@VM_IP=$$(./scripts/multipass.sh ip 2>/dev/null); \
	if [ -n "$$VM_IP" ]; then \
		echo "FERRY_REACHABLE_URL=https://$$VM_IP" >> .ferry-context; \
		./scripts/init-config.sh; \
		./scripts/setup-certs.sh; \
	fi
	./scripts/platform.sh run ./scripts/install.sh --dev
	./scripts/platform.sh run ./scripts/seed-institution.sh
else ifeq ($(TARGET),native)
	@echo ""
	@echo "ERROR: Native installation is not yet supported."
	@echo ""
	@echo "The required host-level preparation has not been"
	@echo "implemented.  Please use a VM-backed target:"
	@echo ""
	@echo "    make install TARGET=multipass"
	@echo "    make install TARGET=orbstack"
	@echo ""
	@exit 1
else
	@echo "Unsupported installation target: $(TARGET)"
	@echo "Supported targets: orbstack, multipass"
	@exit 1
endif
	@echo ""
	@echo "=== FERRY installed ==="
	@echo ""
	@echo "Frontend:"
ifeq ($(TARGET),multipass)
	@echo "  $$(sed -n 's/^FERRY_REACHABLE_URL=//p' .ferry-context 2>/dev/null)/"
else
	@echo "  https://localhost/"
endif
	@echo ""
	@echo "Administrator account:"
	@echo "  Email:"
	@echo "      admin@ferry.local"
	@echo "  Password:"
	@echo "      Stored as ADMIN_PASSWORD in .env"
	@echo ""
	@echo "Configuration:"
	@if [ "$(ENV_FRESH)" = "yes" ]; then \
		echo "  .env was created automatically from .env.example"; \
		echo "  and contains installation-specific configuration,"; \
		echo "  including:"; \
		echo ""; \
		echo "    - administrator password"; \
		echo "    - application secrets"; \
		if [ "$(TARGET)" = "multipass" ]; then \
			echo "    - FERRY_REACHABLE_URL set to the VM IP"; \
		fi; \
		echo "    - optional SMTP configuration"; \
	else \
		echo "  Existing .env configuration reused."; \
	fi
	@echo ""
	@echo "Platform status:"
	@echo "  - Platform running"
	@echo "  - Platform Terms published"
	@echo "  - Institutional publications registered"
	@echo ""
	@echo "To prepare an evaluation environment:"
	@echo ""
	@echo "    make seed-demo"

# uninstall stops the platform and removes the installation.
# Dispatch depends on the execution context (.ferry-context).
# The Git working tree and .env are preserved.

# Detect explicit TARGET= override for uninstall recovery.
# When TARGET is set on the command line (not inherited from the
# default), it is passed as an environment variable override so
# that platform.sh can dispatch to the correct backend even when
# .ferry-context is missing.
ifneq ($(origin TARGET),command line)
_FERRY_TARGET_OVERRIDE :=
else
_FERRY_TARGET_OVERRIDE := FERRY_TARGET=$(TARGET)
endif

uninstall:
	@if [ ! -f .ferry-context ] && [ -z "$(_FERRY_TARGET_OVERRIDE)" ]; then \
		echo "No execution context found."; \
		echo ""; \
		echo "Specify the execution backend to uninstall:"; \
		echo ""; \
		echo "    make uninstall TARGET=multipass"; \
		echo "    make uninstall TARGET=orbstack"; \
		echo "    make uninstall TARGET=native"; \
		exit 1; \
	fi; \
	echo "=== FERRY Uninstall ==="; \
	$(_FERRY_TARGET_OVERRIDE) ./scripts/platform.sh compose down 2>/dev/null || true; \
	$(_FERRY_TARGET_OVERRIDE) ./scripts/platform.sh destroy || true; \
	rm -f .ferry-context; \
	rm -rf certs; \
	if [ -f .env ]; then \
		echo ""; \
		echo ".env preserved at $$PWD/.env"; \
	fi

# --- Operations -------------------------------------------------------------------
# start, stop, and restart are the primary lifecycle commands.
# start is the single command to bring an existing installation online.
# restart is stop followed by start — no rebuild, no reseed, no migration.
# upgrade, backup, and restore are maintenance operations.

# Start a running FERRY installation.  If the platform runs inside a VM,
# the VM is started first; then all services are started.
# No rebuild, no reseed, no migration — this is purely start after stop or reboot.
start:
	./scripts/platform.sh start
	./scripts/platform.sh compose up -d

# Stop all services gracefully.  All persistent state is preserved.
stop:
	./scripts/platform.sh compose down

# Stop then start.  No image rebuild — containers restart with their
# existing images.  Use `make upgrade` to update images.
restart:
	./scripts/platform.sh compose down
	./scripts/platform.sh compose up -d

# Build a single service image.  SVC defaults to all services.
SVC ?=
build:
	./scripts/platform.sh compose build $(SVC)
	./scripts/platform.sh compose up -d $(SVC)

# Pull latest code, rebuild all images, start services, run migrations.
upgrade:
	./scripts/platform.sh run ./scripts/upgrade.sh

# Create a backup archive (pg_dump + tarball).  Stores off-VM guidance
# is in the backup and recovery documentation.
backup:
	./scripts/platform.sh run ./scripts/backup.sh

# Restore from a backup archive.  Overwrites current database and filesystem.
restore:
	./scripts/platform.sh run ./scripts/restore.sh $(FILE)

# Regenerate TLS certificates, restart reverse proxy.
# Idempotent: safe to run at any time.
certs:
	./scripts/setup-certs.sh
	@if [ -f .ferry-context ]; then \
		echo "Restarting reverse proxy..."; \
		if ./scripts/platform.sh restart reverse-proxy; then \
			echo ""; \
			echo "✓ Certificate configuration applied."; \
		else \
			echo ""; \
			echo "Certificates were generated successfully."; \
			echo ""; \
			echo "The new certificates are not yet active because the reverse"; \
			echo "proxy could not be restarted automatically."; \
			echo ""; \
			echo "Please restart the reverse proxy manually, then revisit:"; \
			echo ""; \
			echo "    https://localhost"; \
			echo ""; \
			false; \
		fi; \
	fi

# --- Administration ---------------------------------------------------------------
# Platform configuration and resource management.

# Enable and prepare AI assistance.
# Idempotent — safe to run at any time.
OLLAMA_MODEL := $(shell grep '^OLLAMA_MODEL=' .env 2>/dev/null | cut -d= -f2-)
OLLAMA_MODEL ?= llama3.2

enable-ai:
	./scripts/setup-ai.sh
	@if [ -f .ferry-context ]; then \
		echo "Starting AI services..."; \
		./scripts/platform.sh compose --profile ai up -d || { \
			echo ""; \
			echo "Failed to start AI services."; \
			echo "Check Docker status and try again."; \
			false; }; \
		echo "Pulling AI model ($(OLLAMA_MODEL))..."; \
		./scripts/platform.sh exec ollama ollama pull $(OLLAMA_MODEL) || { \
			echo ""; \
			echo "Failed to pull AI model."; \
			echo "Check network connectivity and Ollama status."; \
			false; }; \
		echo "Restarting backend..."; \
		./scripts/platform.sh restart backend || true; \
		echo "Verifying AI readiness..."; \
		for i in 1 2 3 4 5 6 7 8 9 10 11 12; do \
			./scripts/platform.sh exec backend python -m app.cli check-ai-status 2>/dev/null; \
			if [ $$? -eq 0 ]; then \
				echo ""; \
				echo "=== AI assistance is operational ==="; \
				echo "Model: $(OLLAMA_MODEL)"; \
				echo ""; \
				echo "AI review is not yet enabled."; \
				echo "Enable it in the admin interface:"; \
				echo "  Admin > Settings > Enable AI-assisted bundle review"; \
				exit 0; \
			fi; \
			sleep 5; \
		done; \
		echo ""; \
		echo "=== AI verification timed out ==="; \
		echo "Run the CLI command to diagnose:"; \
		echo "  ./scripts/platform.sh exec backend python -m app.cli check-ai-status"; \
		false; \
	fi

# Seed evaluation personas and print welcome message.
# Idempotent: safe to run multiple times.
seed-demo:
	./scripts/platform.sh run ./scripts/seed-personas.sh
	./scripts/platform.sh run ./scripts/seed-demo.sh

# Register all resource manifests with FERRY.
# Creates new resources; skips previously registered ones.
register-resources:
	./scripts/platform.sh exec backend python -m app.cli resource-register-all

# Register a single resource manifest by identifier.
register-resource:
	./scripts/platform.sh exec backend python -m app.cli resource-register "$(ID)"

# Tail container logs.
logs:
	./scripts/platform.sh logs -f

# Interactive session on the platform host.
shell:
	./scripts/platform.sh shell

# --- Production deployment (SSH to Ubuntu VM) ----------------------------------

deploy:
	$(SSH) 'cd $(VM_DIR) && ./scripts/install.sh'
	@echo "FERRY_TARGET=remote" > .ferry-context
	@echo "FERRY_HOST=$(VM_HOST)" >> .ferry-context
	@echo "FERRY_USER=$(VM_USER)" >> .ferry-context
	@echo "FERRY_DIR=$(VM_DIR)" >> .ferry-context

deploy-dev:
	$(SSH) 'cd $(VM_DIR) && ./scripts/install.sh --dev'
	@echo "FERRY_TARGET=remote" > .ferry-context
	@echo "FERRY_HOST=$(VM_HOST)" >> .ferry-context
	@echo "FERRY_USER=$(VM_USER)" >> .ferry-context
	@echo "FERRY_DIR=$(VM_DIR)" >> .ferry-context

# --- Development ------------------------------------------------------------------
# Local development, testing, and CI workflows.

dev: restart
	./scripts/platform.sh run ./scripts/seed-institution.sh
	./scripts/platform.sh run ./scripts/seed-developer.sh
	./scripts/platform.sh run ./scripts/seed-personas.sh

# Run backend unit, integration, and smoke tests inside the container.
# Drops the file-backed cache to avoid stale last-failed artefacts.
# Depends on a running stack (make restart / make dev).
test-backend:
	./scripts/platform.sh exec backend python3 -m pytest tests/unit tests/integration tests/smoke -v --no-header -q --tb=short -p no:cacheprovider

# Run the execution (worker) integration test suite.
# Worker source and test files are copied into the container at runtime;
# PYTHONPATH is set so that ``from worker.main import ...`` resolves via
# normal package lookup.  Depends on a running stack (make restart / make dev).
test-execution:
	@echo "Preparing worker test environment..."
	./scripts/platform.sh compose exec --user root backend mkdir -p /worker_src /worker_tests 2>/dev/null
	./scripts/platform.sh compose cp worker backend:/worker_src/worker 2>/dev/null
	./scripts/platform.sh compose cp worker/tests backend:/worker_tests 2>/dev/null
	@echo "Running worker tests..."
	./scripts/platform.sh compose exec -e PYTHONPATH=/worker_src/worker backend \
		python3 -m pytest /worker_tests/ -v --tb=short -p no:cacheprovider

dev-destroy:
	./scripts/platform.sh compose down
	@echo "=== Development containers stopped ==="

# Scaffold a new data resource skeleton from a template.
# Usage: make new-data-resource ID=uk-biobank NAME="UK Biobank Serum" PROVIDER=csv
new-data-resource:
	./scripts/new-resource.sh "$(ID)" "$(NAME)" "$(PROVIDER)"

# Remove stale resource registrations (developer utility only).
# Removes resources whose manifest directory no longer exists on disk.
# Resources still referenced by projects or bundles are preserved
# by database constraints.
dev-prune-resources:
	./scripts/platform.sh exec backend python -m app.cli resource-clean

# Full CI bootstrap (init, build, start, seed all).
ci:
	./scripts/init-config.sh
	./scripts/platform.sh run ./scripts/bootstrap.sh
	./scripts/platform.sh run ./scripts/seed-institution.sh
	./scripts/platform.sh run ./scripts/seed-personas.sh
	./scripts/platform.sh run ./scripts/seed-developer.sh
	@echo "FERRY_TARGET=native" > .ferry-context

# Destroy all CI resources (volumes + .env).
ci-clean:
	./scripts/platform.sh compose down -v
	rm -f .env

# Run the complete platform test suite.
# Runs unit tests natively (with coverage), then backend and execution
# integration tests inside the container.
test:
	@failed=0; \
	echo "=== Running unit tests ==="; \
	(cd backend && $(PYTHON) -m pytest tests/unit -v --cov=app --cov-report=term-missing --no-header -q) || failed=1; \
	echo ""; \
	$(MAKE) test-backend || failed=1; \
	echo ""; \
	$(MAKE) test-execution || failed=1; \
	echo ""; \
	if [ $$failed -eq 0 ]; then echo "=== All tests passed ==="; else echo "=== Some tests failed ==="; exit 1; fi

# Run acceptance tests (requires full stack).
# Uses a compose override to increase the login rate limit for the
# Playwright suite (51 sequential API logins across 8 tests).
playwright:
	./scripts/platform.sh compose -f docker-compose.yml -f docker-compose.playwright.yml up -d backend
	@BASE=$${PLAYWRIGHT_BASE_URL:-$$(sed -n 's/^FERRY_REACHABLE_URL=//p' .ferry-context 2>/dev/null || true)}; \
	if [ -z "$$BASE" ] && [ -f .env ]; then \
		BASE=$$(sed -n 's/^PUBLIC_URL=//p' .env 2>/dev/null || true); \
	fi; \
	export ADMIN_PASSWORD=$$(grep ^ADMIN_PASSWORD= .env | cut -d= -f2-); \
	cd frontend && PLAYWRIGHT_BASE_URL="$${BASE:-https://localhost}" npx playwright test

# Auto-format Python code.
format:
	cd backend && $(PYTHON) -m ruff format

# Static analysis.
lint:
	cd backend && $(PYTHON) -m ruff check

# Auto-fix then format.
fix:
	cd backend && $(PYTHON) -m ruff check --fix
	cd backend && $(PYTHON) -m ruff format

# --- Development (destructive) ----------------------------------------------------
# Commands that destroy platform state.  Never run on a commissioned installation.

# DANGER: Drops ALL database tables.  All users, projects, bundles, audit events,
# terms, and governance records are permanently lost.
# This is a development utility only — never run on a commissioned installation.
dev-drop-db:
	@echo ""
	@echo " DANGER: This will destroy ALL data in the database."
	@echo " Users, projects, bundles, audit events, terms, and"
	@echo " governance records will be permanently lost."
	@echo ""
	@read -p " Continue? [y/N] " confirm; \
	if [ "$$confirm" != "y" ]; then echo "Aborted."; exit 1; fi
	./scripts/platform.sh compose exec -T postgres psql -U ferry -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>/dev/null || \
		(./scripts/platform.sh compose up -d postgres && sleep 3 && \
		 ./scripts/platform.sh compose exec -T postgres psql -U ferry -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
	./scripts/platform.sh restart backend
	@echo ""
	@echo "=== Database reset (all tables recreated on startup) ==="

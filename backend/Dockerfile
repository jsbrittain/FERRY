FROM python:3.11-slim AS base

WORKDIR /app

# Create the ferry user with a fixed UID (1000) matching the
# provisioned host user from cloud-init.yaml.  This ensures that
# host-mounted volume directories owned by uid 1000 are writable by
# the container process.  Deployment scripts (bootstrap.sh) handle
# directory provisioning — the runtime never compensates for it.
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --system --create-home --shell /bin/false --uid 1000 ferry

COPY pyproject.toml .
RUN pip install --no-cache-dir "."

COPY . .

RUN mkdir -p /var/lib/ferry/bundles /var/lib/ferry/outputs /var/lib/ferry/releases && \
    chown -R ferry:ferry /var/lib/ferry

USER ferry
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS development
USER root
RUN pip install --no-cache-dir ".[dev]"
USER ferry

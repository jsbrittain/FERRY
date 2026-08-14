## Local Development

The execution environment image is defined by the Dockerfile in this directory.
It is an institution-specified runtime image — during development it may be
built locally; in production it will refer to an image published to a registry
chosen by the institution.

### Build the image

The Dockerfile is available from the **Technical Reference** tab on this page,
or directly at `execution-environments/conda/Dockerfile` in the repository.

```sh
docker build -t ferry/conda:latest .
```

### Run with your dependencies

Mount your analysis code and install dependencies before running the entrypoint:

```sh
docker run --rm -it \
  -v $(pwd):/analysis \
  -v $(pwd)/data:/data:ro \
  -v $(pwd)/output:/output \
  ferry/conda:latest \
  sh -c "micromamba install -y -n base -f /analysis/environment.yml && micromamba clean --all --yes && python /analysis/run.py"
```

### Run interactive shell

Explore the runtime interactively:

```sh
docker run --rm -it \
  -v $(pwd):/analysis \
  -v $(pwd)/data:/data:ro \
  ferry/conda:latest \
  /bin/bash
```

### Test with representative data

Download a representative dataset and place it in your local `data/` directory. The container mounts `data/` at `/data` (read-only), matching the production data path.

### Run without Docker

Install micromamba on your development machine:

```sh
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba
export PATH="$PWD/bin:$PATH"

# Create environment from your Analysis Bundle
micromamba create -f /path/to/analysis/environment.yml
micromamba run -n analysis python /path/to/analysis/run.py
```

### Expected paths

| Path | Purpose | Access |
|------|---------|--------|
| `/analysis` | Bundle source code | Read-write |
| `/data` | Data resources | Read-only |
| `/output` | Analysis results | Read-write |
| `/work` | Scratch space | Read-write |

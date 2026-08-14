## Local Development

The execution environment image is defined by the Dockerfile in this directory.
It is an institution-specified runtime image — during development it may be
built locally; in production it will refer to an image published to a registry
chosen by the institution.

### Build the image

The Dockerfile is available from the **Technical Reference** tab on this page,
or directly at `execution-environments/python-3.13/Dockerfile` in the repository.

```sh
docker build -t ferry/python-3.13:latest .
```

### Run with your dependencies

Mount your analysis code and install dependencies before running the entrypoint:

```sh
docker run --rm -it \
  -v $(pwd):/analysis \
  -v $(pwd)/data:/data:ro \
  -v $(pwd)/output:/output \
  ferry/python-3.13:latest \
  sh -c "pip install --no-cache-dir -r /analysis/requirements.txt && python /analysis/run.py"
```

### Run interactive shell

Explore the runtime interactively:

```sh
docker run --rm -it \
  -v $(pwd):/analysis \
  -v $(pwd)/data:/data:ro \
  ferry/python-3.13:latest \
  /bin/bash
```

### Test with representative data

Download a representative dataset and place it in your local `data/` directory. The container mounts `data/` at `/data` (read-only), matching the production data path.

### Expected paths

| Path | Purpose | Access |
|------|---------|--------|
| `/analysis` | Bundle source code | Read-write |
| `/data` | Data resources | Read-only |
| `/output` | Analysis results | Read-write |
| `/work` | Scratch space | Read-write |

## Local Development

You can develop and test Analysis Bundles locally using the execution environment image.

### Prerequisites

- Docker installed on your machine

### Build the Environment Image

The execution environment image is defined in the repository under
`execution-environments/`. Build it locally from the Dockerfile:

```sh
docker build -t ferry/python-3.14:latest execution-environments/python-3.14/
```

The tag is a local convention. In production, this image would be built and
published to a registry chosen by the institution.

### Prepare Your Workspace

```
my-analysis/
    run.py
    requirements.txt
    data/               # Representative data (download from Data Resource)
    output/             # Local output directory
```

### Run Your Analysis

```sh
docker run --rm -it \
  -v $(pwd):/analysis \
  -v $(pwd)/data:/data:ro \
  -v $(pwd)/output:/output \
  ferry/python-3.14:latest \
  python /analysis/run.py
```

### Test with Representative Data

Each [Data Resource](/resources) may publish a **Representative Dataset** — a small sample suitable for local development. Download it from the resource detail page and place it in your `data/` directory.

### Expected Paths

The container follows the same path conventions as institutional execution:

| Path | Purpose | Access |
|------|---------|--------|
| `/analysis` | Bundle source code | Read-write |
| `/data` | Data resources | Read-only |
| `/output` | Analysis results | Read-write |
| `/work` | Scratch space | Read-write |

### Environment-Specific Guidance

Each [Execution Environment](/environments) has a **Local Development** tab with environment-specific instructions.

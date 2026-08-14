## Minimal Python Bundle Template

A minimal Python analysis bundle structure for [Python 3.14](/environments/python-3.14).

### Contents

- `run.py` — Entrypoint skeleton
- `requirements.txt` — Python dependencies

### Getting Started

1. Download `template.zip`
2. Extract and customise `run.py`
3. Add your analysis code
4. Zip the files and upload to FERRY

### Bundle Structure

```
run.py              # Entrypoint (required)
requirements.txt    # Python dependencies (optional)
```

### Execution Contract

- `/analysis` — Bundle source code (read-write)
- `/data` — Data resources (read-only)
- `/output` — Analysis results (read-write)

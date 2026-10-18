# Local Docker Demonstration

Docker is optional: the [Python setup](../README.md) provides the same functionality.
Use Docker Engine/Desktop with **Linux containers** and Compose v2. Initial image build
downloads Python packages; later synthetic-data runs use only local resources.

## Start Jupyter

Run from the clone root. Create mount directories explicitly so Docker does not create
root-owned directories unexpectedly.

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force data, outputs
docker compose up --build notebook
```

Linux/macOS Bash:

```bash
mkdir -p data outputs
export LOCAL_UID=$(id -u)
export LOCAL_GID=$(id -g)
docker compose up --build notebook
```

Open `http://localhost:8888` and use the token printed in the log. Select
`notebooks/finance_demo.ipynb`, then restart the kernel and run all cells. The source
notebook explicitly selects inline plotting so charts also render in the container.
Authentication is left enabled, and the host port binds only to `127.0.0.1`.
Never publish the token or expose the port on a public interface.

If port 8888 is occupied, set `NOTEBOOK_PORT` before starting, for example
`$env:NOTEBOOK_PORT = '8889'` in PowerShell or `export NOTEBOOK_PORT=8889` in Bash.
Then open `http://localhost:8889`; the internal service port remains 8888.

To run in the background:

```bash
docker compose up -d --build --wait notebook
docker compose logs notebook
```

Keep the shell's `LOCAL_UID`/`LOCAL_GID` values for subsequent Compose commands on Linux.
The non-root image defaults to UID/GID 10001. If bind-mounted files are not writable,
set these variables to the host owner's numeric IDs and recreate the service.
On Windows Docker Desktop, enable access to the project drive/directory if prompted.

## Batch and HTML Reports

```bash
docker compose build
docker compose run --rm batch
docker compose run --rm batch python scripts/execute_notebook.py
```

`batch` runs the same `finance-demo` implementation without starting a notebook server.
Its default generates synthetic fixtures, then writes the database, metrics, CSVs,
and plots into `outputs/`. The second command executes the notebook in a fresh kernel
and exports `outputs/finance_demo.html` and `outputs/finance_demo.executed.ipynb`.
Do not run batch processing concurrently with Run All in the notebook.

For real private inputs already under `data/private`, explicitly replace the command:

```bash
docker compose run --rm batch python -m finance_tracker.pipeline --input-dir data/private --output-dir outputs/private --config config/demo.json
```

This command does not generate or overwrite demo fixtures. Follow the data contract
and minimum-history requirements in [DEMO.md](DEMO.md).

## Persistent Files and Configuration

| Host directory | Container directory | Purpose |
| --- | --- | --- |
| `data/` | `/app/data` | Synthetic or private bank inputs and receipts |
| `outputs/` | `/app/outputs` | SQLite documents, analytical marts, plots, reports, logs |
| `notebooks/` | `/app/notebooks` | Notebook source and saved edits |

Only these directories are bind-mounted. Package code, scripts, and configuration are
copied into the image. After changing `src/`, `scripts/`, `config/`, dependency pins,
or the Dockerfile, rebuild using `docker compose build`. If the notebook is saved with
outputs in the browser, those changes persist to the tracked source file; clear outputs
before committing. Private data and outputs are ignored but must still be reviewed
before sharing a repository or notebook.

SQLite, CSV marts, and local report directories provide the document, analytical, and
artifact storage needed for the demo. No separate database server or object-store
container is necessary. The archived future material is excluded from the image context.

## Stop and Verify

```bash
docker compose config --quiet
docker compose ps
docker compose logs --no-color
docker compose down
```

Stopping containers does not delete host data or reports. Delete those manually only
when no longer needed. `docker image rm personal-finance-demo:local` removes the built
demo image after stopping containers; it does not remove project files.

Before a Docker presentation, verify a successful build, a healthy notebook service,
rendered charts, working widgets, and persisted reports on your own machine. Docker
runtime verification was not possible on the implementation machine because Docker
was unavailable. Python/notebook checks and YAML parsing are separate, narrower evidence.
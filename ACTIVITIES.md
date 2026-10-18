# Local Implementation Activity Log

This is the current code/setup walkthrough. Earlier design decisions and verification
history are preserved in
[future-cloud-scope/docs/HISTORICAL_ACTIVITIES.md](future-cloud-scope/docs/HISTORICAL_ACTIVITIES.md).

## 1. Narrow the Supported Scope

The project now demonstrates data science locally through Python and Jupyter, with
optional Docker Compose packaging. Local directories hold inputs/reports; SQLite stores
transaction JSON and nested receipts; Pandas constructs monthly marts. The CLI provides
repeatable batch runs, and the notebook presents the experiments and results.

The original abstract and prior external-infrastructure implementation are retained in
[future-cloud-scope](future-cloud-scope/README.md), not deleted. That directory is an
inactive reference archive, excluded from active packaging, tests, CI, and Docker builds.
The active abstract now distinguishes local analytics from distributed-scale claims.

## 2. Remove External Execution Paths

- `pipeline.py` no longer exposes an external publishing/downloading option. Its only
  actions are local fixture generation, preprocessing, analysis, persistence, and reports.
- `pyproject.toml` declares local analytical dependencies and the development extra only.
- The previous provider adapters, tests, dependency snapshot, deployment files, and guides
  were moved intact into the archive. Active tests collect only the local `tests/` tree.
- A CLI test checks that the old external execution flag is absent and rejected.
- Observed focused validation: four analytical/CLI tests passed; after relocation,
  all six active tests passed with warnings treated as errors.

## 3. Preserve the Analytical Work

`data.py` generates reproducible CSV/JSON fixtures and audits missing/invalid/duplicate
records. `analytics.py` computes cash flow, trains a chronological category classifier,
flags unusual expenses, and compares rolling Ridge forecasts with a seasonal baseline.
`pipeline.py` shares the implementation across notebook, CLI, and container batch runs.
Known categories remain separate from inferred labels; synthetic scores are not claims
of real-world accuracy. The weak anomaly precision remains an explicit study limitation.

## 4. Add Local Container Packaging

- `Dockerfile` installs the local project on Python 3.14, copies notebooks/scripts/config,
  and starts Jupyter as a non-root user. It has no remote execution entry point.
- `compose.yaml` defines notebook and opt-in batch services using the same image.
  Only the notebook binds a host port, restricted to loopback. Token authentication stays on.
- Host data, report, and notebook directories persist across container removal. Linux
  UID/GID overrides prevent root-owned outputs; writable mount directories are required.
- The batch service runs the same Python pipeline. An explicit command can also execute
  and export the notebook without starting a server.
- CI now checks Python on Windows/Linux and defines local container build, batch,
  notebook execution, and server-health gates. No infrastructure-provider job remains.
- Observed local configuration check: Compose and CI YAML parse; service/job scope and
  local-only notebook exposure were checked. Docker is unavailable here, so actual
  container build, startup, mounts, and widget interaction are not yet verified.

## 5. Update Demonstration Instructions

The root guide now starts with Python/Jupyter and offers Docker as an alternative.
`docs/DEMO.md` covers the viva sequence, input schema, local storage, privacy, and optional
OS scheduling. `docs/DOCKER.md` covers setup, ports, persistent files, batch/HTML export,
permissions, and cleanup. Historical remote deployment instructions remain only in the archive.

The notebook retains its analytical cells and metadata while replacing external
storage instructions with local JSON/SQL inspection. Each notebook run continues to
write a timestamped `outputs/notebook_activities.md` execution log. Further observed
validation results are recorded below as they complete.

## 6. Verify a Clean Local-Only Installation

A new temporary Python 3.14 virtual environment was created outside the repository;
the existing user environment was left intact. Installing only `.[dev]` using the
previous version constraints installed no Google SDK or RPC packages. A new active
`requirements-lock.txt` was generated from this environment, excluding machine-specific
editable paths and retaining Windows platform markers. The original broader dependency
snapshot remains in the inactive archive.

The notebook explicitly selects inline plotting before importing pyplot. This matters
because the batch container uses the headless `Agg` backend. A clean-environment run
with `MPLBACKEND=Agg` completed and emitted five nonblank chart images. Storage inspection
now queries nested receipt JSON and monthly cash flow directly from local SQLite.

| Local check | Observed result |
| --- | --- |
| Fresh installation without external SDK extras | No Google SDK/RPC packages present |
| `pip check` in the fresh environment | No broken requirements |
| `pytest -q -W error` | 6 active tests passed |
| Root-wide pytest collection | Only the same 6 local tests; archive excluded |
| Clean-kernel notebook execution | All 6 code cells completed and HTML exported |
| Headless chart rendering | 5 nonblank inline chart images verified from exported outputs |
| Installed local CLI | Completed; 4,320 clean transactions and report artifacts |
| Source notebook format | 12 cells valid with required language/ID metadata |
| Active Markdown links | All checked targets resolve |
| Compose and CI YAML | Parsed; local services/jobs and loopback binding checked |
| Editor diagnostics | No errors in active Python source/tests/scripts |
| Git diff check | Passed; only the existing LF/CRLF conversion warning appeared |

On Windows, the notebook runner still prints Jupyter event-loop and local kernel
transport warnings; execution succeeds. Keep notebook/kernel ports private. Docker is
not available here, so no image build, container execution, or browser/widget interaction
inside Docker is claimed. The local container CI gates are defined but have not run here.
No remote infrastructure was contacted or created. No commit or push was performed
for this scope update.
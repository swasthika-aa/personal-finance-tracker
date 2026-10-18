# Local Demonstration and Data Guide

## Suggested 12-Minute Viva

1. Present the three questions in notebook Cell 1: categorization, anomaly review,
   and forecasting. Explain that the data is synthetic and the work runs locally.
2. Run the setup cell. Inspect duplicate removal, invalid-date rejection, missing
   descriptions, UTC timestamps, and receipt matching in the cleaning audit.
3. Show EDA, category trends, and monthly cash-flow reconciliation. Cumulative
   net cash flow is not an account balance because the opening balance is unknown.
4. Compare classification macro F1 against the majority baseline; explain the
   chronological split, train-only preprocessing, and repeated-merchant limitation.
5. Review flagged expenses and synthetic anomaly precision/recall. Weak precision
   is a finding to discuss, not evidence of reliable fraud detection.
6. Compare rolling forecast MAE with seasonal naive; acknowledge whichever wins.
   Explain recursive prediction and the heuristic, uncalibrated uncertainty band.
7. Change the year/category controls and budget-reduction slider in the live notebook.
8. Inspect nested receipt JSON and a monthly SQL summary from local SQLite.
9. Show local CSV/PNG reports and the generated HTML and execution Markdown log.
10. Close with data consent, real-label validation, forecast uncertainty, and next experiments.

## Prepare the Demo

Follow the root [README](../README.md) for Python setup, or
[DOCKER.md](DOCKER.md) for an isolated local container. Run these checks before presenting:

```bash
python -m pytest -q -W error
python scripts/execute_notebook.py
```

Use the `.venv` Python if it is not activated. The notebook runner executes a fresh kernel
and writes HTML plus an executed notebook under ignored `outputs/`. Keep the HTML as an
offline fallback; widget interaction requires Jupyter. Every full run resets
`outputs/notebook_activities.md` and records setup, processing, evaluation, and results.

Install dependencies or build the Docker image before an offline presentation. The
actual seeded-data pipeline requires neither Internet nor external authentication.
Do not run multiple pipelines against the same SQLite/report paths simultaneously.

## Input Contract

An input directory contains one or more CSVs and optional `receipts.json`. IDs must be
globally unique across bank accounts and files; use anonymized account prefixes.

```csv
transaction_id,date,description,amount,currency,category
accountA-001,2024-01-01T09:00:00Z,Employer Salary,4200.00,USD,income
accountA-002,2024-01-02T11:30:00Z,Fresh Market,-62.25,USD,groceries
accountA-003,2024-01-03T12:00:00Z,Metro Pass,-24.00,USD,transport
```

```json
[
  {
    "transaction_id": "accountA-002",
    "merchant": "Fresh Market",
    "items": [{"name": "Vegetables", "quantity": 2}]
  }
]
```

- Required columns: `transaction_id`, `date`, `description`, `amount`, `currency`.
  Ingestion can accept missing categories, but the supervised experiment needs known
  labels across at least two categories in the earlier training period.
- ISO 8601 timestamps are recommended. Naive timestamps are interpreted as UTC;
  explicitly convert bank-local times when that interpretation would be incorrect.
- Numeric amounts use positive income and negative spending without currency symbols
  or thousands separators. Use one configured currency; there is no FX conversion.
- Duplicate IDs with the same amount/date keep the first record; conflicting amounts
  or dates raise errors. Harmonize other fields in overlapping exports before merging.
- Receipt IDs enrich transactions, not duplicate expenses. Keep one receipt per ID;
  later duplicate receipt entries currently replace earlier entries.
- Use at least 36 complete calendar months for the full forecasting pipeline. Remove
  partial boundary months and verify missing months mean zero activity, not missing files.
- Clean transfers and distinguish refunds manually. Floating-point analytics is not
  an auditable double-entry accounting implementation.
- The optional `is_injected_anomaly` column is a synthetic evaluation label only,
  never a feature. Absence of real anomaly labels does not imply negative ground truth.

For real inputs, use a separate private input **and output** directory:

```bash
finance-demo --input-dir data/private --output-dir outputs/private
```

Never pass `--generate-demo` to a real-data directory. Do not reuse a database between
unrelated datasets: local persistence upserts IDs and does not remove old IDs absent
from a later input set. Use a fresh output directory when changing dataset coverage.
The monthly mart is rebuilt from the supplied full-history input on each run.

## Local Storage, Scale, and Automation

Local directories replace object storage, SQLite JSON replaces remote document access,
and Pandas plus CSV replaces a hosted analytical mart. These are intentionally small,
transparent implementations suited to the project assessment. Inputs are concatenated
in memory; no distributed processing, remote ingestion service, or scale benchmark is claimed.

Use `finance-demo` for repeatable batch processing, or `docker compose run --rm batch`.
For unattended execution, configure your OS scheduler explicitly; nothing is scheduled
automatically. Windows Task Scheduler can run the environment's Python with
`scripts/execute_notebook.py` as its argument and the clone root as **Start in**. A Unix
scheduler can invoke the same script using absolute interpreter/script paths. Both
regenerate synthetic fixtures and export the notebook report. Prevent overlapping runs
and redirect output to a local log. Disable the schedule after the demonstration.

## Reproducibility and Privacy

`config/demo.json` controls seed, years, currency, and horizon. The clean source notebook
and code can be committed, while `data/`, `outputs/`, and environments are ignored.
Notebook edits made in Jupyter can save private outputs into the tracked notebook:
clear outputs before committing, and inspect staged changes. The automated runner
keeps executed results in ignored `outputs/` rather than modifying the source notebook.

The included generated dataset needs no external dataset host. An imported dataset
would need a documented license, provenance, column mapping, consent/privacy review,
and human-reviewed labels. Do not publish real financial records or executed private notebooks.

## Verification

The canonical test command is `python -m pytest -q -W error`. Active tests cover
cleaning, duplicate/currency validation, JSON upserts, full-pipeline exports, unknown-label
inference, chronological holdouts, a forecast leakage invariant, and local-only CLI options.
The clean-kernel execution script is the demonstration integration check.

CI defines Windows/Linux Python verification and Docker batch, notebook execution,
and notebook-server health checks. A workflow definition is not proof of a passing run.
Docker is not installed on the implementation machine, so container runtime behavior
must be checked on a Docker-capable machine before presenting that option.
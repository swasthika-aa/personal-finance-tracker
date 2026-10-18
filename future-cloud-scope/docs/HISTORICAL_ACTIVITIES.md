# Implementation Activity Log

This file records implementation decisions, code responsibilities, setup commands,
and observed validation results. It is also a walkthrough for the project viva.

## 1. Choose the demonstration architecture

- The abstract is the requirements source. The reference `khoros_bridge_demo` is
  an AWS infrastructure demonstration; this project should not copy its service count.
- Jupyter and Python are the primary experience. A local run must work without
  cloud credentials, paid services, or a dataset download.
- Deterministic synthetic bank transactions make the demonstration repeatable and
  avoid committing private financial records. Synthetic results do not establish
  accuracy on real bank data.
- SQLite stores JSON documents for a lightweight local demonstration. SQLite is
  not presented as a distributed NoSQL system; optional Firestore provides that path.
- GCP is optional for cloud storage, NoSQL persistence, analytical warehousing,
  and scheduled batch execution. Kaggle is optional, not a dependency.

## 2. Establish the Python package and ingestion boundary

- `pyproject.toml` declares the installable package, notebook dependencies, optional
  development and GCP dependencies, and the eventual `finance-demo` command.
- `src/finance_tracker/data.py` creates five years of seeded synthetic CSV data and
  receipt JSON. It deliberately includes duplicates, missing descriptions, an invalid
  date, and labelled injected anomalies to make preprocessing visible.
- Ingestion reads CSV files in a supplied directory, normalizes timestamps to UTC,
  validates numeric amounts, rejects conflicting IDs and mixed currencies, removes
  duplicate transaction IDs, fills missing descriptions, and attaches receipt documents.
- The amount convention is positive income and negative spending. The derived
  `expense` column is nonnegative. No automatic exchange-rate conversion is attempted.
- Local persistence uses parameterized SQLite upserts with transaction IDs as keys,
  so repeating an ingestion does not multiply stored documents.
- `.gitignore` excludes generated data, reports, virtual environments, Terraform
  state, and local credential files. Never commit real bank exports or secrets.

## 3. Validate the first implementation slice

- `tests/test_data.py` checks cleaning counts, UTC timestamps, receipt matching,
  nonnegative expenses, idempotent persistence, currency rejection, and conflicting IDs.
- The available command-line interpreter is Python 3.14. This does not establish
  which interpreter VS Code currently selects for its notebook kernel.
- The first environment-install command returned no recorded result. A subsequent
  relative-path environment check failed; setup is being retried with an explicit path.
- Intended setup: `python -m venv .venv`, then install with
  `python -m pip install -e ".[dev,gcp]"` using that environment's Python.
- Validation results will be added below after actual execution; unexecuted checks
  are not treated as passing.

### Observed result

The dependency install was interrupted once and then completed on retry. The two
ingestion tests passed (`2 passed`). No cloud credentials or cloud resources were used.

## 4. Implement analytics and evaluation

- `analytics.py` computes monthly income, expense, net cash flow, savings rate,
  and cumulative net cash flow. The latter is not a bank balance: opening balances,
  transfers, liabilities, and investments are outside this demo's ledger.
- Category classification combines TF-IDF merchant text and training-only standardized
  expense values in a scikit-learn pipeline. The last 20% of time is held out;
  macro F1 is compared with a majority-class baseline and unseen descriptions counted.
- Isolation Forest flags unusual spending using log expense and transaction day.
  Its scaler and detector fit only the earlier period. Synthetic anomaly labels
  are used for evaluation only, never as model features.
- Monthly Ridge forecasts use lagged values and calendar seasonality. A rolling
  12-month backtest refits using only earlier observations and compares MAE with
  last year's same-month spending. Six future months are forecast recursively.
- Forecast shading uses empirical backtest absolute residuals; it is a heuristic
  band, not a calibrated probability interval or financial advice.
- `pipeline.py` shares this workflow between the notebook and command line and
  exports metrics, analytical CSVs, a document database, and a PNG overview.
- Tests now include cash-flow reconciliation, chronological classification, forecast
  outputs, and a leakage check: changing the final actual month must not change
  the backtest predictions that precede observing it.

### Observed result

All five tests passed. A warning-strict rerun found that SQLite's transaction context
does not close its connection. Explicit `contextlib.closing` now closes both production
and test connections. Historical/future chart dates now use the same plotting converter.
The complete five-test suite passes with `-W error` and no warnings.

## 5. Build the central Jupyter demonstration

- `notebooks/finance_demo.ipynb` walks through setup, data quality, EDA, monthly cash
  flow, supervised classification, anomalies, forecasting, interactive filters,
  budget scenarios, nested receipt storage, optional GCP, and study limitations.
- Year/category dropdowns update a spending chart. A budget-reduction slider computes
  hypothetical cash flow against assumed recent income; it is not investment advice.
- Each major notebook activity appends an explanation and observed results to
  `outputs/notebook_activities.md`, with UTC timestamps. This runtime log complements
  this committed implementation log. Restarting the notebook starts a fresh runtime log.
- `ENABLE_GCP = False` ensures Run All cannot provision or contact cloud services.
  Turning it on is an explicit optional action after external setup and authentication.
- `scripts/execute_notebook.py` validates the notebook format, runs a fresh kernel,
  fails on execution errors, and writes an executed notebook plus an HTML report to
  ignored `outputs/`. It never embeds generated results into the committed source notebook.
- The editor notebook execution tool did not return a completion result. The scripted
  clean-kernel execution is the definitive local notebook check.

### Observed result

The clean-kernel script executed all six code cells successfully and generated
`outputs/finance_demo.executed.ipynb` and `outputs/finance_demo.html`. On Windows,
Jupyter emitted an event-loop compatibility warning and a localhost kernel transport
warning; neither prevented execution. Do not expose kernel or Jupyter ports publicly.

## 6. Add optional cloud adapters

- `cloud.py` loads cloud identifiers only from environment variables and uses
  Application Default Credentials, never embedded service-account keys.
- Cloud Storage downloads only flat `raw/*.csv` and `raw/receipts.json` inputs into
  an empty destination. Path traversal and Windows path separators are excluded.
- Reports receive a unique run prefix. SQLite databases are not uploaded.
- Firestore uses stable SHA-256 document IDs and batches of 400 upserts. This
  supports transaction IDs containing slashes and repeatable processing.
- BigQuery receives a typed monthly mart using replace semantics, so repeated runs
  do not accumulate duplicate monthly rows. The example annual query limits billed bytes.
- Cloud publishing is not an atomic transaction across services: a failure can leave
  partial reports or writes. Rerunning repairs upserts and the mart; run-prefix
  reports remain independent snapshots. This is a sandbox batch demonstration.
- Local cloud tests mock client boundaries; passing them does not establish IAM,
  API availability, billing configuration, or deployment success in a real GCP account.

### Observed result

All three mocked cloud-boundary tests passed. The full suite then passed with
`8 passed` and warnings treated as failures. Tests cover slash-containing transaction
IDs, unsafe GCS filenames (including Windows drive-relative names), 400-document
batch boundaries, monthly replacement, and BigQuery query billing limits. If the
optional GCP clients are not installed, the cloud test module skips cleanly.

## 7. Provision portable optional infrastructure

- `infra/terraform/` defines project API enablement, a private GCS bucket, a named
  Firestore database, a BigQuery dataset, an Artifact Registry repository, and separate
  runtime/build/scheduler service accounts and IAM bindings.
- The first apply creates prerequisites only. Build the image with `cloudbuild.yaml`,
  then enable the Cloud Run Job using the built URI in ignored tfvars. This avoids
  attempting to deploy an image before the repository exists.
- Cloud Scheduler is paused unless explicitly enabled. Its OAuth identity has
  invocation permission on this job rather than data-store access.
- The container uses Python 3.14 and a non-root user. The job runs the same Python
  pipeline and exports the same reports as the notebook; there is no second ML implementation.
- Data-deletion settings are protective by default. The cloud guide explains explicit
  opt-in destructive teardown and warns about costs, non-atomic publishing, stale
  Firestore records, overlapping jobs, and full-history input requirements.
- Cloud documentation was checked for the Cloud Run v2 scheduling endpoint and
  nested Terraform job/container field definitions.

### Observed infrastructure validation

Terraform was absent from PATH. An initial PowerShell download failed with a transport
reset and checksum mismatch, so that binary was not used. A bounded curl download
succeeded. Its SHA-256 checksum matched HashiCorp's manifest. Terraform 1.13.5 then
formatted the files, initialized the signed Google provider 7.46.1 locally, and reported
`Success! The configuration is valid.` No plan/apply, GCP account access, or resource
creation was performed. The generated `.terraform.lock.hcl` is portable provider metadata,
not state or credentials. Docker is unavailable; no local container build is claimed.

## 8. Document and verify the demonstration

- `README.md` explains why Jupyter/Python is primary, GCP optional, and Kaggle unnecessary.
  It provides Windows/macOS/Linux setup commands and a source/artifact map.
- `docs/DEMO.md` supplies a viva sequence, bank/receipt data contract, modelling caveats,
  notebook hosting options, privacy rules, and the testing strategy.
- `docs/GCP.md` supplies two-phase deployment, ADC authentication, environment configuration,
  local-Jupyter/cloud integration, scheduling, least-privilege boundaries, and teardown.
- `requirements-lock.txt` captures all observed package versions without editable machine
  paths; Windows-only packages carry platform markers. Python 3.14 is the verified baseline.
- `.github/workflows/validate.yml` defines Windows/Linux tests and notebook execution,
  Terraform validation, and a container build. These CI jobs have not been run here.
- Classification predictions and effective labels are exported separately from recorded
  labels. Missing labels use inference; known labels are not overwritten. Reported model
  metrics still refer only to the chronological holdout, not in-sample CSV predictions.
- The notebook's GCP cell uses a fresh temporary input directory each time so it can
  be rerun without stale files. Its default remains `ENABLE_GCP = False`.
- A mechanical JSON normalization adds the requested `metadata.language` and `metadata.id`
  to all 12 cells. Windows PowerShell initially introduced a UTF-8 BOM; the format check
  caught it, and conversion to BOM-free UTF-8 restored successful `nbformat` validation.
- The overview PNG was inspected: all four charts render with labels and legends.
  `pip check` reports no broken requirements; editor diagnostics report no code errors.

### Observed synthetic results (seed 42, five years)

| Measure | Observed result |
| --- | --- |
| Raw / clean rows | 4,333 / 4,320 |
| Rejected invalid rows / duplicate IDs removed | 1 / 12 |
| Missing descriptions filled / receipts matched | 43 / 1 |
| Category holdout macro F1 / majority baseline | 0.9872 / 0.0549 |
| Unseen merchant descriptions in classification holdout | 0 (important synthetic limitation) |
| Synthetic anomaly holdout precision / recall | 0.0714 / 0.3333 |
| Ridge rolling MAE / seasonal-naive MAE | 364.60 / 413.31 USD |

The anomaly model's precision is weak: unusual legitimate spending is also flagged.
This is an observed limitation to discuss, not a successful fraud-detection claim.
The forecast improves over this baseline on this synthetic sample only. All results
are educational and do not establish accuracy, fairness, or safety on real financial data.

## 9. Final Local Verification

| Check | Result |
| --- | --- |
| `python -m pytest -q -W error` | 8 tests passed, including unknown-category inference |
| `python -m pip check` | No broken requirements |
| `python scripts/execute_notebook.py` | All 6 code cells executed in a fresh kernel; HTML generated |
| Notebook JSON and metadata | 12 cells valid; language/ID metadata present; no source outputs |
| Installed `finance-demo --generate-demo` | Completed end to end; 4,320 clean rows and reports generated |
| Terraform 1.13.5 `init -backend=false` / `validate` | Provider initialized; configuration valid |
| Terraform `fmt -check` | Passed |
| Overview chart inspection | Four nonblank charts with legible labels and legends |
| Editor diagnostics | No code errors reported |
| Git status review | Only intended source/docs/config; generated/private artifacts ignored |

The final notebook execution still prints the documented Windows/Jupyter event-loop
and localhost kernel-transport warnings. They do not prevent the demonstration.
Live GCP execution, Docker image build, hosted notebook compatibility, and the remote
Windows/Linux CI jobs remain unverified here. No commit or cloud deployment was made.
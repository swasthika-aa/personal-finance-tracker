# Demonstration and Data Guide

## Suggested 12-Minute Viva

1. Explain the questions in notebook Cell 1: classification, anomaly review, forecasting.
2. Run the setup cell and inspect the cleaning audit: duplicate removal, missing
   descriptions, invalid-date rejection, nested receipt matching, and UTC timestamps.
3. Show the EDA and reconcile monthly cash flow with transaction amounts. Explain
   that cumulative net cash flow is not the account balance.
4. Compare classification macro F1 with the majority baseline. Read the confusion
   matrix and explain temporal splitting and train-only preprocessing.
5. Review flagged anomalies. Explain why synthetic precision/recall does not establish
   fraud-detection performance or justify automatically blocking a payment.
6. Compare forecast MAE with seasonal naive; acknowledge whichever model wins.
   Explain recursive forecast uncertainty and the deliberately heuristic band.
7. Change the year/category dropdowns and budget reduction slider in the live notebook.
8. Inspect a JSON receipt in SQLite and show the CSV/PNG/HTML reports.
9. Optionally show the deployed GCP job, its execution log, Firestore documents,
   Cloud Storage reports, and the notebook's BigQuery summary.
10. Finish with limitations, ethics, consented real-data validation, and the next experiment.

Prepare by running `python -m pytest -q -W error` and
`python scripts/execute_notebook.py`. Keep the generated HTML report as an offline
fallback. Live widgets are not guaranteed to work in a static export. The notebook
resets its execution Markdown log on a full rerun; implementation history is in
[../ACTIVITIES.md](../ACTIVITIES.md).

## Input Contract

Use an input directory containing one or more bank CSVs and optional `receipts.json`.
Transaction IDs must be globally unique across banks and files; prefix them with an
anonymized account identifier if necessary. Do not use sensitive account numbers.

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

- Required CSV columns: `transaction_id`, `date`, `description`, `amount`, `currency`.
  `category` is optional for ingestion but supervised training needs known labels
  spanning at least two categories in the earlier training period.
- Use ISO 8601 dates. Naive timestamps are interpreted as UTC, not inferred as local
  bank time. Convert bank-local timestamps before ingestion if that is inappropriate.
- Amounts are decimal numbers without thousands separators or currency symbols.
  Negative means spending, positive means income. Currency must match configuration;
  no FX conversion occurs. Floating-point amounts are suitable for this analytics
  demonstration, not an auditable double-entry accounting ledger.
- Conflicting amounts or dates under one ID raise errors. Duplicate IDs with the same
  amount/date keep the first record. Harmonize descriptions/categories before merging
  overlapping exports. Each receipt ID should occur once; later duplicate receipt
  entries currently replace earlier entries.
- All bank CSV rows are concatenated in memory. This is intentionally not a streaming
  ingestion service. Benchmark memory on representative data before claiming scale.
- Use at least 36 complete months for the full pipeline. Remove incomplete boundary
  months and verify missing months mean no activity, not missing exports. Omit transfers,
  distinguish refunds, and review labels before using real records.
- The optional `is_injected_anomaly` column is only a synthetic evaluation label.
  Do not include it as a model feature or interpret absent labels as negatives.

Run a real-input directory without overwriting it:

```bash
finance-demo --input-dir data/private --output-dir outputs/private
```

Do not pass `--generate-demo` for a real-input directory. Generated fixtures are kept
in `data/demo` by default. All `data/` and `outputs/` content is ignored by Git, but
inspect `git status` and staged diffs before committing. Notebook outputs and exported
HTML may contain the input data, so never publish a real-data executed notebook.

## How to Host Jupyter

| Option | Recommendation | Run method |
| --- | --- | --- |
| Local JupyterLab / VS Code | Primary assessed demo; most reproducible | Follow the root README and select `.venv` |
| Local Jupyter with GCP | Best optional cloud demo | Same notebook, ADC and environment variables, then explicitly enable GCP |
| Vertex AI Workbench | Only when a GCP-hosted notebook is required | Create a sandbox instance, clone repo, create an environment, install, select kernel |
| Kaggle / Colab | Optional secondary runtime | Clone repo, install dependencies in its Python runtime, open/copy the notebook and set working directory |

Vertex AI Workbench is deliberately not provisioned by Terraform: a paid notebook VM
is unnecessary for scheduled batch processing. Creating one is a separate explicit
choice. Give its attached identity only the storage/dataset/document permissions it
needs; stop/delete the instance and disks after the demo.

For Kaggle/Colab, cloning and installing requires Internet to be enabled. Managed
runtimes may use an older Python than the verified Python 3.14 snapshot. Install
`pip install -e '.[dev]'` using compatible dependency resolution there instead of
forcing this snapshot onto an incompatible interpreter; restart the kernel after
installing, and rerun validation. Set the working directory to the clone root before
executing cells. Remote hosted runtime compatibility is not verified here.

No Kaggle API token is needed. If using an external dataset, document its URL,
license, provenance, consent/privacy restrictions, column mapping, and label quality.
Do not assume a public financial dataset permits redistribution or has trustworthy labels.

## Testing Strategy

There were no legacy tests or executable implementation in the starting finance folder.
The canonical command is `python -m pytest -q -W error`:

- Unit/boundary tests check cleaning, mixed currencies, duplicate conflicts, and JSON persistence.
- Local integration runs the complete generated-data pipeline and verifies artifacts.
- Time-order tests verify classification boundaries and a forecasting leakage invariant.
- Mocked cloud tests validate input filtering, batching, upserts, mart replacement,
  and query billing configuration. They do not validate actual Google IAM or services.
- `python scripts/execute_notebook.py` runs the entire notebook in a clean kernel
  and exports HTML, serving as the demonstration-level integration gate.
- CI runs Python checks and notebook execution on Windows and Linux, Terraform schema
  validation without credentials, and a container build. CI results must be checked
  on the destination repository; defining a workflow is not evidence it passed.

No custom web frontend or infrastructure integration test requiring Docker was chosen.
Charts and widgets use Jupyter's established UI. Browser interaction, other OS runtimes,
container execution, hosted notebooks, and live cloud deployment require their own
environment checks before a presentation; only actual local results are recorded as verified.
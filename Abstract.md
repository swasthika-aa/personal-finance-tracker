# Multi-Year Personal Finance Tracker and Predictive Visualizer Using Python, Jupyter, and Machine Learning

## Abstract

Understanding long-term financial behavior requires reproducible data preparation,
exploratory analysis, and careful evaluation of predictive models. This bachelor's
data science project implements a local Jupyter-based workflow for multi-year bank
transaction CSVs and receipt JSON. It handles missing descriptions, invalid amounts
and timestamps, duplicate transaction IDs, and single-currency validation; normalizes
dates to UTC; and applies training-only feature scaling within machine-learning pipelines.

Transactions and nested receipt documents are stored locally as JSON in SQLite.
Pandas constructs monthly analytical marts, while Matplotlib and Seaborn visualize
income, expenses, category trends, and cumulative net cash flow. Supervised expense
categorization, unsupervised anomaly review, and lag-based expense forecasting are
evaluated chronologically against explicit baselines. Interactive notebook controls
support category exploration and hypothetical budget scenarios.

## Highlights

- A Jupyter notebook is the central demonstration and research narrative.
- Five years of fixed-seed synthetic transactions support a portable, privacy-safe demo.
- CSV/JSON ingestion, preprocessing audits, and local document persistence are reproducible.
- Monthly cash-flow marts and visualizations reveal category and time-series patterns.
- Classification and forecasting are evaluated against simple baselines without future leakage.
- Local command-line and optional Docker Compose execution share the notebook's Python code.
- Metrics, CSVs, plots, HTML reports, and a Markdown activity log support assessment.

## Approach

1. Ingest full-history bank CSV exports and optional JSON receipts from local directories.
2. Clean and validate records, normalize timestamps, and audit rejected/duplicate rows.
3. Store transaction JSON documents and receipts in a local SQLite database.
4. Aggregate transactions into monthly Pandas analytical marts.
5. Evaluate expense classification, anomaly detection, and monthly expense forecasts.
6. Explore charts, filters, and budget scenarios in Jupyter and export the results.
7. Reproduce the workflow on another machine using pinned Python dependencies or Docker.

## Outcomes and Boundaries

The outcome is an executable, notebook-first personal finance analytics demonstration,
not a production financial ledger. Synthetic results do not establish accuracy on real
bank data. SQLite JSON storage is not a distributed NoSQL service, and Pandas is not
a distributed processing engine. Anomaly flags require human review; forecast bands
are heuristic and do not constitute financial advice.

The original broader abstract is preserved in
[future-cloud-scope/docs/ORIGINAL_ABSTRACT.md](future-cloud-scope/docs/ORIGINAL_ABSTRACT.md).
Future infrastructure ambitions are outside the current assessed implementation.

## Keywords

Personal finance, Python, Jupyter, exploratory data analysis, preprocessing,
time-series analytics, document storage, machine learning, visualization, reproducibility
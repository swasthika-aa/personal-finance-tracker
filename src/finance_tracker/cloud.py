"""Optional Google Cloud adapters; clients use Application Default Credentials."""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def settings() -> dict:
    required = ["GCP_PROJECT_ID", "GCS_BUCKET", "BQ_DATASET", "FIRESTORE_DATABASE"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise ValueError(f"Missing cloud environment variables: {', '.join(missing)}")
    config = {name: os.environ[name] for name in required}
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", config["GCP_PROJECT_ID"]):
        raise ValueError("Expected a standard GCP project ID, not a project number")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,1023}", config["BQ_DATASET"]):
        raise ValueError("Invalid BigQuery dataset identifier")
    return config


def download_inputs(directory: Path) -> int:
    from google.cloud import storage

    config = settings()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise ValueError("Cloud input directory must be empty; use a fresh directory per run")
    client = storage.Client(project=config["GCP_PROJECT_ID"])
    count = 0
    for blob in client.list_blobs(config["GCS_BUCKET"], prefix="raw/"):
        relative = blob.name.removeprefix("raw/")
        if "/" in relative or "\\" in relative or ":" in relative or relative in {"", ".", ".."}:
            continue
        if relative.endswith(".csv") or relative == "receipts.json":
            blob.download_to_filename(str(directory / relative))
            count += 1
    if count == 0:
        raise ValueError("Bucket raw/ prefix has no supported inputs")
    return count


def document_id(transaction_id: str) -> str:
    return hashlib.sha256(transaction_id.encode("utf-8")).hexdigest()


def publish(result: dict, output_dir: Path) -> dict:
    from google.cloud import bigquery, firestore, storage

    config = settings()
    project = config["GCP_PROJECT_ID"]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    bucket = storage.Client(project=project).bucket(config["GCS_BUCKET"])
    published = []
    for path in sorted(Path(output_dir).iterdir()):
        if path.is_file() and path.suffix in {".csv", ".json", ".png", ".html", ".md", ".ipynb"}:
            name = f"reports/{run_id}/{path.name}"
            bucket.blob(name).upload_from_filename(str(path))
            published.append(name)
    documents = json.loads(result["transactions"].to_json(orient="records", date_format="iso"))
    database = firestore.Client(project=project, database=config["FIRESTORE_DATABASE"])
    for offset in range(0, len(documents), 400):
        batch = database.batch()
        for document in documents[offset:offset + 400]:
            reference = database.collection("transactions").document(document_id(document["transaction_id"]))
            batch.set(reference, document)
        batch.commit()
    monthly = result["monthly"].reset_index()
    monthly["date"] = monthly.date.dt.strftime("%Y-%m-%d")
    rows = json.loads(monthly.to_json(orient="records"))
    table = f"{project}.{config['BQ_DATASET']}.monthly"
    schema = [bigquery.SchemaField("date", "DATE"), bigquery.SchemaField("income", "FLOAT"),
              bigquery.SchemaField("expense", "FLOAT"), bigquery.SchemaField("transactions", "INTEGER"),
              bigquery.SchemaField("net_cash_flow", "FLOAT"), bigquery.SchemaField("cumulative_savings", "FLOAT"),
              bigquery.SchemaField("savings_rate", "FLOAT")]
    client = bigquery.Client(project=project)
    job = client.load_table_from_json(rows, table, job_config=bigquery.LoadJobConfig(
        schema=schema, write_disposition="WRITE_TRUNCATE"))
    job.result()
    summary = {"run_id": run_id, "bucket": config["GCS_BUCKET"], "report_objects": published,
               "firestore_documents_upserted": len(documents), "bigquery_table": table}
    print(json.dumps(summary, indent=2))
    return summary


def cloud_summary() -> list[dict]:
    from google.cloud import bigquery

    config = settings()
    table = f"{config['GCP_PROJECT_ID']}.{config['BQ_DATASET']}.monthly"
    client = bigquery.Client(project=config["GCP_PROJECT_ID"])
    query = f"SELECT EXTRACT(YEAR FROM date) AS year, SUM(expense) AS expense, SUM(net_cash_flow) AS net_cash_flow FROM `{table}` GROUP BY year ORDER BY year"
    job = client.query(query, job_config=bigquery.QueryJobConfig(maximum_bytes_billed=100_000_000))
    return [dict(row) for row in job.result()]
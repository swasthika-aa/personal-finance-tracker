"""Synthetic inputs, bank CSV ingestion, receipt JSON, and local document storage."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import numpy as np
import pandas as pd


MERCHANTS = {
    "groceries": ["Fresh Market", "Family Foods", "Green Grocer"],
    "transport": ["Metro Pass", "City Fuel", "Rail Ticket"],
    "dining": ["Corner Cafe", "Pizza Kitchen", "Noodle House"],
    "utilities": ["City Energy", "Home Internet", "Water Board"],
    "entertainment": ["Movie House", "Music Stream", "Book Store"],
}


def generate_demo(directory: Path, seed: int = 42, years: int = 5) -> Path:
    """Create fixed-calendar synthetic data in the explicitly supplied directory."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    rows = []
    for month_index, month in enumerate(pd.date_range("2020-01-01", periods=years * 12, freq="MS")):
        rows.append({"transaction_id": f"salary-{month_index}", "date": month.isoformat(),
                     "description": "Employer Salary", "amount": 4200 + month_index * 12,
                     "category": "income", "currency": "USD"})
        rows.append({"transaction_id": f"rent-{month_index}", "date": (month + pd.Timedelta(days=1)).isoformat(),
                     "description": "Apartment Rent", "amount": -1200 - 25 * (month_index // 12),
                     "category": "housing", "currency": "USD"})
        for purchase in range(70):
            category = str(rng.choice(list(MERCHANTS)))
            base = {"groceries": 50, "transport": 25, "dining": 30, "utilities": 85, "entertainment": 20}[category]
            amount = -round(float(rng.lognormal(np.log(base), 0.35)) * (1 + month_index * 0.003), 2)
            rows.append({"transaction_id": f"purchase-{month_index}-{purchase}",
                         "date": (month + pd.Timedelta(days=int(rng.integers(0, 28)))).isoformat(),
                         "description": str(rng.choice(MERCHANTS[category])), "amount": amount,
                         "category": category, "currency": "USD"})
    frame = pd.DataFrame(rows)
    frame["is_injected_anomaly"] = False
    suspicious = rng.choice(frame.index[frame.amount < 0], size=max(1, years * 3), replace=False)
    frame.loc[suspicious, "amount"] *= 12
    frame.loc[suspicious, "is_injected_anomaly"] = True
    missing = rng.choice(frame.index, size=max(1, len(frame) // 100), replace=False)
    frame.loc[missing, "description"] = None
    frame = pd.concat([frame, frame.iloc[:12]], ignore_index=True)
    invalid = frame.iloc[[0]].copy()
    invalid["transaction_id"] = "invalid-date-example"
    invalid["date"] = "not-a-date"
    frame = pd.concat([frame, invalid], ignore_index=True)
    frame.to_csv(directory / "bank.csv", index=False)
    receipts = [{"transaction_id": "purchase-0-0", "merchant": "Demo receipt", "items": [{"name": "Example item", "quantity": 1}]}]
    (directory / "receipts.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    return directory


def ingest(directory: Path, currency: str = "USD") -> tuple[pd.DataFrame, dict]:
    """Positive amounts are income; negative amounts are expenses, in one currency."""
    files = sorted(Path(directory).glob("*.csv"))
    if not files:
        raise ValueError("No bank CSV files found")
    raw = pd.concat([pd.read_csv(path, dtype={"transaction_id": "string"}) for path in files], ignore_index=True)
    required = {"transaction_id", "date", "description", "amount", "currency"}
    if not required.issubset(raw.columns):
        raise ValueError(f"Missing CSV columns: {sorted(required - set(raw.columns))}")
    raw["date"] = pd.to_datetime(raw["date"], errors="coerce", utc=True, format="mixed")
    raw["amount"] = pd.to_numeric(raw["amount"], errors="coerce")
    invalid = raw["date"].isna() | ~np.isfinite(raw["amount"]) | raw.transaction_id.isna() | raw.transaction_id.str.strip().eq("")
    clean = raw.loc[~invalid].copy()
    if not clean.currency.eq(currency).all():
        raise ValueError("Mixed or unexpected currencies: convert explicitly before ingestion")
    conflicting = clean.groupby("transaction_id").agg({"date": "nunique", "amount": "nunique"})
    if conflicting.gt(1).any().any():
        raise ValueError("Conflicting transactions share an ID")
    duplicates = int(clean.duplicated("transaction_id").sum())
    clean = clean.drop_duplicates("transaction_id").copy()
    missing_descriptions = int(clean.description.isna().sum())
    clean["description"] = clean.description.fillna("Unknown merchant").astype(str)
    if "category" not in clean:
        clean["category"] = "unknown"
    clean["category"] = clean.category.fillna("unknown").astype(str)
    receipts_path = Path(directory) / "receipts.json"
    receipts = json.loads(receipts_path.read_text(encoding="utf-8")) if receipts_path.exists() else []
    receipt_map = {str(item["transaction_id"]): item for item in receipts}
    clean["receipt"] = clean.transaction_id.map(receipt_map)
    clean["expense"] = -clean.amount.clip(upper=0)
    clean = clean.sort_values(["date", "transaction_id"]).reset_index(drop=True)
    audit = {"input_rows": len(raw), "invalid_rows": int(invalid.sum()), "duplicates_removed": duplicates,
             "missing_descriptions_filled": missing_descriptions, "clean_rows": len(clean),
             "receipts_matched": int(clean.receipt.notna().sum())}
    return clean, audit


def store_documents(frame: pd.DataFrame, database: Path) -> int:
    """SQLite stores JSON documents locally; this is not a distributed NoSQL database."""
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    records = json.loads(frame.to_json(orient="records", date_format="iso"))
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("CREATE TABLE IF NOT EXISTS transactions (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        connection.executemany("INSERT OR REPLACE INTO transactions VALUES (?, ?)",
                               [(record["transaction_id"], json.dumps(record)) for record in records])
        return connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
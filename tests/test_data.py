import sqlite3
from contextlib import closing

import pandas as pd
import pytest

from finance_tracker.data import generate_demo, ingest, store_documents


def test_generated_data_cleaning_and_idempotent_storage(tmp_path):
    generate_demo(tmp_path)
    frame, audit = ingest(tmp_path)
    assert len(frame) == 5 * 12 * 72
    assert audit["invalid_rows"] == 1
    assert audit["duplicates_removed"] == 12
    assert audit["receipts_matched"] == 1
    assert frame.description.notna().all()
    assert frame.date.dt.tz is not None
    assert (frame.expense >= 0).all()
    database = tmp_path / "documents.sqlite3"
    assert store_documents(frame, database) == len(frame)
    assert store_documents(frame, database) == len(frame)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT json_extract(payload, '$.currency') FROM transactions LIMIT 1").fetchone()[0] == "USD"


def test_currency_and_conflicting_ids_are_rejected(tmp_path):
    generate_demo(tmp_path, years=1)
    path = tmp_path / "bank.csv"
    raw = pd.read_csv(path)
    raw.loc[0, "currency"] = "EUR"
    raw.to_csv(path, index=False)
    with pytest.raises(ValueError, match="currencies"):
        ingest(tmp_path)
    raw.loc[0, "currency"] = "USD"
    raw.loc[len(raw) - 2, "amount"] = -999999
    raw.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Conflicting"):
        ingest(tmp_path)
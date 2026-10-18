from unittest.mock import MagicMock

import pytest

from finance_tracker.cloud import cloud_summary, document_id, download_inputs, publish, settings
from finance_tracker.data import generate_demo, ingest
from finance_tracker.analytics import monthly_mart


pytest.importorskip("google.cloud.storage")
pytest.importorskip("google.cloud.firestore")
pytest.importorskip("google.cloud.bigquery")


@pytest.fixture
def cloud_env(monkeypatch):
    for name, value in {"GCP_PROJECT_ID": "demo-project-123", "GCS_BUCKET": "test-bucket",
                        "BQ_DATASET": "finance_demo", "FIRESTORE_DATABASE": "finance-demo"}.items():
        monkeypatch.setenv(name, value)


def test_settings_fail_closed(monkeypatch):
    for name in ["GCP_PROJECT_ID", "GCS_BUCKET", "BQ_DATASET", "FIRESTORE_DATABASE"]:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValueError, match="Missing cloud"):
        settings()
    assert document_id("bank/id") == document_id("bank/id")
    assert "/" not in document_id("bank/id")


def test_download_filters_unsafe_paths(tmp_path, cloud_env, monkeypatch):
    from google.cloud import storage

    client = MagicMock()
    valid, unsafe, windows_path, drive_path = MagicMock(), MagicMock(), MagicMock(), MagicMock()
    valid.name, unsafe.name, windows_path.name = "raw/bank.csv", "raw/../escape.csv", "raw/..\\escape.csv"
    drive_path.name = "raw/C:escape.csv"
    client.list_blobs.return_value = [valid, unsafe, windows_path, drive_path]
    monkeypatch.setattr(storage, "Client", lambda **kwargs: client)
    assert download_inputs(tmp_path) == 1
    valid.download_to_filename.assert_called_once()
    unsafe.download_to_filename.assert_not_called()
    windows_path.download_to_filename.assert_not_called()
    drive_path.download_to_filename.assert_not_called()


def test_publish_contract_and_query(tmp_path, cloud_env, monkeypatch):
    from google.cloud import bigquery, firestore, storage

    clients = {"storage": MagicMock(), "firestore": MagicMock(), "bigquery": MagicMock()}
    monkeypatch.setattr(storage, "Client", lambda **kwargs: clients["storage"])
    monkeypatch.setattr(firestore, "Client", lambda **kwargs: clients["firestore"])
    monkeypatch.setattr(bigquery, "Client", lambda **kwargs: clients["bigquery"])
    generate_demo(tmp_path / "input", years=1)
    frame, _ = ingest(tmp_path / "input")
    output = tmp_path / "output"
    output.mkdir()
    (output / "metrics.json").write_text('{}')
    (output / "transactions.sqlite3").write_text('not-uploaded')
    summary = publish({"transactions": frame, "monthly": monthly_mart(frame)}, output)
    assert summary["firestore_documents_upserted"] == 864
    assert len(summary["report_objects"]) == 1
    assert clients["firestore"].batch.return_value.commit.call_count == 3
    load = clients["bigquery"].load_table_from_json.call_args
    assert load.args[1] == "demo-project-123.finance_demo.monthly"
    assert load.kwargs["job_config"].write_disposition == "WRITE_TRUNCATE"
    clients["bigquery"].query.return_value.result.return_value = [{"year": 2020, "expense": 50}]
    assert cloud_summary()[0]["year"] == 2020
    assert clients["bigquery"].query.call_args.kwargs["job_config"].maximum_bytes_billed == 100_000_000
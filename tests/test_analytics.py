import numpy as np
import pandas as pd
import pytest

from finance_tracker.analytics import classify_expenses, forecast_expenses, monthly_mart
from finance_tracker.data import generate_demo, ingest
from finance_tracker.pipeline import run_pipeline


def test_end_to_end_pipeline(tmp_path):
    generate_demo(tmp_path / "input")
    bank_path = tmp_path / "input" / "bank.csv"
    raw = pd.read_csv(bank_path)
    raw.loc[raw.transaction_id.eq("purchase-59-69"), "category"] = None
    raw.to_csv(bank_path, index=False)
    result = run_pipeline(tmp_path / "input", tmp_path / "output")
    assert len(result["monthly"]) == 60
    assert len(result["forecast"]["future"]) == 6
    assert len(result["forecast"]["backtest"]) == 12
    assert np.isfinite(result["forecast"]["future"].to_numpy()).all()
    assert result["classification"]["metrics"]["macro_f1"] > result["classification"]["metrics"]["majority_baseline_macro_f1"]
    assert (tmp_path / "output" / "overview.png").stat().st_size > 1000
    assert (tmp_path / "output" / "categorized_transactions.csv").exists()
    assert result["transactions"].predicted_category.notna().all()
    unlabelled = result["transactions"].set_index("transaction_id").loc["purchase-59-69"]
    assert unlabelled.category == "unknown"
    assert unlabelled.effective_category == unlabelled.predicted_category
    assert unlabelled.effective_category != "unknown"
    assert result["anomalies"]["transactions"].flagged.any()
    monthly = result["monthly"]
    assert monthly.net_cash_flow.sum() == pytest.approx(result["transactions"].amount.sum())


def test_forecast_backtest_cannot_see_future(tmp_path):
    generate_demo(tmp_path)
    frame, _ = ingest(tmp_path)
    monthly = monthly_mart(frame)
    original = forecast_expenses(monthly)
    changed = monthly.copy()
    changed.iloc[-1, changed.columns.get_loc("expense")] *= 100
    repeated = forecast_expenses(changed)
    pd.testing.assert_series_equal(original["backtest"].ridge, repeated["backtest"].ridge)
    with pytest.raises(ValueError, match="36"):
        forecast_expenses(monthly.head(20))


def test_classifier_holdout_is_strictly_later(tmp_path):
    generate_demo(tmp_path)
    frame, _ = ingest(tmp_path)
    result = classify_expenses(frame)
    assert (result["test"].date >= pd.Timestamp(result["metrics"]["cutoff"])).all()
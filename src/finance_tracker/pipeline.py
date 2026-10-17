"""Shared command-line and notebook workflow."""

import argparse
import json
from pathlib import Path

from finance_tracker.analytics import classify_expenses, detect_anomalies, forecast_expenses, monthly_mart, plot_overview
from finance_tracker.data import generate_demo, ingest, store_documents


def run_pipeline(input_dir: Path, output_dir: Path, currency: str = "USD", horizon: int = 6) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame, quality = ingest(input_dir, currency)
    monthly = monthly_mart(frame)
    classification = classify_expenses(frame)
    frame["predicted_category"] = "income"
    expense_mask = frame.amount < 0
    frame.loc[expense_mask, "predicted_category"] = classification["model"].predict(frame.loc[expense_mask])
    frame["effective_category"] = frame.category.where(~frame.category.isin(["unknown", ""]), frame.predicted_category)
    store_documents(frame, output_dir / "transactions.sqlite3")
    anomalies = detect_anomalies(frame)
    forecast = forecast_expenses(monthly, horizon)
    metrics = {"data_quality": quality, "classification": classification["metrics"],
               "anomalies": anomalies["metrics"], "forecast": forecast["metrics"], "currency": currency}
    monthly.to_csv(output_dir / "monthly.csv")
    frame.drop(columns=["receipt"]).to_csv(output_dir / "categorized_transactions.csv", index=False)
    forecast["future"].to_csv(output_dir / "forecast.csv")
    forecast["backtest"].to_csv(output_dir / "forecast_backtest.csv")
    anomalies["transactions"].drop(columns=["receipt"]).to_csv(output_dir / "anomalies.csv", index=False)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False), encoding="utf-8")
    figure = plot_overview(frame, monthly, forecast, output_dir / "overview.png")
    import matplotlib.pyplot as plt

    plt.close(figure)
    return {"transactions": frame, "monthly": monthly, "classification": classification,
            "anomalies": anomalies, "forecast": forecast, "metrics": metrics}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("data/demo"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--generate-demo", action="store_true")
    parser.add_argument("--config", type=Path, default=Path("config/demo.json"))
    parser.add_argument("--cloud", action="store_true", help="Explicitly download from and publish to GCP")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.cloud and args.generate_demo:
        parser.error("Generate synthetic fixtures locally before uploading to cloud storage")
    if args.generate_demo:
        generate_demo(args.input_dir, seed=config["seed"], years=config["years"])
    if args.cloud:
        from finance_tracker.cloud import download_inputs

        download_inputs(args.input_dir)
    result = run_pipeline(args.input_dir, args.output_dir, config["currency"], config["forecast_months"])
    if args.cloud:
        from finance_tracker.cloud import publish

        publish(result, args.output_dir)
    print(json.dumps(result["metrics"], indent=2))


if __name__ == "__main__":
    main()
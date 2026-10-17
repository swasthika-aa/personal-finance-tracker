"""Time-ordered experiments, cash-flow marts, and notebook visualizations."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import classification_report, confusion_matrix, f1_score, mean_absolute_error, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def monthly_mart(frame: pd.DataFrame) -> pd.DataFrame:
    indexed = frame.set_index("date").sort_index()
    monthly = indexed.resample("MS").agg(income=("amount", lambda values: values.clip(lower=0).sum()),
                                          expense=("expense", "sum"), transactions=("amount", "size"))
    monthly["net_cash_flow"] = monthly.income - monthly.expense
    monthly["cumulative_savings"] = monthly.net_cash_flow.cumsum()
    monthly["savings_rate"] = monthly.net_cash_flow.div(monthly.income.replace(0, np.nan))
    return monthly


def classify_expenses(frame: pd.DataFrame) -> dict:
    labelled = frame.loc[(frame.amount < 0) & ~frame.category.isin(["unknown", "", "income"])].copy()
    if labelled.empty:
        raise ValueError("Classification needs historically labelled expenses")
    cutoff = labelled.date.quantile(0.8)
    train = labelled.loc[labelled.date < cutoff]
    test = labelled.loc[labelled.date >= cutoff]
    if train.category.nunique() < 2 or test.empty:
        raise ValueError("Classification needs at least two training categories and a later holdout")
    model = Pipeline([
        ("features", ColumnTransformer([
            ("merchant", TfidfVectorizer(ngram_range=(1, 2)), "description"),
            ("amount", StandardScaler(), ["expense"]),
        ])),
        ("classifier", LogisticRegression(max_iter=1500, random_state=42)),
    ])
    model.fit(train, train.category)
    predictions = model.predict(test)
    labels = sorted(set(train.category) | set(test.category))
    majority = train.category.mode().iloc[0]
    return {
        "model": model, "test": test, "predictions": predictions, "labels": labels,
        "confusion": confusion_matrix(test.category, predictions, labels=labels),
        "report": classification_report(test.category, predictions, zero_division=0, output_dict=True),
        "metrics": {"macro_f1": float(f1_score(test.category, predictions, average="macro", zero_division=0)),
                    "majority_baseline_macro_f1": float(f1_score(test.category, [majority] * len(test), average="macro", zero_division=0)),
                    "train_rows": len(train), "test_rows": len(test), "cutoff": cutoff.isoformat(),
                    "unseen_test_descriptions": int((~test.description.isin(train.description)).sum())},
    }


def detect_anomalies(frame: pd.DataFrame) -> dict:
    expenses = frame.loc[frame.expense > 0].copy()
    if len(expenses) < 20:
        raise ValueError("Anomaly detection needs at least 20 expenses")
    cutoff = expenses.date.quantile(0.8)
    train_mask = expenses.date < cutoff
    features = pd.DataFrame({"log_expense": np.log1p(expenses.expense), "day": expenses.date.dt.day}, index=expenses.index)
    model = Pipeline([("scale", StandardScaler()),
                      ("detector", IsolationForest(contamination=0.015, random_state=42, n_estimators=150))])
    model.fit(features.loc[train_mask])
    expenses["anomaly_score"] = -model.decision_function(features)
    expenses["flagged"] = model.predict(features) == -1
    expenses["evaluation_holdout"] = ~train_mask
    metrics = {"flagged_count": int(expenses.flagged.sum()), "cutoff": cutoff.isoformat()}
    if "is_injected_anomaly" in expenses:
        holdout = expenses.loc[~train_mask]
        truth = holdout.is_injected_anomaly.astype(str).str.lower().eq("true")
        metrics.update({"synthetic_holdout_precision": float(precision_score(truth, holdout.flagged, zero_division=0)),
                        "synthetic_holdout_recall": float(recall_score(truth, holdout.flagged, zero_division=0)),
                        "synthetic_holdout_anomalies": int(truth.sum())})
    return {"model": model, "transactions": expenses, "metrics": metrics}


def _forecast_features(history: list[float], month: int) -> list[float]:
    return [history[-1], float(np.mean(history[-3:])), history[-12],
            float(np.sin(2 * np.pi * month / 12)), float(np.cos(2 * np.pi * month / 12))]


def forecast_expenses(monthly: pd.DataFrame, horizon: int = 6) -> dict:
    if len(monthly) < 36:
        raise ValueError("Forecasting needs at least 36 complete calendar months")
    if not 1 <= horizon <= 24:
        raise ValueError("Forecast horizon must be between 1 and 24 months")
    values = monthly.expense.to_numpy(dtype=float)
    features = np.array([_forecast_features(values[:position].tolist(), monthly.index[position].month)
                         for position in range(12, len(values))])
    targets = values[12:]
    backtest_rows = []
    model = Pipeline([("scale", StandardScaler()), ("regressor", Ridge(alpha=10))])
    for position in range(len(targets) - 12, len(targets)):
        model.fit(features[:position], targets[:position])
        prediction = max(0.0, float(model.predict(features[position:position + 1])[0]))
        calendar_position = position + 12
        backtest_rows.append({"date": monthly.index[calendar_position], "actual": targets[position],
                              "ridge": prediction, "seasonal_baseline": values[calendar_position - 12]})
    backtest = pd.DataFrame(backtest_rows).set_index("date")
    residual_size = float(np.quantile(np.abs(backtest.actual - backtest.ridge), 0.9))
    model.fit(features, targets)
    history = values.tolist()
    future_rows = []
    future_dates = pd.date_range(monthly.index[-1] + pd.offsets.MonthBegin(), periods=horizon, freq="MS")
    for date in future_dates:
        prediction = max(0.0, float(model.predict([_forecast_features(history, date.month)])[0]))
        future_rows.append({"date": date, "predicted_expense": prediction,
                            "lower_heuristic": max(0.0, prediction - residual_size),
                            "upper_heuristic": prediction + residual_size})
        history.append(prediction)
    return {"model": model, "backtest": backtest, "future": pd.DataFrame(future_rows).set_index("date"),
            "metrics": {"ridge_mae": float(mean_absolute_error(backtest.actual, backtest.ridge)),
                        "seasonal_baseline_mae": float(mean_absolute_error(backtest.actual, backtest.seasonal_baseline)),
                        "backtest_months": len(backtest), "horizon_months": horizon,
                        "heuristic_residual_band": residual_size}}


def plot_overview(frame: pd.DataFrame, monthly: pd.DataFrame, forecast: dict, output=None):
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", palette="colorblind")
    figure, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    monthly[["income", "expense"]].plot(ax=axes[0, 0], title="Monthly income and expenses")
    frame.groupby("category").expense.sum().sort_values().plot.barh(ax=axes[0, 1], title="Spending by recorded category")
    monthly.cumulative_savings.plot(ax=axes[1, 0], title="Cumulative net cash flow (not account balance)")
    observed = monthly.expense.tail(18)
    axes[1, 1].plot(observed.index, observed.to_numpy(), label="Observed")
    future = forecast["future"]
    axes[1, 1].plot(future.index, future.predicted_expense, label="Ridge forecast")
    axes[1, 1].fill_between(future.index, future.lower_heuristic, future.upper_heuristic, alpha=0.2, label="Heuristic residual band")
    axes[1, 1].set_title("Expense outlook; band is not a calibrated interval")
    axes[1, 1].legend()
    for axis in axes.flat:
        axis.set_ylabel("Amount (single configured currency)")
    if output is not None:
        figure.savefig(output, dpi=140, bbox_inches="tight")
    return figure
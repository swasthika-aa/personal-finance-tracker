# Historical Notebook Integration

This is the cloud-specific notebook code removed from the active demonstration.
It is preserved as reference only. It assumes the old `finance_tracker.cloud`
module, external resources, ADC authentication, environment variables, and the earlier
notebook's local variables. None of those integrations are enabled by the current package.
Do not paste or run this in the local assessed demo without a separately validated future integration.

```python
import tempfile
from pathlib import Path

ENABLE_GCP = False
if ENABLE_GCP:
    from finance_tracker.cloud import cloud_summary, download_inputs, publish

    with tempfile.TemporaryDirectory(prefix="finance-cloud-") as temporary:
        cloud_input = Path(temporary)
        download_inputs(cloud_input)
        cloud_results = run_pipeline(
            cloud_input, OUTPUT / "cloud", CONFIG["currency"], CONFIG["forecast_months"]
        )
        published = publish(cloud_results, OUTPUT / "cloud")
    display(published)
    display(cloud_summary())
    record_activity(
        "GCP demonstration",
        "Read bucket inputs, ran pipeline, published reports/documents/mart, and queried BigQuery.",
        str(published),
    )
```

The active notebook instead inspects receipt JSON and monthly aggregates from SQLite.
See [archive status](../README.md) for the full local replacement map.
# Future Cloud Scope (Inactive Archive)

This folder preserves the previous GCP design for future study. It is **not part of
the installed Python package, active tests, CI, Docker build context, or notebook demo**.
The supported project now runs entirely on a local machine or through Docker Compose.

## Preserved Material

- `infra/terraform/`: original infrastructure and provider lock for Storage, Firestore,
  BigQuery, Artifact Registry, Cloud Run, Scheduler, and IAM.
- `src/finance_tracker/cloud.py` and `tests/test_cloud.py`: original Google client
  adapters and mocked boundary tests; these are reference code, not active modules.
- `Dockerfile`, `cloudbuild.yaml`, `.gcloudignore`, and `.github/workflows/validate.yml`:
  original cloud deployment/build definitions and CI, retained outside active locations.
- `requirements-lock.txt`: original dependency snapshot including Google SDKs.
- `requirements-gcp.txt`: the former optional GCP dependency declarations, reference only.
- `docs/GCP.md`: historical deployment instructions, no longer a supported runbook.
- `docs/NOTEBOOK_INTEGRATION.md`: the removed cloud notebook integration, reference only.
- `docs/ORIGINAL_README.md`, `docs/ORIGINAL_DEMO.md`, and
  `docs/HISTORICAL_ACTIVITIES.md`: the earlier cloud-facing guides and activity history.
- `docs/ORIGINAL_ABSTRACT.md`: the supplied abstract before narrowing the current scope.

These files describe the **old repository layout**. Commands referencing the old root
Dockerfile, cloud extras, CLI `--cloud` flag, or `infra/terraform` path will not work
against the current local-only package. Do not run an archived deployment command
without explicitly restoring and testing a cloud integration in a separate future task.
No service account, API, billing setup, Kaggle account, or credentials are needed now.

## Local Replacements

| Previous cloud responsibility | Current supported implementation |
| --- | --- |
| Cloud Storage inputs and reports | Ignored local `data/` and `outputs/` directories |
| Firestore transaction documents | SQLite JSON documents with stable transaction-ID upserts |
| BigQuery monthly analytical mart | Pandas aggregation and `outputs/monthly.csv` |
| Cloud Run batch processing | `finance-demo` locally or `docker compose run --rm batch` |
| Cloud-hosted notebook | Local JupyterLab or the Compose notebook service |
| Cloud Scheduler | Explicit repeatable CLI invocation; optional OS scheduling |
| Cloud Logging | Console output, metrics JSON, and notebook Markdown execution log |
| Artifact Registry / Cloud Build | Local image built using `docker compose build` |

SQLite is a local document-storage demonstration, not a distributed NoSQL service.
Pandas is in-memory processing, not a distributed big-data engine. These limitations
remain explicit in the active abstract and demonstration.

## Future Reintroduction

If cloud work becomes appropriate later, reintroduce optional SDK dependencies,
package the adapters, add a separate cloud entry point, update infrastructure paths,
and validate authentication, IAM, cost controls, container execution, and cleanup in
a sandbox account. Do not silently reconnect the assessed local notebook to paid services.

See the active [project guide](../README.md) and [Docker guide](../docs/DOCKER.md).
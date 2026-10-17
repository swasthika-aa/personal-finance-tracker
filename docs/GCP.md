# Optional GCP Deployment

The local notebook is complete without this extension. Use a dedicated **billing-enabled
sandbox project**, synthetic inputs, and a reviewed budget. No resources are provisioned
by running the default notebook. There are no account-specific project IDs, keys,
bucket names, or principals committed to the implementation.

## Services and Responsibilities

| Service | Demonstration purpose |
| --- | --- |
| Cloud Storage | Bank CSV/receipt landing area and versioned-by-run report paths |
| Firestore Native | Actual NoSQL transaction documents and nested receipt payloads |
| BigQuery | Typed monthly analytical mart and notebook SQL summary |
| Artifact Registry | Batch container images |
| Cloud Build | Remote image build, without local Docker |
| Cloud Run Job | On-demand execution of the same Python pipeline as Jupyter |
| Cloud Scheduler | Optional daily invocation; provisioned paused by default |
| IAM | Separate runtime, builder, and scheduler identities without downloaded keys |
| Cloud Logging | Built-in job/build/scheduler logs; metrics contain no bank rows |

There is no public web endpoint, notebook server, VPC/NAT gateway, Kubernetes cluster,
or permanently running application service. Workbench is an optional manual notebook
hosting choice, not a prerequisite.

## Prerequisites and Permissions

Install Google Cloud CLI and Terraform 1.6+ (or use Google Cloud Shell, which avoids
Windows shell differences). The commands below use **Bash in Cloud Shell** from the
cloned repository root. Install Python dependencies there if generating fixtures there;
otherwise upload already generated synthetic fixtures from your local machine.

Use an isolated project where you are authorized to enable APIs, create resources,
manage their IAM, build images, and act as the three created service accounts. A sandbox
project Owner can perform setup, but do not give Owner to runtime/build/scheduler identities.
In an organization, ask an administrator for the required service-specific administration
roles, Service Usage Admin, IAM service-account administration, project IAM management,
and service-account `actAs`. Organization policies may prohibit parts of this setup.

Authenticate interactively yourself; never paste tokens into chat or commit credentials:

```bash
gcloud auth login
gcloud auth application-default login
export PROJECT="your-sandbox-project-id"
export REGION="us-central1"
gcloud config set project "$PROJECT"
gcloud auth application-default set-quota-project "$PROJECT"
gcloud services enable serviceusage.googleapis.com cloudresourcemanager.googleapis.com --project "$PROJECT"
```

Cloud Shell often already has CLI authentication, but Terraform and local client
libraries still need usable ADC. Never use a production project for this demo.

## Phase 1: Provision Storage and Build Prerequisites

```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
```

Edit the ignored `terraform.tfvars`: set `project_id`, choose a common supported region,
and retain `deploy_job = false`, `schedule_enabled = false`, and
`allow_data_destroy = false`. Names must be unused in that project. Bucket names
incorporate the project ID to make deployments portable across accounts. This Terraform
creates a new **named** Firestore database, not `(default)`; import an existing resource
explicitly if reusing one. Region changes for existing databases/buckets can require replacement.

```bash
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
terraform -chdir=infra/terraform plan
terraform -chdir=infra/terraform apply
export BUCKET=$(terraform -chdir=infra/terraform output -raw bucket)
export BUILDER=$(terraform -chdir=infra/terraform output -raw builder_service_account)
export IMAGE_BASE=$(terraform -chdir=infra/terraform output -raw image_base)
export IMAGE="$IMAGE_BASE:demo-v1"
```

Review the plan before accepting. This first phase deliberately creates no executable
Cloud Run job referencing a nonexistent image. Enabling APIs may need propagation time;
if GCP returns a transient API/IAM propagation error, investigate it before retrying.

## Phase 2: Build, Upload Inputs, and Deploy the Job

From the project root, build with the explicitly configured builder identity:

```bash
gcloud builds submit . --project "$PROJECT" --region "$REGION" --config cloudbuild.yaml --substitutions "_IMAGE=$IMAGE" --service-account "projects/$PROJECT/serviceAccounts/$BUILDER" --gcs-source-staging-dir "gs://$BUCKET/build/source"
```

Cloud Build builds as Linux amd64 using Python 3.14. The runtime is a non-root container.
Build source excludes local data, outputs, environments, credentials, and Terraform.
For an immutable deployment, resolve the pushed image digest and use `image@sha256:...`
instead of a mutable tag. Rebuild with a new tag/digest when code/configuration changes.

Generate and upload fixtures on the machine with the installed package:

```bash
finance-demo --generate-demo
gcloud storage cp data/demo/bank.csv data/demo/receipts.json "gs://$BUCKET/raw/"
```

The entire bank history must be present under `raw/` on each run. Files must follow the
data contract in [DEMO.md](DEMO.md), with global unique transaction IDs. Do not upload
partial incremental history: the BigQuery monthly table is replaced from the current
input set. For this demo, use one account/dataset; do not mix unrelated users.

Edit the same ignored `terraform.tfvars` to set `deploy_job = true` and `image` to
the built URI. Keep those values in the file for later applies/destroy operations;
using temporary command-line flags and then omitting them can inadvertently remove a job.

```bash
terraform -chdir=infra/terraform plan
terraform -chdir=infra/terraform apply
export JOB=$(terraform -chdir=infra/terraform output -raw job_name)
gcloud run jobs execute "$JOB" --project "$PROJECT" --region "$REGION" --wait
gcloud logging read 'resource.type="cloud_run_job"' --project "$PROJECT" --limit 15
gcloud storage ls "gs://$BUCKET/reports/"
```

Inspect the execution's success status, metrics log, reports, named Firestore database,
and BigQuery `finance_demo.monthly` table before calling deployment verified.

The job has a 900-second limit, one task, one CPU, 1 GiB memory, and one retry.
This is sized for the small demonstration, not millions of bank records. Avoid overlapping
manual executions: the monthly mart uses last-writer-wins replacement, and publishing
across GCS/Firestore/BigQuery is not atomic. Firestore upserts do not delete old records
removed from a later input set; reset the sandbox database explicitly when changing datasets.

## Demonstrate GCP from Jupyter

Keep Jupyter on your local machine. Install `.[gcp]`, authenticate with ADC there,
and set the environment **before launching Jupyter**. Obtain exact values with:

```bash
terraform -chdir=infra/terraform output -json notebook_environment
```

Bash example:

```bash
export GCP_PROJECT_ID="your-sandbox-project-id"
export GCS_BUCKET="your-sandbox-project-id-finance-demo-data"
export FIRESTORE_DATABASE="finance-demo"
export BQ_DATASET="finance_demo"
python -m jupyterlab notebooks/finance_demo.ipynb
```

PowerShell example, after running the root README's environment setup:

```powershell
$env:GCP_PROJECT_ID = 'your-sandbox-project-id'
$env:GCS_BUCKET = 'your-sandbox-project-id-finance-demo-data'
$env:FIRESTORE_DATABASE = 'finance-demo'
$env:BQ_DATASET = 'finance_demo'
.\.venv\Scripts\python.exe -m jupyterlab notebooks/finance_demo.ipynb
```

Use the actual Terraform outputs if you changed resource names. The interactive user's
ADC needs bucket access, Firestore read/write, BigQuery job creation and dataset access.
Do not solve permission errors by downloading a runtime service-account key.

Change `ENABLE_GCP` to `True` in the notebook's storage cell. That cell downloads raw
inputs into an empty temporary directory, runs the same pipeline, publishes reports,
upserts Firestore documents, replaces the mart, and queries annual BigQuery totals.
It does not provision resources or trigger the deployed job; show the Cloud Run execution
separately using the command above. Restore `False` before committing the notebook.

For a cloud-only notebook, manually create a Vertex AI Workbench instance, attach an
appropriately authorized service identity, clone this repository and install it in an
isolated kernel. Workbench instance and disk costs are additional. No Kaggle account is needed.

## Schedule, Costs, Security, and Cleanup

Scheduler is paused by default. To enable recurring processing, set
`schedule_enabled = true` in your tfvars and review/apply the change. It invokes the
Cloud Run v2 `:run` API using OAuth and a job-scoped Run Invoker identity at 06:00 UTC.
Scheduler confirms job submission, not successful completion; inspect Cloud Run execution
status. Replaying a full five-year dataset incurs Firestore writes each time, even on upsert.

- There is no guaranteed free deployment: Cloud Build, Cloud Run execution, Scheduler,
  Artifact Registry images, GCS storage/operations, Firestore writes/storage and BigQuery
  queries/storage can all be billable. Set budgets/alerts; budgets do not enforce a cap.
- The example BigQuery summary caps billed query bytes, but arbitrary user queries may
  not. Report/build GCS objects have a 30-day deletion rule. Raw inputs are retained.
- Runtime has bucket-scoped object administration, dataset-scoped BigQuery data editing,
  project-scoped BigQuery job creation and Firestore data access. Firestore access is
  broader than a single collection; this is why a dedicated sandbox project is required.
- Builder can access this bucket, write this image repository and send logs. Scheduler
  can only invoke this job. No service-account keys are created or exported.
- This is not a production financial system: no multi-tenant isolation, KMS policy,
  DLP, audit-ledger guarantees, backup plan, drift monitoring, or regulatory certification.

For teardown, first set `schedule_enabled = false` and apply. Back up any needed reports.
The bucket, BigQuery contents and Firestore database are protected against destructive
cleanup by default. For disposable synthetic data only, set `allow_data_destroy = true`,
review and apply it to disable Firestore deletion protection, then:

```bash
terraform -chdir=infra/terraform plan -destroy
terraform -chdir=infra/terraform destroy
```

This permanently removes managed demo data and images. APIs stay enabled deliberately;
the existing GCP project and billing account are not created or deleted. Verify resource
cleanup in the console, including any manually created Workbench instance/disks. Terraform
state is ignored and should be protected; another account must create its own state and
resources, never reuse an unrelated account's state.

## Validation Status

Local Python, notebook execution, and mocked cloud-client behavior were checked during
implementation. Terraform 1.13.5 was downloaded into a temporary directory after an initial
connection-reset failure; its SHA-256 checksum was verified. Formatting, local provider
initialization with Google provider 7.46.1, and `terraform validate` passed without cloud
credentials. The provider lock file is committed for reproducible selection.
No GCP project was deployed or billed. Docker is unavailable locally, so container build
and live service/IAM behavior remain unverified. Check the included CI gates and execute
the explicit deployment steps above in your own sandbox before a cloud presentation.

References: [Cloud Run scheduled jobs](https://docs.cloud.google.com/run/docs/execute/jobs-on-schedule)
and [Terraform Cloud Run v2 Job](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_job).
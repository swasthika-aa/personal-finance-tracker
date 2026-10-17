terraform {
  required_version = ">= 1.6, < 2.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0, < 8.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "apis" {
  for_each = toset([
    "serviceusage.googleapis.com", "cloudresourcemanager.googleapis.com", "iam.googleapis.com", "run.googleapis.com",
    "storage.googleapis.com", "firestore.googleapis.com", "bigquery.googleapis.com",
    "artifactregistry.googleapis.com", "cloudbuild.googleapis.com",
    "cloudscheduler.googleapis.com", "logging.googleapis.com"
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "google_storage_bucket" "data" {
  name                        = "${var.project_id}-${var.name}-data"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.allow_data_destroy
  lifecycle_rule {
    condition {
      age            = 30
      matches_prefix = ["reports/", "build/"]
    }
    action {
      type = "Delete"
    }
  }
  depends_on = [google_project_service.apis]
}

resource "google_firestore_database" "documents" {
  name                    = var.name
  location_id             = var.region
  type                    = "FIRESTORE_NATIVE"
  deletion_policy         = "DELETE"
  delete_protection_state = var.allow_data_destroy ? "DELETE_PROTECTION_DISABLED" : "DELETE_PROTECTION_ENABLED"
  depends_on              = [google_project_service.apis]
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id                 = var.dataset_id
  location                   = var.region
  delete_contents_on_destroy = var.allow_data_destroy
  depends_on                 = [google_project_service.apis]
}

resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = var.name
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

resource "google_service_account" "runtime" {
  account_id   = "${var.name}-runtime"
  display_name = "Finance analytics batch runtime"
  depends_on   = [google_project_service.apis]
}

resource "google_service_account" "scheduler" {
  account_id   = "${var.name}-schedule"
  display_name = "Finance job invocation only"
  depends_on   = [google_project_service.apis]
}

resource "google_service_account" "builder" {
  account_id   = "${var.name}-builder"
  display_name = "Finance container build identity"
  depends_on   = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "objects" {
  for_each = {
    runtime = google_service_account.runtime.email
    builder = google_service_account.builder.email
  }
  bucket = google_storage_bucket.data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${each.value}"
}

resource "google_project_iam_member" "runtime" {
  for_each = toset(["roles/datastore.user", "roles/bigquery.jobUser"])
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_bigquery_dataset_iam_member" "runtime" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_artifact_registry_repository_iam_member" "builder" {
  location   = var.region
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.builder.email}"
}

resource "google_project_iam_member" "builder_logs" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.builder.email}"
}

resource "google_cloud_run_v2_job" "pipeline" {
  count               = var.deploy_job ? 1 : 0
  name                = var.name
  location            = var.region
  deletion_protection = false
  template {
    task_count  = 1
    parallelism = 1
    template {
      service_account = google_service_account.runtime.email
      timeout         = "900s"
      max_retries     = 1
      containers {
        image = var.image
        args  = ["--cloud", "--input-dir", "/tmp/finance-input", "--output-dir", "/tmp/finance-output", "--config", "/app/config/demo.json"]
        resources {
          limits = { cpu = "1", memory = "1Gi" }
        }
        dynamic "env" {
          for_each = {
            GCP_PROJECT_ID     = var.project_id
            GCS_BUCKET         = google_storage_bucket.data.name
            FIRESTORE_DATABASE = google_firestore_database.documents.name
            BQ_DATASET         = google_bigquery_dataset.analytics.dataset_id
            MPLBACKEND         = "Agg"
          }
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }
  lifecycle {
    precondition {
      condition     = !var.deploy_job || length(var.image) > 0
      error_message = "Build and supply an image before enabling deploy_job."
    }
  }
  depends_on = [google_project_iam_member.runtime, google_storage_bucket_iam_member.objects, google_bigquery_dataset_iam_member.runtime]
}

resource "google_cloud_run_v2_job_iam_member" "scheduler" {
  count    = var.deploy_job ? 1 : 0
  location = var.region
  name     = google_cloud_run_v2_job.pipeline[0].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_cloud_scheduler_job" "pipeline" {
  count     = var.deploy_job ? 1 : 0
  name      = "${var.name}-daily"
  region    = var.region
  schedule  = "0 6 * * *"
  time_zone = "Etc/UTC"
  paused    = !var.schedule_enabled
  http_target {
    uri         = "https://run.googleapis.com/v2/${google_cloud_run_v2_job.pipeline[0].id}:run"
    http_method = "POST"
    body        = base64encode("{}")
    headers     = { "Content-Type" = "application/json" }
    oauth_token {
      service_account_email = google_service_account.scheduler.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
  depends_on = [google_cloud_run_v2_job_iam_member.scheduler]
}
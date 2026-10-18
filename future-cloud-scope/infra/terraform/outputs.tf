output "bucket" {
  value = google_storage_bucket.data.name
}

output "image_base" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${var.name}/pipeline"
}

output "builder_service_account" {
  value = google_service_account.builder.email
}

output "runtime_service_account" {
  value = google_service_account.runtime.email
}

output "notebook_environment" {
  value = {
    GCP_PROJECT_ID     = var.project_id
    GCS_BUCKET         = google_storage_bucket.data.name
    FIRESTORE_DATABASE = google_firestore_database.documents.name
    BQ_DATASET         = google_bigquery_dataset.analytics.dataset_id
  }
}

output "job_name" {
  value = var.deploy_job ? google_cloud_run_v2_job.pipeline[0].name : null
}
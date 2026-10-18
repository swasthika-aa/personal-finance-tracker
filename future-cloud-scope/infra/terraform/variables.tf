variable "project_id" {
  description = "Existing billing-enabled sandbox GCP project ID; never a project number."
  type        = string
}

variable "region" {
  description = "Region supported by Cloud Run, Scheduler, Firestore and BigQuery."
  type        = string
  default     = "us-central1"
}

variable "name" {
  description = "Unique prefix within the project and named Firestore database ID."
  type        = string
  default     = "finance-demo"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{3,17}$", var.name))
    error_message = "Use 4-18 lowercase letters, digits or hyphens, starting with a letter."
  }
}

variable "dataset_id" {
  type    = string
  default = "finance_demo"
  validation {
    condition     = can(regex("^[A-Za-z_][A-Za-z0-9_]*$", var.dataset_id))
    error_message = "Use a valid BigQuery dataset ID."
  }
}

variable "deploy_job" {
  description = "False for storage/repository bootstrap; true only after pushing the image."
  type        = bool
  default     = false
}

variable "image" {
  description = "Built Artifact Registry image URI, preferably pinned by digest."
  type        = string
  default     = ""
}

variable "schedule_enabled" {
  description = "Explicitly opt into daily executions and recurring charges."
  type        = bool
  default     = false
}

variable "allow_data_destroy" {
  description = "Allow deleting bucket contents, Firestore database and BigQuery tables during teardown."
  type        = bool
  default     = false
}
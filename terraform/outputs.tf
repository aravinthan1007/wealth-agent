output "cloud_run_url" {
  description = "Aurelius Agent Cloud Run service URL"
  value       = google_cloud_run_v2_service.aurelius.uri
}

output "cloud_run_service_name" {
  description = "Cloud Run service name"
  value       = google_cloud_run_v2_service.aurelius.name
}

output "artifact_registry_url" {
  description = "Artifact Registry URL for pushing images"
  value       = google_artifact_registry_repository.aurelius.repository_url
}

output "service_account_email" {
  description = "Service account for Cloud Run"
  value       = google_service_account.aurelius.email
}

output "deployment_info" {
  description = "Deployment information"
  value = {
    region            = var.region
    project_id        = var.project_id
    service_url       = google_cloud_run_v2_service.aurelius.uri
    service_account   = google_service_account.aurelius.email
    artifact_registry = google_artifact_registry_repository.aurelius.repository_url
    memory_mb         = var.memory
    cpu               = var.cpu
    max_instances     = var.max_instances
    model             = "gemini-3.1-pro-preview"
    tier              = "3-cloud"
  }
}

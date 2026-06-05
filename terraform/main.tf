# Tier 3: Terraform configuration for Aurelius Cloud Run deployment
# Pattern: Cloud Run + Artifact Registry + Secret Manager
# Usage: terraform init && terraform plan && terraform apply

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --- Artifact Registry (for container images) ---

resource "google_artifact_registry_repository" "aurelius" {
  location      = var.region
  repository_id = "aurelius-agent"
  description   = "Container registry for Aurelius Agent"
  format        = "DOCKER"
}

# --- Secret Manager (for Phoenix API key) ---

resource "google_secret_manager_secret" "phoenix_api_key" {
  secret_id = "aurelius-phoenix-api-key"
  labels = {
    environment = var.environment
    service     = "aurelius-agent"
  }
}

resource "google_secret_manager_secret_version" "phoenix_api_key" {
  count           = var.phoenix_api_key != "" ? 1 : 0
  secret          = google_secret_manager_secret.phoenix_api_key.id
  secret_data     = var.phoenix_api_key
  deletion_policy = "DELETE"
}

# --- Service Account ---

resource "google_service_account" "aurelius" {
  account_id   = "aurelius-agent"
  display_name = "Aurelius Agent Service Account"
  description  = "Service account for Cloud Run deployment"
}

# IAM: Cloud Run service account can invoke itself
resource "google_project_iam_member" "run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.aurelius.email}"
}

# IAM: Access to Vertex AI (for LlmAgent)
resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.aurelius.email}"
}

# IAM: Access to Secret Manager
resource "google_secret_manager_iam_member" "phoenix_secret_accessor" {
  secret_id = google_secret_manager_secret.phoenix_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.aurelius.email}"
}

# --- Cloud Run Service ---

resource "google_cloud_run_v2_service" "aurelius" {
  name        = var.service_name
  location    = var.region
  description = "Aurelius Wealth Management Agent (Tier 3)"
  protocol    = "http2"

  template {
    spec {
      service_account = google_service_account.aurelius.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.aurelius.repository_id}/${var.image_name}:latest"

        ports {
          container_port = 8000
        }

        # Environment variables
        env {
          name  = "PORT"
          value = "8000"
        }

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }

        env {
          name  = "GOOGLE_CLOUD_LOCATION"
          value = var.region
        }

        env {
          name  = "GOOGLE_GENAI_USE_VERTEXAI"
          value = "true"
        }

        env {
          name  = "MODEL"
          value = "gemini-3.1-pro-preview"
        }

        # Secret: Phoenix API key
        env {
          name = "PHOENIX_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.phoenix_api_key.secret_id
              version = google_secret_manager_secret_version.phoenix_api_key[0].version
            }
          }
        }

        # Resource limits
        resources {
          limits = {
            cpu    = var.cpu
            memory = "${var.memory}Mi"
          }
        }

        # Health check
        liveness_probe {
          http_get {
            path = "/health"
            port = 8000
          }
          initial_delay_seconds = 10
          timeout_seconds       = 5
          period_seconds        = 30
          failure_threshold     = 3
        }

        startup_probe {
          http_get {
            path = "/health"
            port = 8000
          }
          initial_delay_seconds = 5
          timeout_seconds       = 3
          period_seconds        = 10
          failure_threshold     = 3
        }
      }

      timeout = "${var.timeout_seconds}s"

      # Scale configuration
      scaling {
        min_instance_count = 1
        max_instance_count = var.max_instances
      }
    }

    metadata {
      labels = {
        environment = var.environment
        service     = "aurelius-agent"
        tier        = "3-cloud"
      }

      annotations = {
        autoscaling_limits = "max_instances=${var.max_instances}"
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [client, launch_stage]
  }
}

# --- IAM: Public access (if enabled) ---

resource "google_cloud_run_service_iam_member" "public_access" {
  count   = var.allow_unauthenticated ? 1 : 0
  service = google_cloud_run_v2_service.aurelius.name
  role    = "roles/run.invoker"
  member  = "allUsers"
  location = var.region
}

# --- Outputs ---

output "service_url" {
  value       = google_cloud_run_v2_service.aurelius.uri
  description = "Cloud Run service URL"
}

output "service_name" {
  value       = google_cloud_run_v2_service.aurelius.name
  description = "Cloud Run service name"
}

output "artifact_registry" {
  value       = google_artifact_registry_repository.aurelius.repository_url
  description = "Artifact Registry repository URL"
}

output "service_account_email" {
  value       = google_service_account.aurelius.email
  description = "Service account email"
}

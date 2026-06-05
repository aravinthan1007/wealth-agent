variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "aurelius-wealth-agent"
}

variable "region" {
  description = "GCP region for Cloud Run"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "aurelius-agent"
}

variable "image_name" {
  description = "Container image name"
  type        = string
  default     = "aurelius-agent"
}

variable "memory" {
  description = "Memory allocation (MB)"
  type        = number
  default     = 512
}

variable "cpu" {
  description = "CPU allocation"
  type        = string
  default     = "1"
}

variable "max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 100
}

variable "timeout_seconds" {
  description = "Request timeout"
  type        = number
  default     = 300
}

variable "phoenix_api_key" {
  description = "Phoenix API key for tracing"
  type        = string
  sensitive   = true
  default     = ""
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access"
  type        = bool
  default     = true
}

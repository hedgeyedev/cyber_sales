variable "app_name" {
  description = "Application name"
  type        = string
  default     = "cyber-sales"
}

variable "app_environment" {
  description = "Environment name (staging/production)"
  type        = string
  default     = "production"
}

variable "app_image" {
  description = "Docker image from ECR (e.g., <account>.dkr.ecr.us-east-1.amazonaws.com/cyber-sales-web:latest)"
  type        = string
}

variable "replica_count" {
  description = "Number of web server replicas"
  type        = number
  default     = 2
}

variable "route53_hostname" {
  description = "Subdomain for the app (creates <name>.staging.hedgeye.cloud)"
  type        = string
  default     = "cyber-reports"
}

variable "storage_size" {
  description = "PersistentVolume size for reports storage"
  type        = string
  default     = "10Gi"
}

variable "reports_user" {
  description = "HTTP Basic Auth username"
  type        = string
  default     = "hedgeye"
  sensitive   = true
}

variable "reports_pass" {
  description = "HTTP Basic Auth password"
  type        = string
  sensitive   = true
}

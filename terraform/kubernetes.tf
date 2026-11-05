# Namespace for cyber sales app
resource "kubernetes_namespace" "app" {
  metadata {
    name = var.app_name
  }

  lifecycle {
    ignore_changes = [metadata.0.annotations]
  }
}

locals {
  namespace = kubernetes_namespace.app.metadata[0].name
}

# Deployment - Sinatra web server serving HTML reports
resource "kubernetes_deployment" "web" {
  metadata {
    name      = var.app_name
    namespace = local.namespace

    labels = {
      "tags.datadoghq.com/env"     = var.app_environment
      "tags.datadoghq.com/service" = var.app_name
    }
  }

  spec {
    replicas = var.replica_count

    selector {
      match_labels = {
        app = var.app_name
      }
    }

    template {
      metadata {
        labels = {
          app                          = var.app_name
          "tags.datadoghq.com/env"     = var.app_environment
          "tags.datadoghq.com/service" = var.app_name
        }
      }

      spec {
        container {
          name  = var.app_name
          image = var.app_image

          port {
            container_port = 4567  # Sinatra default port
          }

          # Mount the persistent volume for reading HTML reports
          volume_mount {
            name       = "reports-data"
            mount_path = "/app"
            read_only  = true  # Web server only reads, cronjob writes
          }

          # Environment variables for Basic Auth
          env {
            name  = "REPORTS_USER"
            value = var.reports_user
          }

          env {
            name  = "REPORTS_PASS"
            value = var.reports_pass
          }

          env {
            name  = "PORT"
            value = "4567"
          }

          # Health checks
          readiness_probe {
            http_get {
              path = "/health"
              port = 4567
            }
            initial_delay_seconds = 10
            period_seconds        = 5
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 4567
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }

          # Resource limits
          resources {
            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
            requests = {
              cpu    = "250m"
              memory = "256Mi"
            }
          }
        }

        # Define the volume
        volume {
          name = "reports-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim_v1.reports_data.metadata[0].name
          }
        }
      }
    }
  }

  wait_for_rollout = true
}

# Service - Expose web server within cluster
resource "kubernetes_service" "web" {
  metadata {
    name      = var.app_name
    namespace = local.namespace
  }

  spec {
    selector = {
      app = var.app_name
    }

    type = "NodePort"

    port {
      port        = 80
      target_port = 4567
      protocol    = "TCP"
    }
  }
}

# Ingress - Expose via ALB with HTTPS
resource "kubernetes_ingress_v1" "web" {
  metadata {
    name      = var.app_name
    namespace = local.namespace

    annotations = {
      "alb.ingress.kubernetes.io/scheme"          = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"     = "ip"
      "alb.ingress.kubernetes.io/certificate-arn" = data.terraform_remote_state.layer1.outputs.output[0].wildcard_cert_arn
      "alb.ingress.kubernetes.io/listen-ports"    = jsonencode([{ HTTPS : 443 }, { HTTP : 80 }])
      "alb.ingress.kubernetes.io/ssl-redirect"    = "443"
    }
  }

  spec {
    ingress_class_name = "alb"

    rule {
      host = "${var.route53_hostname}.hedgeye.com"  # Production domain

      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = kubernetes_service.web.metadata[0].name
              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }
}

# Output the URL for easy access
output "app_url" {
  value       = "https://${var.route53_hostname}.hedgeye.com"
  description = "URL to access cyber sales reports"
}

output "namespace" {
  value       = local.namespace
  description = "Kubernetes namespace (needed for cronjob deployment)"
}

output "pvc_name" {
  value       = kubernetes_persistent_volume_claim_v1.reports_data.metadata[0].name
  description = "PVC name (needed for cronjob to mount same storage)"
}

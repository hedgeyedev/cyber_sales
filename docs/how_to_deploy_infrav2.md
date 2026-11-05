  The microapp module used by the 2048-app sample does not support persistent volumes. Since your app needs to save files to disk, you'll need to create a
  custom Layer 3 deployment (like the discourse or jenkins examples) that includes:
  1. A PersistentVolumeClaim (PVC) using the EFS storage class
  2. A custom Kubernetes deployment with volume mounts

  Step-by-Step Guide

  1. Create Your Dockerfile

  Create a Linux x86 Dockerfile for your Sinatra app. Example:

  FROM --platform=linux/amd64 ruby:3.2-slim

  # Install Python if needed
  RUN apt-get update && apt-get install -y python3 python3-pip

  WORKDIR /app

  # Copy your app files
  COPY Gemfile Gemfile.lock ./
  RUN bundle install

  COPY . .

  # Ensure your app can write to this directory
  RUN mkdir -p /app/data && chmod 777 /app/data

  EXPOSE 4567

  CMD ["ruby", "app.rb", "-o", "0.0.0.0"]

  2. Build and Push Docker Image

  You'll need to push to Hedgeye's ECR repository:

  # Get ECR repository URL from devops
  ECR_REPO="<your-ecr-repo-url>"

  # Build for x86
  docker build --platform linux/amd64 -t your-app-name:latest .

  # Tag and push
  docker tag your-app-name:latest $ECR_REPO/your-app-name:latest
  aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPO
  docker push $ECR_REPO/your-app-name:latest

  3. Create Layer 3 Terraform Configuration

  Create a directory structure in your app's repository (or temporarily in environments/staging/layer3/apps/your-app/):

  your-app/
  ├── main.tf
  ├── pvc.tf
  ├── kubernetes.tf
  └── variables.tf

  main.tf:
  terraform {
    cloud {
      organization = "hedgeye"
      workspaces {
        name = "staging-your-app-name"  # Get this from devops
      }
    }

    required_version = ">= 1.4.0"

    required_providers {
      kubernetes = {
        source  = "hashicorp/kubernetes"
        version = "~> 2.27.0"
      }
    }
  }

  provider "kubernetes" {
    config_path = "../kubeconfig.yaml"  # Adjust path as needed

    ignore_annotations = ["^.*cattle\\.io.*"]
    ignore_labels      = ["^.*cattle\\.io.*"]
  }

  data "terraform_remote_state" "layer1" {
    backend = "remote"
    config = {
      organization = "hedgeye"
      workspaces = {
        name = "staging-layer1"
      }
    }
  }

  data "terraform_remote_state" "layer2" {
    backend = "remote"
    config = {
      organization = "hedgeye"
      workspaces = {
        name = "staging-layer2-public"
      }
    }
  }

  pvc.tf:
  # Persistent storage for your app's file saves
  resource "kubernetes_persistent_volume_claim_v1" "app_data" {
    wait_until_bound = false

    metadata {
      name      = "${var.app_name}-data"
      namespace = var.namespace
    }

    spec {
      access_modes       = ["ReadWriteMany"]  # EFS supports multiple pods
      storage_class_name = "efs-csi"           # Uses the cluster's EFS

      resources {
        requests = {
          storage = "10Gi"  # Adjust as needed
        }
      }
    }
  }

  kubernetes.tf:
  resource "kubernetes_namespace" "app" {
    metadata {
      generate_name = "${var.app_name}-"
    }

    lifecycle {
      ignore_changes = [metadata.0.annotations]
    }
  }

  locals {
    namespace = kubernetes_namespace.app.metadata[0].name
  }

  resource "kubernetes_deployment" "app" {
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
            app = var.app_name
            "tags.datadoghq.com/env"     = var.app_environment
            "tags.datadoghq.com/service" = var.app_name
          }
        }

        spec {
          container {
            name  = var.app_name
            image = var.app_image

            port {
              container_port = 4567  # Sinatra default
            }

            # Mount the persistent volume
            volume_mount {
              name       = "app-data"
              mount_path = "/app/data"  # Where your app saves files
            }

            # Health checks
            readiness_probe {
              http_get {
                path = "/"
                port = 4567
              }
              initial_delay_seconds = 10
            }

            liveness_probe {
              http_get {
                path = "/"
                port = 4567
              }
              initial_delay_seconds = 30
            }

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
            name = "app-data"
            persistent_volume_claim {
              claim_name = kubernetes_persistent_volume_claim_v1.app_data.metadata[0].name
            }
          }
        }
      }
    }

    wait_for_rollout = true
  }

  resource "kubernetes_service" "app" {
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

  resource "kubernetes_ingress_v1" "app" {
    metadata {
      name      = var.app_name
      namespace = local.namespace

      annotations = {
        "alb.ingress.kubernetes.io/scheme"           = "internet-facing"
        "alb.ingress.kubernetes.io/target-type"      = "ip"
        "alb.ingress.kubernetes.io/certificate-arn"  = data.terraform_remote_state.layer1.outputs.output[0].wildcard_cert_arn
        "alb.ingress.kubernetes.io/listen-ports"     = jsonencode([{HTTPS: 443}, {HTTP: 80}])
        "alb.ingress.kubernetes.io/ssl-redirect"     = "443"
      }
    }

    spec {
      ingress_class_name = "alb"

      rule {
        host = "${var.route53_hostname}.staging.hedgeye.cloud"

        http {
          path {
            path      = "/"
            path_type = "Prefix"

            backend {
              service {
                name = kubernetes_service.app.metadata[0].name
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

  variables.tf:
  variable "app_name" {
    default = "your-app-name"
  }

  variable "app_environment" {
    default = "staging"
  }

  variable "app_image" {
    description = "Docker image from ECR"
    type        = string
  }

  variable "replica_count" {
    default = 2
  }

  variable "route53_hostname" {
    description = "Subdomain for your app"
    default     = "your-app"
  }

  variable "namespace" {
    default = "default"
  }

  4. Deploy

  cd path/to/your/layer3/config

  # Initialize Terraform
  terraform init

  # Plan and apply
  terraform plan -var="app_image=<your-ecr-repo>/your-app:latest"
  terraform apply -var="app_image=<your-ecr-repo>/your-app:latest"

  Key Differences from 2048-app

  1. No microapp module - You're creating a custom deployment because you need persistent storage
  2. PVC with EFS - Using storage_class_name = "efs-csi" which is already configured in Layer 2
  3. Volume mounts - Your pods will mount /app/data (or wherever your app saves files) to the PVC
  4. Multiple replicas can share - EFS supports ReadWriteMany, so multiple pods can write to the same volume

  Important Notes

  - Get kubeconfig.yaml from devops for the staging cluster
  - Create Terraform Cloud workspace - Ask devops to create workspace staging-your-app-name
  - Adjust mount path - Change /app/data to wherever your Sinatra app writes files
  - EFS is shared - All replicas write to the same filesystem, ensure your app handles concurrent access properly


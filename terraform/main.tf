terraform {
  cloud {
    organization = "hedgeye"
    workspaces {
      name = "production-cyber-sales"  # Get this workspace created by devops
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
  # Uses current kubectl context (production cluster)
  # Alternative: config_path = "~/.kube/config"

  ignore_annotations = ["^.*cattle\\.io.*"]
  ignore_labels      = ["^.*cattle\\.io.*"]
}

# Layer 1 outputs (wildcard SSL cert, etc.)
data "terraform_remote_state" "layer1" {
  backend = "remote"
  config = {
    organization = "hedgeye"
    workspaces = {
      name = "production-layer1"
    }
  }
}

# Layer 2 outputs (EFS storage class, etc.)
data "terraform_remote_state" "layer2" {
  backend = "remote"
  config = {
    organization = "hedgeye"
    workspaces = {
      name = "production-layer2-public"
    }
  }
}

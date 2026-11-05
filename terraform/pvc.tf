# Persistent storage for cyber sales reports
# Uses EFS storage class configured in Layer 2
# Supports ReadWriteMany so both web server and cronjob can access

resource "kubernetes_persistent_volume_claim_v1" "reports_data" {
  wait_until_bound = false

  metadata {
    name      = "${var.app_name}-data"
    namespace = local.namespace
  }

  spec {
    access_modes       = ["ReadWriteMany"]  # EFS supports multiple pods reading/writing
    storage_class_name = "efs-csi"          # Layer 2 provides this

    resources {
      requests = {
        storage = var.storage_size
      }
    }
  }
}

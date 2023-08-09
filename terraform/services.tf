# Copyright 2023 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

##
# Cloud Storage Bucket
#
# Creates a Google Cloud Storage bucket for the keywordplatform outputs.

resource "google_storage_bucket" "output_bucket" {
  name          = format("%s-%s", var.project_id, var.bucket_name)
  location      = "US"
  storage_class = "STANDARD"

  uniform_bucket_level_access = true
  force_destroy = true
}

##
# Cloud Run Services
#
# Creates the backend and frontend run services. Images need to be available
# via: "gcr.io/${var.project_id}/keywordplatform/[backend|frontend]".

resource "google_cloud_run_service" "backend_run" {
  name     = "backend"
  location = var.region
  project  = var.project_id

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "1000"
      }
    }

    spec {
      service_account_name = google_service_account.backend_sa.email

      containers {
        image = format("%s:%s", var.backend_image, "latest")

        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }
        env {
          name  = "BUCKET_NAME"
          value = google_storage_bucket.output_bucket.name
        }
      }
    }
  }

  autogenerate_revision_name = true

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.apis]
}

locals {
  backend_url = google_cloud_run_service.backend_run.status[0].url
}

resource "google_cloud_run_service" "frontend_run" {
  name     = "frontend"
  location = var.region
  project  = var.project_id

  metadata {
    annotations = {
      # For valid annotation values and descriptions, see
      # https://cloud.google.com/sdk/gcloud/reference/run/deploy#--ingress
      "run.googleapis.com/ingress" = "internal-and-cloud-load-balancing"
    }
  }

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "1"
      }
    }

    spec {
      service_account_name = google_service_account.frontend_sa.email

      containers {
        image = format("%s:%s", var.frontend_image, "latest")

        env {
          name  = "BACKEND_URL"
          value = local.backend_url
        }
      }
    }
  }

  autogenerate_revision_name = true

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.apis]
}

##
# Secret Manager
#
# Adds credentials required for Google Ads authenticaton.

resource "google_secret_manager_secret" "client_id" {
  secret_id = "client_id"
  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "client_id-latest" {
  secret = google_secret_manager_secret.client_id.name
  secret_data = var.client_id
}

resource "google_secret_manager_secret_iam_member" "client_id-access" {
  secret_id = google_secret_manager_secret.client_id.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret" "client_secret" {
  secret_id = "client_secret"
  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "client_secret-latest" {
  secret = google_secret_manager_secret.client_secret.name
  secret_data = var.client_secret
}

resource "google_secret_manager_secret_iam_member" "client_secret-access" {
  secret_id = google_secret_manager_secret.client_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret" "login_customer_id" {
  secret_id = "login_customer_id"
  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "login_customer_id-latest" {
  secret = google_secret_manager_secret.login_customer_id.name
  secret_data = var.login_customer_id
}

resource "google_secret_manager_secret_iam_member" "login_customer_id-access" {
  secret_id = google_secret_manager_secret.login_customer_id.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret" "developer_token" {
  secret_id = "developer_token"
  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "developer_token-latest" {
  secret = google_secret_manager_secret.developer_token.name
  secret_data = var.developer_token
}

resource "google_secret_manager_secret_iam_member" "developer_token-access" {
  secret_id = google_secret_manager_secret.developer_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_secret_manager_secret" "refresh_token" {
  secret_id = "refresh_token"
  replication {
    automatic = true
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "refresh_token-latest" {
  secret = google_secret_manager_secret.refresh_token.name
  secret_data = var.refresh_token
}

resource "google_secret_manager_secret_iam_member" "refresh_token-access" {
  secret_id = google_secret_manager_secret.refresh_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}
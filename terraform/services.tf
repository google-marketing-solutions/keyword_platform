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
        image = data.google_container_registry_image.backend_latest.image_url

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
        image = data.google_container_registry_image.frontend_latest.image_url

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

// In order to update the Cloud Run deployment when the underlying :latest
// image changes, we will retrieve the sha256_digest of the image through
// the docker provider, since the google container registry does not seem
// to have an API.
data "google_client_config" "default" {}

provider "docker" {
  registry_auth {
    address  = "gcr.io"
    username = "oauth2accesstoken"
    password = data.google_client_config.default.access_token
  }
}

data "docker_registry_image" "frontend_image" {
  name = format("%s:%s", var.frontend_image, "latest")
}

data "google_container_registry_image" "frontend_latest" {
  name    = "keywordplatform-frontend"
  project = var.project_id
  digest  = data.docker_registry_image.frontend_image.sha256_digest
}

data "docker_registry_image" "backend_image" {
  name = format("%s:%s", var.backend_image, "latest")
}

data "google_container_registry_image" "backend_latest" {
  name    = "keywordplatform-backend"
  project = var.project_id
  digest  = data.docker_registry_image.backend_image.sha256_digest
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

resource "google_secret_manager_secret_version" "palm_api_key_latest" {
  count       = var.palm_api_key != null ? 1 : 0
  secret      = google_secret_manager_secret.palm_api_key.name
  secret_data = var.palm_api_key
}

resource "google_secret_manager_secret_iam_member" "palm_api_key-access" {
  count     = google_secret_manager_secret_version.palm_api_key_latest[*].count
  secret_id = google_secret_manager_secret.palm_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}
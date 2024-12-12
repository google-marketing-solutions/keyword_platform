# Copyright 2024 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

##
# Service Accounts
#

resource "google_service_account" "frontend_sa" {
  account_id   = "keywordplatform-frontend-sa"
  display_name = "Keyword Platform Frontend Service Account"
  project      = var.project_id
}

resource "google_service_account" "backend_sa" {
  account_id   = "keywordplatform-backend-sa"
  display_name = "Keyword Platform Backend Service Account"
  project      = var.project_id
}

resource "google_service_account" "iap_sa" {
  account_id   = "keywordplatform-iap-sa"
  display_name = "Keyword Platform IAP Service Account"
  project      = var.project_id
}

resource "google_service_account" "pubsub_sa" {
  account_id   = "keywordplatform-pubsub-invoker"
  display_name = "Keyword Platform Pub/Sub Service Account"
  project      = var.project_id
}

resource "google_project_service_identity" "cloudbuild_managed_sa" {
  provider = google-beta
  project  = var.project_id
  service  = "cloudbuild.googleapis.com"
}

resource "google_project_service_identity" "iap_managed_sa" {
  provider = google-beta
  project  = var.project_id
  service  = "iap.googleapis.com"
}

resource "google_project_service_identity" "pubsub_agent" {
  provider = google-beta
  project  = var.project_id
  service  = "pubsub.googleapis.com"
}

##
# Service Account Permissions
#

resource "google_project_iam_member" "backend_sa_logging_writer" {
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
  project = var.project_id
  role    = "roles/logging.logWriter"
}

resource "google_project_iam_member" "backend_sa_logging_viewer" {
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
  project = var.project_id
  role    = "roles/logging.viewer"
}

resource "google_project_iam_member" "backend_sa_token_creator" {
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
}

resource "google_project_iam_member" "backend_sa_storage_object_admin" {
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
  project = var.project_id
  role    = "roles/storage.objectAdmin"
}

resource "google_project_iam_member" "backend_sa_vertexai_user" {
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
  project = var.project_id
  role    = "roles/aiplatform.user"
}

resource "google_project_iam_member" "backend_builds_viewer" {
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
  project = var.project_id
  role    = "roles/cloudbuild.builds.viewer"
}

# Needed to access the backend image during migrations from Cloud Build.
resource "google_project_iam_member" "cloudbuild_managed_sa_object_viewer" {
  member  = "serviceAccount:${google_project_service_identity.cloudbuild_managed_sa.email}"
  project = var.project_id
  role    = "roles/storage.objectViewer"
}

##
# Cloud Run permissions
#
# We delegate the authentication flow to IAP, so we need to give IAP SA access
# to Cloud Run.

data "google_iam_policy" "iap_users" {
  binding {
    role = "roles/iap.httpsResourceAccessor"
    members = concat(
      ["serviceAccount:${google_service_account.frontend_sa.email}"],
      var.iap_allowed_users
    )
  }
}

resource "google_iap_web_backend_service_iam_policy" "frontend" {
  project             = google_compute_backend_service.frontend_backend.project
  web_backend_service = google_compute_backend_service.frontend_backend.name
  policy_data         = data.google_iam_policy.iap_users.policy_data
}

data "google_iam_policy" "frontend_run_users" {
  binding {
    role = "roles/run.invoker"
    members = [
      "serviceAccount:${google_project_service_identity.iap_sa.email}",
      "serviceAccount:${google_service_account.frontend_sa.email}",
    ]
  }
}

data "google_iam_policy" "backend_run_users" {
  binding {
    role = "roles/run.invoker"
    members = [
      "serviceAccount:${google_service_account.frontend_sa.email}",
      "serviceAccount:${google_service_account.pubsub_sa.email}",
      "serviceAccount:${google_service_account.backend_sa.email}",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "frontend_run_invoker" {
  location    = google_cloud_run_service.frontend_run.location
  project     = google_cloud_run_service.frontend_run.project
  service     = google_cloud_run_service.frontend_run.name
  policy_data = data.google_iam_policy.frontend_run_users.policy_data
}

resource "google_cloud_run_service_iam_policy" "backend_run_invoker" {
  location    = google_cloud_run_service.backend_run.location
  project     = google_cloud_run_service.backend_run.project
  service     = google_cloud_run_service.backend_run.name
  policy_data = data.google_iam_policy.backend_run_users.policy_data
}

resource "google_project_iam_binding" "project_token_creator" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  members = [
    "serviceAccount:${google_project_service_identity.pubsub_agent.email}",
    "serviceAccount:${google_service_account.backend_sa.email}"
  ]
}


##
# PubSub Permissions
#

// Enable notifications by giving the correct IAM permission to the unique service account.
data "google_storage_project_service_account" "gcs_account" {
  provider = google-beta
}

// Create a Pub/Sub topic.
resource "google_pubsub_topic_iam_binding" "binding" {
  provider = google-beta
  project  = var.project_id
  topic    = google_pubsub_topic.create_glossary.id
  role     = "roles/pubsub.publisher"
  members  = ["serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"]
}

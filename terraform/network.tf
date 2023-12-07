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

resource "google_compute_global_address" "default" {
  name          = "global-keywordplatform-default"
  address_type  = "EXTERNAL"

  # Create a network only if the compute.googleapis.com API has been activated.
  depends_on = [google_project_service.apis]
  project = var.project_id
}

resource "google_compute_region_network_endpoint_group" "frontend_neg" {
  name                  = "frontend-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id
  cloud_run {
    service = google_cloud_run_service.frontend_run.name
  }
  lifecycle {
   create_before_destroy = true
 }
}

resource "google_compute_backend_service" "frontend_backend" {
  name                            = "keywordplatform-frontend-backend-service"
  enable_cdn                      = false
  connection_draining_timeout_sec = 10
  project                         = var.project_id

  backend {
    group = google_compute_region_network_endpoint_group.frontend_neg.id
  }

  iap {
    oauth2_client_id = google_iap_client.default.client_id
    oauth2_client_secret = google_iap_client.default.secret
  }

  load_balancing_scheme = "EXTERNAL"
  protocol              = "HTTP"
}

resource "google_compute_url_map" "default" {
  name             = "keywordplatform-http-lb"
  default_service  = google_compute_backend_service.frontend_backend.id
  project          = var.project_id

  host_rule {
    hosts        = ["*"]
    path_matcher = "allpaths"
  }

  path_matcher {
    name = "allpaths"
    default_service = google_compute_backend_service.frontend_backend.id
  }
}

resource "google_compute_target_https_proxy" "default" {
  name    = "keywordplatform-default-https-lb-proxy"
  url_map = google_compute_url_map.default.id
  project = var.project_id
  ssl_certificates = [
    google_compute_managed_ssl_certificate.default.id,
  ]
}

resource "google_compute_global_forwarding_rule" "default" {
  name = "keywordplatform-default-https-lb-forwarding-rule"
  project = var.project_id
  ip_protocol = "TCP"
  load_balancing_scheme = "EXTERNAL"
  port_range = "443"
  target = google_compute_target_https_proxy.default.id
  ip_address = google_compute_global_address.default.id
}
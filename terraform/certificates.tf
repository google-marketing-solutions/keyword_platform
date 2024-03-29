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

locals {
  secured_domain = "keywordplatform.${google_compute_global_address.default.address}.nip.io"
}

resource "google_compute_managed_ssl_certificate" "default" {
  name = "keywordplatform-managed"
  project = var.project_id

  managed {
    domains = [local.secured_domain]
  }
}
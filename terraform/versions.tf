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

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.43.1"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "4.43.1"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.4.3"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
  }
  provider_meta "google" {
    module_name = "cloud-solutions/keyword-platform-deploy-v2.1.7"
  }
}

provider "google" {
  access_token = var.test_google_access_token
  project      = var.project_id
  region       = var.region
}

provider "google-beta" {
  access_token = var.test_google_access_token
  project      = var.project_id
  region       = var.region
}

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
# Security (IAP configuration)

variable "iap_brand_id" {
  description = "Existing IAP Brand ID - only INTERNAL TYPE (you can obtain it using this command: `$ gcloud iap oauth-brands list --format='value(name)' | sed 's:.*/::'`)."
}

variable "iap_allowed_users" {
  type = list
}

##
# Images

variable "frontend_image" {
  description = "The Docker Image for the frontend service."
}

variable "backend_image" {
  description = "The Docker Image for the backend service."
}

##
# Google Ads OAuth2

variable "client_id" {
  description = "OAuth2.0 Web Client ID."
}

variable "client_secret" {
  description = "OAuth2.0 Web Client Secret."
}

variable "login_customer_id" {
  description = "The Google Ads Login Customer Id (typically top level MCC.)"
}

variable "developer_token" {
  description = "The Google Ads Developer Token."
}

variable "refresh_token" {
  description = "The Google Ads OAuth2 Refresh Token"
}

##
# Google Cloud Project

variable "project_id" {
  description = "GCP Project ID"
}

variable "region" {
  description = "GCP Region"
}

variable "bucket_name" {
  description = "The bucket name to store Keywordplatform output files."
}

variable "opt_out" {
  description = "Whether or not to opt out of GA tracking."
  type = bool
}


##
# Test utilities

variable "test_google_access_token" {
  type    = string
  default = null
}

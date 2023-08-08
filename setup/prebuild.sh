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

# This file is executed as part of the Cloud Run Deploy flow.
#
# Has to be run from the root directory e.g. `chmod -x && ./setup/prebuild.sh`
# as part of a Cloud Run deployment hook and expects various environment
# variables (see below).
#
# Globals:
#   GOOGLE_CLOUD_PROJECT
#   GOOGLE_CLOUD_REGION
#   CLIENT_ID
#   BUCKET_NAME
#   CLIENT_ID
#   CLIENT_SECRET
#   DEVELOPER_TOKEN
#   LOGIN_CUSTOMER_ID
#   REFRESH_TOKEN
#   IAP_ALLOWED_USERS
#   IAP_SUPPORT_EMAIL

terraform_state_bucket_name="${GOOGLE_CLOUD_PROJECT}-bucket-tfstate"
backend_image="gcr.io/${GOOGLE_CLOUD_PROJECT}/keywordplatform/backend"
frontend_image="gcr.io/${GOOGLE_CLOUD_PROJECT}/keywordplatform/frontend"

echo "Setting Project ID: ${GOOGLE_CLOUD_PROJECT}"
gcloud auth login --project $GOOGLE_CLOUD_PROJECT
gcloud config set project ${GOOGLE_CLOUD_PROJECT}

# Enable the Cloud Storage API.
gcloud services enable storage.googleapis.com

# Create a GCS bucket to store terraform state files.
gsutil -q stat gs://${terraform_state_bucket_name}/*
return_value=$?
if [ $return_value != 0 ]; then
  echo "${terraform_state_bucket_name} alredy exists. Re-using..."
else
  echo "Creating terraform state cloud storage bucket..." 
  gcloud storage buckets create gs://${terraform_state_bucket_name} \
    --project=${GOOGLE_CLOUD_PROJECT}
  # Enable versioning.
  gcloud storage buckets update gs://${terraform_state_bucket_name} \
    --versioning
fi

# Build docker images.
echo "Building backend service."
gcloud builds submit ./py \
--tag $backend_image

echo "Building frontend service..."
gcloud builds submit ./ui \
--tag $frontend_image

echo "SUCCESS: Frontend and Backend images built successfully."

# Check if there is an existing Consent Screen.
oauth_brands=$(gcloud iap oauth-brands list)

if [ $? -eq 0 ]; then
  iap_brand_id=$(gcloud iap oauth-brands list --format="value(name)" | sed "s:.*/::")
  support_email=$(gcloud iap oauth-brands list --format="value(supportEmail)")
else
  support_email=$IAP_SUPPORT_EMAIL
  iap_brand_id="null"
fi

# Convert the list of iap allowed users to a terraform compatible list.
allowed_users_tf_list=$(echo "$IAP_ALLOWED_USERS" | sed 's/\([^,]\+\)/"user:\1"/g' | sed 's/,/, /g' | sed 's/.*/[&]/')

# Setup & Run Terraform.
terraform -chdir=./terraform init \
  -backend-config="bucket=$terraform_state_bucket_name" \
  -get=true \
  -upgrade

terraform -chdir=./terraform plan \
  -var "bucket_name=$BUCKET_NAME" \
  -var "frontend_image=$frontend_image" \
  -var "backend_image=$backend_image" \
  -var "client_id=$CLIENT_ID" \
  -var "client_secret=$CLIENT_SECRET" \
  -var "developer_token=$DEVELOPER_TOKEN" \
  -var "login_customer_id=$LOGIN_CUSTOMER_ID" \
  -var "project_id=$GOOGLE_CLOUD_PROJECT" \
  -var "region=$GOOGLE_CLOUD_REGION" \
  -var "iap_allowed_users=$allowed_users_tf_list" \
  -var "iap_support_email=$support_email" \
  -var "iap_brand_id=$iap_brand_id" \
  -out="/tmp/tfplan"

terraform -chdir=./terraform apply -auto-approve "/tmp/tfplan"

echo "-----------------------------------------------------"
echo "Congrats! You successfully deployed Keyword Platform."
echo "-----------------------------------------------------"
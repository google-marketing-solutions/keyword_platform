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

# Supress apt-get warnings if run in an ephemeral cloud shell.
mkdir ~/.cloudshell touch ~/.cloudshell/no-apt-get-warning
sudo apt-get install fzf
# Get a list of accessible gcloud projects and store them in an array
projects=($(gcloud projects list --format="value(projectId)"))

# Use fzf to interactively select a project
selected_project=$(printf "%s\n" "${projects[@]}" | fzf --prompt="Select a project: ")

# Check if a project was selected
if [[ -n $selected_project ]]; then
    echo "Selected project: $selected_project"
    # Pass the selected project to a variable or use it directly in your script
    # For example, you can export it to make it available in the environment
    export GOOGLE_CLOUD_PROJECT="$selected_project"
else
    echo "No project selected."
fi

echo "Setting Project ID: ${GOOGLE_CLOUD_PROJECT}"
gcloud config set project ${GOOGLE_CLOUD_PROJECT}

regions=($(gcloud compute regions list --format="value(name)"))

# Display a select menu for the user to choose a region
PS3="Select a region: "
select selected_region in "${regions[@]}"; do
    if [[ -n $selected_region ]]; then
        echo "Selected region: $selected_region"
        # Pass the selected region to a variable or use it directly in your script
        # For example, you can export it to make it available in the environment
        export GOOGLE_CLOUD_REGION="$selected_region"
        break
    else
        echo "Invalid choice, please select a valid region."
    fi
done

echo "Enter a name for a bucket used to store Keyword Platform files:"
read bucket_name
BUCKET_NAME=$bucket_name

echo "Enter an OAuth2.0 Web Client ID"
read client_id
CLIENT_ID=$client_id

echo "Enter an OAuth2.0 Web Client Secret"
read client_secret
CLIENT_SECRET=$client_secret

echo "Enter a Google Ads Developer Token:"
read developer_token
DEVELOPER_TOKEN=$developer_token

echo "Enter your Google Ads Login Customer ID (without hyphens):"
read login_customer_id
LOGIN_CUSTOMER_ID=$login_customer_id

echo "Enter a support Email for the OAuth Consent Screen:"
read iap_support_email
IAP_SUPPORT_EMAIL=$iap_support_email

echo "Enter a comma-separated list of users to grant access to the solution:"
read iap_allowed_users
IAP_ALLOWED_USERS=$iap_allowed_users

opt_out="N"

read -p "Do you want to opt out of sending usage information to Google? (N/n) " yn

if [[ -z "$yn" ]]; then
  yn="$opt_out"
fi

yn=$(tr '[:upper:]' '[:lower:]' <<< "$yn")

# If the user's response is "y" or "yes", then they want to opt out.
if [[ "$yn" == "y" || "$yn" == "yes" ]]; then
  echo "You have opted out."
  OPT_OUT=true
  pattern_to_replace="<script async src=\"https:\/\/www.googletagmanager.com\/gtag\/js?id=G-C0ZGCTLG7Z\"><\/script>"
  ui_index_file="./ui/src/index.html"
  out_out_message="<!-- User opted out of Google Analytics. -->"
  sed -i "s|$pattern_to_replace|$out_out_message|g" $ui_index_file
  pattern_to_delete="<!-- Google tag (gtag.js) -->"
  sed -i "s|$pattern_to_delete||g" $ui_index_file
else
  echo "You have not opted out."
  OPT_OUT=false
fi

terraform_state_bucket_name="${GOOGLE_CLOUD_PROJECT}-bucket-tfstate"
backend_image="gcr.io/${GOOGLE_CLOUD_PROJECT}/keywordplatform-backend"
frontend_image="gcr.io/${GOOGLE_CLOUD_PROJECT}/keywordplatform-frontend"

# Enable the APIs.
REQUIRED_APIS=(
  storage.googleapis.com
  iap.googleapis.com
  compute.googleapis.com
  run.googleapis.com
)

for API in "${REQUIRED_APIS[@]}"; do
  gcloud services enable $API
done

# Create a GCS bucket to store terraform state files.
echo "Creating terraform state cloud storage bucket..."
gcloud storage buckets create gs://${terraform_state_bucket_name} \
  --project=${GOOGLE_CLOUD_PROJECT}
# Enable versioning.
gcloud storage buckets update gs://${terraform_state_bucket_name} \
  --versioning

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
  iap_brand_id=""
fi

# Convert the list of iap allowed users to a terraform compatible list.
allowed_users_tf_list=$(echo "$IAP_ALLOWED_USERS" | sed 's/\([^,]\+\)/"user:\1"/g' | sed 's/,/, /g' | sed 's/.*/[&]/')

python ./setup/utils/oauth_flow.py --client_id="${CLIENT_ID}" --client_secret="${CLIENT_SECRET}"
refresh_token=$(cat refresh_token.txt)
rm -f refresh_token.txt

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
  -var "opt_out=$OPT_OUT" \
  -var "client_secret=$CLIENT_SECRET" \
  -var "developer_token=$DEVELOPER_TOKEN" \
  -var "login_customer_id=$LOGIN_CUSTOMER_ID" \
  -var "refresh_token=$refresh_token" \
  -var "project_id=$GOOGLE_CLOUD_PROJECT" \
  -var "region=$GOOGLE_CLOUD_REGION" \
  -var "iap_allowed_users=$allowed_users_tf_list" \
  -var "iap_support_email=$support_email" \
  -var "iap_brand_id=$iap_brand_id" \
  -out="/tmp/tfplan"

terraform_apply_exit_code=$(terraform -chdir=./terraform apply -auto-approve "/tmp/tfplan" | tee /dev/tty | ( ! grep "Error applying plan" ); echo $?)

if [ $terraform_apply_exit_code -ne 0 ]; then
  echo "--------------------------------------------------------------------------------------"
  echo "Oops! Something didn't work, ensure you have Project Owner permissions and try again. "
  echo "--------------------------------------------------------------------------------------"
else
  echo "-----------------------------------------------------"
  echo "Congrats! You successfully deployed Keyword Platform."
  echo "-----------------------------------------------------"
fi

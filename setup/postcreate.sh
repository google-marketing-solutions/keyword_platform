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

#######################################
# Adds secret to secret manager and grants backend access.
# Globals:
#   SECRET
#   BACKEND_SERVICE_NAME
#   GOOGLE_CLOUD_PROJECT
# Arguments:
#   None
#######################################
add_secret() {
    printf '%s' "Enter a value for $SECRET :"
    local input
    read -r input
    gcloud secrets create "$SECRET" --replication-policy=automatic
    gcloud secrets versions add "$SECRET" --data-file=<(echo ${input})
    sleep 1
    gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:${BACKEND_SERVICE_NAME}-identity@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
    echo "$SECRET has been successfully added."
}

echo "Adding required secrets to Secret Manager..."

REQUIRED_SECRETS=(
    client_id
    client_secret
    login_customer_id
    refresh_token
    developer_token
)

EXISTING_SECRETS=$(gcloud secrets list)

for SECRET in "${REQUIRED_SECRETS[@]}"
do
  if echo "$EXISTING_SECRETS" | grep -q "$SECRET"
  then
    printf '%s' "$SECRET already exists. Do you want to add a new value for it? [Y/n]:"
    local input
    read -r input
    if [[ ${input} == 'n' || ${input} == 'N' ]]; then
        gcloud secrets add-iam-policy-binding $SECRET \
        --member="serviceAccount:${BACKEND_SERVICE_NAME}-identity@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    else
        gcloud --quiet secrets delete $SECRET
        add_secret
  else
    add_secret
  fi
done

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

cat <<EOF
Keyword Factory requires an oAuth2.0 client Id to have access to your Google
Ads accounts. Next to your Google Ads Developer token and Login Customer ID
(typically the MCC ID) you will need a Client ID, Client Secret and Refresh
Token. Follow the instructions below to obtain them.

Click the link below to go to your projects Credentials
page and hit '+ Create Credentials' to create an OAuth Client ID, choose Web
Application and add https://developers.google.com/oauthplayground to the
Authorized redirect URIs. Take note of the Client ID and Client Secret.

Head to https://developers.google.com/oauthplayground and add the select the
following scopes:

  * https://www.googleapis.com/auth/cloud-platform
  * https://www.googleapis.com/auth/cloud-translation
  * https://www.googleapis.com/auth/adwords

Hit the settings/configuration button on the top right and click the box to
use your own credetials. Enter the Client ID and Client Secret. Close the
configuration and hit 'Authorize'. Once you have gone throught the process
exchange the access for a refresh token and take note of it.
EOF

echo "Add the required IDs and tokens below..."

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
    read -r input
    if [[ ${input} == 'n' || ${input} == 'N' ]]
    then
      gcloud secrets add-iam-policy-binding $SECRET \
      --member="serviceAccount:${BACKEND_SERVICE_NAME}-identity@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com" \
      --role="roles/secretmanager.secretAccessor"
    else
      gcloud --quiet secrets delete $SECRET
      add_secret
    fi
  else
    add_secret
  fi
done

echo "-----------------------------------------------------"
echo "Congrats! You successfully deployed Keyword Platform."
echo "-----------------------------------------------------"
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

APPLICATION_TITLE="keyword-platform"
DISPLAY_NAME="keyword-platform-web"

echo "Please log in."
gcloud auth login --no-launch-browser --brief

account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
echo "Account is set to: $account"

if [ "$(gcloud iap oauth-brands list --format="value(name)")" == "" ]; then
    echo "The project does not have an oAuth Consent screen configured."
    echo "Creating oAuth Consent screen."
    oauth_brand=$(gcloud iap oauth-brands create --application_title=${APPLICATION_TITLE} --support_email=${account})
else
    oauth_brand=$(gcloud iap oauth-brands list --format="value(name)")
    echo "Using existing oAuth consent screen: $oauth_brand"

echo "Creating dedicated web application oAuth2.0 client..."

if [ "$(gcloud iap oauth-clients list $oauth_brand --filter="displayName:${DISPLAY_NAME}")" != "" ]; then
    echo "Found existing oAuth client with name: ${DISPLAY_NAME}."
    output=$(gcloud iap oauth-clients list ${oauth_brand} --filter="displayName:${DISPLAY_NAME}" --format="value(name,secret)")
else
    echo "Creating new oAuth client with name: ${DISPLAY_NAME}"
    output=$(gcloud iap oauth-clients create  $oauth_brand --display_name=${DISPLAY_NAME} --format="value(name,secret)")

client_id=$(echo "$output" | awk -F'/' '{print $NF}')
echo "Client ID: $client_id"
client_secret=$(echo "$output" | awk '{print $2}')
echo "Client Secret: $client_secret"

echo "Starting Google Ads authentication..."

echo "Enter the a Google Ads Login Customer Id."
read -p "Login Customer Id: " login_customer_id

echo "Enter the a Google Ads developer token."
read -p "Developer Token: " developer_token

# TODO(): Go through Google Ads oAuth2 flow here.

echo "Setting Cloud Run environment variables..."
gcloud run services update keyword-platfrm --update-env-vars bucket_name=${GOOGLE_CLOUD_PROJECT}-keyword_factory --region=${GOOGLE_CLOUD_REGION}
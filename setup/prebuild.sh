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

echo "Setting Project ID: ${GOOGLE_CLOUD_PROJECT}"
gcloud config set project ${GOOGLE_CLOUD_PROJECT}

REQUIRED_SERVICES=(
  cloudbuild.googleapis.com
  logging.googleapis.com
  secretmanager.googleapis.com
  storage-component.googleapis.com
  googleads.googleapis.com
  translate.googleapis.com
  artifactregistry.googleapis.com
)

echo "Enabling Cloud APIs if necessary..."
ENABLED_SERVICES=$(gcloud services list)
for SERVICE in "${REQUIRED_SERVICES[@]}"
do
  if echo "$ENABLED_SERVICES" | grep -q "$SERVICE"
  then
    echo "$SERVICE is already enabled."
  else
    gcloud services enable "$SERVICE" \
      && echo "$SERVICE has been successfully enabled."
    sleep 1
  fi
done

echo "Creating cloud storage bucket..."
gcloud alpha storage buckets create gs://${GOOGLE_CLOUD_PROJECT}-keyword-platform --project=${GOOGLE_CLOUD_PROJECT}
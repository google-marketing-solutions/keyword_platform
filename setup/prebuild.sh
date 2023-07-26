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

bucket_name="${GOOGLE_CLOUD_PROJECT}-${BUCKET_NAME}"

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
  iamcredentials.googleapis.com
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
if [$(gsutil -q stat gs://${bucket_name}) == 0]
then 
  gcloud alpha storage buckets create gs://${bucket_name} \
  --project=${GOOGLE_CLOUD_PROJECT}
else
  printf '%s' "${bucket_name} alredy exists, do you want to reuse it? [y/N]:"
  local input
  read -r input
  if [[ ${input} == 'n' || ${input} == 'N' ]]; then
  printf '%s' "Enter a new bucket name:"
  local input
  bucket_name=$input
  gcloud alpha storage buckets create gs://${bucket_name} \
  --project=${GOOGLE_CLOUD_PROJECT}


echo "Building backend service."
gcloud builds submit ./py \
--tag gcr.io/${GOOGLE_CLOUD_PROJECT}/${BACKEND_SERVICE_NAME}

echo "Creating backend service account."
gcloud iam service-accounts create ${BACKEND_SERVICE_NAME}-sa

echo "Deploying backend service..."
gcloud run deploy $BACKEND_SERVICE_NAME \
--image gcr.io/${GOOGLE_CLOUD_PROJECT}/${BACKEND_SERVICE_NAME} \
--set-env-vars GCP_PROJECT=$GOOGLE_CLOUD_PROJECT,BUCKET_NAME=$bucket_name \
--service-account ${BACKEND_SERVICE_NAME}-sa@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com \
--region ${GOOGLE_CLOUD_REGION} \
--no-allow-unauthenticated

backend_url=$(gcloud run services describe $BACKEND_SERVICE_NAME \
--format='value(status.url)' \
--platform managed \
--region ${GOOGLE_CLOUD_REGION})

echo "Building frontend service..."
gcloud builds submit ./ui \
--tag gcr.io/${GOOGLE_CLOUD_PROJECT}/${FRONTEND_SERVICE_NAME}

echo "Creating frontend service account."
gcloud iam service-accounts create ${FRONTEND_SERVICE_NAME}-sa

gcloud run services add-iam-policy-binding $BACKEND_SERVICE_NAME \
--member serviceAccount:${FRONTEND_SERVICE_NAME}-sa@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com \
--role roles/run.invoker

echo "Deploying frontend service..."
gcloud run deploy $FRONTEND_SERVICE_NAME \
--image gcr.io/${GOOGLE_CLOUD_PROJECT}/${FRONTEND_SERVICE_NAME} \
--service-account ${FRONTEND_SERVICE_NAME}-sa@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com \
--set-env-vars BACKEND_URL=$backend_url \
--region ${GOOGLE_CLOUD_REGION} \
--allow-unauthenticated

echo "Frontend and Backend deployed successfully."

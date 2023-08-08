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

# Runs the user through the OAuth2.0 process.
#
# The resultig refresh token is saved to a secret manager secret.

client_id=$(gcloud secrets versions access latest --secret=client_id)
client_secret=$(gcloud secrets versions access latest --secret=client_secret)

python ./setup/utils/oauth_flow.py --client_id="${client_id}" --client_secret="${client_secret}"
refresh_token=$(cat refresh_token.txt)

gcloud secrets create refresh_token --data-file="refresh_token.txt"
rm -f refresh_token.txt

echo "Added refresh token to Secret Manager."
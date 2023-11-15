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

"""E2E tests for the backend Python container."""

import json
import os
import urllib


import google.auth
import google.auth.transport.requests
import google.cloud.logging
import google.oauth2.id_token
import pytest


_BACKEND_URL_ENV_VAR = 'BACKEND_URL'
_SERVICE_ACCOUNT = 'SERVICE_ACCOUNT'  # The service account to impersonate.

client = google.cloud.logging.Client()
client.setup_logging()


@pytest.mark.systemtest
def test_accessible_accounts():
  url = os.environ.get(_BACKEND_URL_ENV_VAR)
  service_account = os.environ.get(_SERVICE_ACCOUNT)

  service_account_credentials_url = (
      f'https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/'
      f'{service_account}:generateIdToken')

  # Generates access token
  credentials, _ = google.auth.default(
      scopes='https://www.googleapis.com/auth/cloud-platform')

  # Creates an AuthorizedSession that includes the access_token based on
  # credentials
  authorized_session = google.auth.transport.requests.AuthorizedSession(
      credentials)

  token_response = authorized_session.request(
      'POST',
      service_account_credentials_url,
      data=json.dumps({'audience': url}),
      headers={'Content-Type': 'application/json'})

  jwt = token_response.json()
  id_token = jwt['token']

  assert id_token is not None, 'Could not fetch id token for get accounts.'

  request = urllib.request.Request(f'{url}/accessible_accounts')
  request.add_header('Authorization', f'Bearer {id_token}')

  with urllib.request.urlopen(request) as response:
    assert (
        response.status == 200
    ), 'Got non-200 response from /accessible_accounts'
    body = response.read()
    account_dict = json.loads(body)
    assert account_dict, 'Could not find accessible accounts'


@pytest.mark.systemtest
@pytest.mark.skipif(
    os.getenv('TEST_FAILURE_ALERTING') != 'TRUE',
    reason='Test failure alerting is not set to TRUE.',
)
def test_that_always_fails():
  """A deliberately failing test, to check alerts are sent when tests fail."""
  assert False

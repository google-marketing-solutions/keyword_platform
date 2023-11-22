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
_SELECTED_ACCOUNTS = 'SELECTED_ACCOUNTS'
_SELECTED_CAMPAIGNS = 'SELECTED_CAMPAIGNS'
_URL = os.environ.get(_BACKEND_URL_ENV_VAR)

client = google.cloud.logging.Client()
client.setup_logging()


@pytest.fixture(name='token')
def fixture_token() -> str:
  """Returns an auth token for use in other system tests."""
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
      data=json.dumps({'audience': _URL}),
      headers={'Content-Type': 'application/json'})

  jwt = token_response.json()
  token = jwt['token']

  assert token is not None, 'Could not fetch token.'

  return token


@pytest.mark.systemtest
def test_accessible_accounts(token: str) -> None:
  """Tests the accessible_accounts endpoint."""
  request = urllib.request.Request(f'{_URL}/accessible_accounts')
  request.add_header('Authorization', f'Bearer {token}')

  with urllib.request.urlopen(request) as response:
    assert (
        response.status == 200
    ), 'Got non-200 response from /accessible_accounts'
    body = response.read()
    account_dict = json.loads(body)
    assert account_dict, 'Could not find accessible accounts'


@pytest.mark.systemtest
def test_campaigns(token: str) -> None:
  """Tests the campaigns endpoint."""
  selected_accounts = os.environ.get(_SELECTED_ACCOUNTS)
  data = urllib.parse.urlencode(
      {'selected_accounts': selected_accounts}).encode('utf-8')
  request = urllib.request.Request(f'{_URL}/campaigns', data)
  request.add_header('Authorization', f'Bearer {token}')

  with urllib.request.urlopen(request) as response:
    assert (
        response.status == 200
    ), 'Got non-200 response from /campaigns'
    body = response.read()
    campaigns = json.loads(body)
    assert campaigns, f'Could not find campaigns for {selected_accounts}'


@pytest.mark.systemtest
def test_cost(token: str) -> None:
  """Tests the cost endpoint."""
  selected_accounts = os.environ.get(_SELECTED_ACCOUNTS)
  selected_campaigns = os.environ.get(_SELECTED_CAMPAIGNS)

  data = {
      'selected_accounts': selected_accounts,
      'selected_campaigns': selected_campaigns,
      'translate_ads': 'True',
      'translate_extensions': 'True',
      'translate_keywords': 'True',
  }

  data = urllib.parse.urlencode(data).encode('utf-8')
  request = urllib.request.Request(f'{_URL}/cost', data)
  request.add_header('Authorization', f'Bearer {token}')

  with urllib.request.urlopen(request) as response:
    assert (
        response.status == 200
    ), 'Got non-200 response from /cost'
    body = response.read()
    cost = json.loads(body)
    assert cost, (
        f'Could not get cost for {selected_accounts} / {selected_campaigns}')


@pytest.mark.systemtest
def test_list_glossaries(token: str) -> None:
  """Tests the list_glossaries endpoint."""
  request = urllib.request.Request(f'{_URL}/list_glossaries')
  request.add_header('Authorization', f'Bearer {token}')

  with urllib.request.urlopen(request) as response:
    assert (
        response.status == 200
    ), 'Got non-200 response from /list_glossaries'
    body = response.read()
    glossaries = json.loads(body)
    assert glossaries, 'Could not find glossaries'


@pytest.mark.systemtest
def test_run(token: str) -> None:
  """Tests the run endpoint."""
  selected_accounts = os.environ.get(_SELECTED_ACCOUNTS)
  selected_campaigns = os.environ.get(_SELECTED_CAMPAIGNS)

  data = {
      'source_language_code': 'en',
      'target_language_code': 'de',
      'workers_to_run': 'translationWorker',
      'shorten_translations_to_char_limit': 'True',
      'customer_ids': selected_accounts,
      'campaigns': selected_campaigns,
      'multiple_templates': 'False',
      'translate_ads': 'True',
      'translate_extensions': 'True',
      'translate_keywords': 'True',
  }

  data = urllib.parse.urlencode(data).encode('utf-8')
  request = urllib.request.Request(f'{_URL}/run', data)
  request.add_header('Authorization', f'Bearer {token}')

  with urllib.request.urlopen(request) as response:
    assert (
        response.status == 200
    ), 'Got non-200 response from /run'
    body = response.read()
    results = json.loads(body)
    assert results, (
        f'Could not run for {selected_accounts} / {selected_campaigns}')


@pytest.mark.systemtest
@pytest.mark.skipif(
    os.getenv('TEST_FAILURE_ALERTING') != 'TRUE',
    reason='Test failure alerting is not set to TRUE.',
)
def test_that_always_fails():
  """A deliberately failing test, to check alerts are sent when tests fail."""
  assert False

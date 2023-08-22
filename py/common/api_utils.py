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

"""Common utilities for REST HTTP clients."""

from typing import Any

import requests
from requests import adapters


_OAUTH2_TOKEN_URL = 'https://www.googleapis.com/oauth2/v3/token'
_RETRIES = 5
_BACKOFF_FACTOR = 1
_CODES_TO_RETRY = [
    429,  # Too many requests (rate limited)
    502,  # Bad gateway
    503,  # Temporarily unavailable
    504,  # Did not receive timely response
]


def refresh_access_token(credentials: dict[str, str]) -> str:
  """Requests an OAUTH2 access token.

  Args:
    credentials: A dictionary containing client_id, client_secret,
      and refresh_token

  Returns:
    An access token string, or empty string if the request failed.
  """
  payload = {
      'grant_type': 'refresh_token',
      'client_id': credentials['client_id'],
      'client_secret': credentials['client_secret'],
      'refresh_token': credentials['refresh_token'],
  }

  response = requests.post(_OAUTH2_TOKEN_URL, params=payload)
  response.raise_for_status()
  data = response.json()

  return data.get('access_token', '')


def validate_credentials(
    credentials: dict[str, str], required_keys: tuple[str, ...]) -> None:
  """Validates required fields are in the credentials dictionary.

  Args:
    credentials: A dictionary containing credentials key/value pairs.
    required_keys: A list of required credentials keys.

  Raises:
    AttributeError if any required keys are missing from credentials.
  """
  if not all(key in credentials for key in required_keys):
    raise AttributeError(
        'Missing required field. The required fields are: '
        f'{str(required_keys)}'
    )


def send_api_request(
    url: str,
    params: dict[str, Any],
    http_header: dict[str, str],
    method: str = 'POST') -> Any:
  """Call the requested API endpoint with the given parameters.

  Args:
    url: The API endpoint to call.
    params: The parameters to pass into the API call.
    http_header: The HTTP header to use in the call.
    method: The request method to use.

  Returns:
    The JSON data from the response (this can sometimes be a list or dictionary,
      depending on the API used).
  """
  session = requests.Session()

  retries = adapters.Retry(
      total=_RETRIES,
      backoff_factor=_BACKOFF_FACTOR,
      status_forcelist=_CODES_TO_RETRY)
  session.mount('https://', adapters.HTTPAdapter(max_retries=retries))
  headers = http_header
  response = session.request(
      url=url, method=method, json=params, headers=headers
  )

  response.raise_for_status()

  return response.json()

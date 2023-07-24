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

"""Tests for the api_utils module."""

import requests
import requests_mock
from common import api_utils
from absl.testing import absltest
from absl.testing import parameterized


class ApiUtilsTest(parameterized.TestCase):

  @parameterized.named_parameters(
      {
          'testcase_name': 'access_token_exists',
          'response_json': {'access_token': 'fake_access_token'},
          'expected_access_token': 'fake_access_token',
      },
      {
          'testcase_name': 'no_access_token',
          'response_json': {'Some other data': ''},
          'expected_access_token': '',
      },
  )
  @requests_mock.Mocker()
  def test_refresh_access_token(
      self, mock_requests, response_json, expected_access_token):

    fake_credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }

    mock_requests.post(
        'https://www.googleapis.com/oauth2/v3/token',
        json=response_json,
    )

    actual_access_token = api_utils.refresh_access_token(fake_credentials)

    self.assertEqual(actual_access_token, expected_access_token)

  @requests_mock.Mocker()
  def test_refresh_access_token_raises_error_for_status(self, mock_requests):

    fake_credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }

    mock_requests.post(
        'https://www.googleapis.com/oauth2/v3/token',
        status_code=401,
        json={'Error': 'Something went wrong'},
    )

    with self.assertRaises(requests.HTTPError):
      api_utils.refresh_access_token(fake_credentials)

  def test_validate_credentials(self):
    fake_credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
        }
    required_keys = ('client_id', 'client_secret', 'refresh_token')

    try:
      api_utils.validate_credentials(fake_credentials, required_keys)
    except AttributeError:
      self.fail('validate_credentials() raised AttributeError.')

  def test_validate_credentials_raises_error(self):
    fake_credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        }
    required_keys = ('client_id', 'client_secret', 'missing_credential')

    with self.assertRaises(AttributeError):
      api_utils.validate_credentials(fake_credentials, required_keys)

  @requests_mock.Mocker()
  def test_send_api_request(self, mock_requests):
    fake_credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }

    fake_params = {
        'query': 'SELECT * FROM CUSTOMER'
    }

    expected_response = {
        'data': 'some data',
        'info': 'some info',
    }

    mock_requests.post(
        'https://www.googleapis.com/v1/someapi',
        json=expected_response,
    )

    actual_response = api_utils.send_api_request(
        url='https://www.googleapis.com/v1/someapi',
        params=fake_params,
        http_header=fake_credentials,
        method='POST',
    )

    self.assertEqual(expected_response, actual_response)

  @requests_mock.Mocker()
  def test_send_api_request_raises_error_for_status(self, mock_requests):
    fake_credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }

    fake_params = {
        'query': 'SELECT * FROM CUSTOMER'
    }

    expected_response = {
        'data': 'some data',
        'info': 'some info',
    }

    mock_requests.post(
        'https://www.googleapis.com/v1/someapi',
        status_code=500,
        json=expected_response,
    )

    with self.assertRaises(requests.HTTPError):
      api_utils.send_api_request(
          url='https://www.googleapis.com/v1/someapi',
          params=fake_params,
          http_header=fake_credentials,
          method='POST',
      )


if __name__ == '__main__':
  absltest.main()

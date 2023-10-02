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

"""Tests for main."""

import http
import os
from unittest import mock
import urllib

import flask
import google.oauth2.id_token

from absl.testing import absltest
from keyword_platform.ui.py import main


class MainTest(absltest.TestCase):

  @mock.patch.object(flask, 'send_from_directory', autospec=True)
  def test_index(self, mock_send_from_directory):
    mock_index_page = mock.MagicMock()

    mock_send_from_directory.return_value = mock_index_page

    expected_index_page = mock_index_page
    actual_index_page = main.index()

    self.assertEqual(expected_index_page, actual_index_page)

  @mock.patch.object(flask, 'send_from_directory', autospec=True)
  def test_favicon(self, mock_send_from_directory):
    mock_favicon = mock.MagicMock()

    mock_send_from_directory.return_value = mock_favicon

    expected_favicon = mock_favicon
    actual_favicon = main.favicon()

    self.assertEqual(expected_favicon, actual_favicon)

  @mock.patch.dict(os.environ, {'BACKEND_URL': 'https://fake-url.a.run.app'})
  @mock.patch.object(google.oauth2.id_token, 'fetch_id_token', autospec=True)
  @mock.patch.object(urllib.request, 'urlopen', autospec=True)
  def test_proxy_get_request(self, mock_urlopen, mock_fetch_id_token):
    fake_id_token = '12345'
    mock_fetch_id_token.return_value = fake_id_token
    mock_urlopen.return_value = 'fake_response'

    expected_response = 'fake_response'
    expected_full_url = (
        'https://fake-url.a.run.app/run?endpoint=run&campaign_ids=123')
    expected_auth_header = 'Bearer 12345'

    actual_response = main.app.test_client().get(
        '/proxy?endpoint=run&campaign_ids=123')

    request_arg = mock_urlopen.call_args_list[0][0][0]
    actual_full_url = request_arg.full_url
    actual_auth_header = request_arg.headers['Authorization']

    self.assertEqual(expected_full_url, actual_full_url)
    self.assertEqual(expected_auth_header, actual_auth_header)
    self.assertEqual(expected_response, actual_response.data.decode('utf-8'))

  @mock.patch.dict(os.environ, {'BACKEND_URL': 'https://fake-url.a.run.app'})
  @mock.patch.object(google.oauth2.id_token, 'fetch_id_token', autospec=True)
  @mock.patch.object(urllib.request, 'urlopen', autospec=True)
  def test_proxy_post_request_form(self, mock_urlopen, mock_fetch_id_token):
    fake_id_token = '12345'
    mock_fetch_id_token.return_value = fake_id_token
    mock_urlopen.return_value = 'fake_response'

    expected_response = 'fake_response'
    expected_full_url = (
        'https://fake-url.a.run.app/run')
    expected_auth_header = 'Bearer 12345'
    expected_data = b'endpoint=run&campaign_ids=123'

    actual_response = main.app.test_client().post(
        '/proxy', data={
            'endpoint': 'run',
            'campaign_ids': '123'})

    request_arg = mock_urlopen.call_args_list[0][0][0]
    actual_full_url = request_arg.full_url
    actual_data = request_arg.data
    actual_auth_header = request_arg.headers['Authorization']

    self.assertEqual(expected_full_url, actual_full_url)
    self.assertEqual(expected_auth_header, actual_auth_header)
    self.assertEqual(expected_response, actual_response.data.decode('utf-8'))
    self.assertEqual(expected_data, actual_data)

  @mock.patch.dict(os.environ, {'BACKEND_URL': 'https://fake-url.a.run.app'})
  @mock.patch.object(google.oauth2.id_token, 'fetch_id_token', autospec=True)
  @mock.patch.object(urllib.request, 'urlopen', autospec=True)
  def test_proxy_post_request_json(self, mock_urlopen, mock_fetch_id_token):
    fake_id_token = '12345'
    mock_fetch_id_token.return_value = fake_id_token
    mock_urlopen.return_value = 'fake_response'

    expected_response = 'fake_response'
    expected_full_url = (
        'https://fake-url.a.run.app/run')
    expected_auth_header = 'Bearer 12345'
    expected_data = b'campaign_ids=123&endpoint=run'

    actual_response = main.app.test_client().post(
        '/proxy', json={
            'endpoint': 'run',
            'campaign_ids': '123'})

    request_arg = mock_urlopen.call_args_list[0][0][0]
    actual_full_url = request_arg.full_url
    actual_data = request_arg.data
    actual_auth_header = request_arg.headers['Authorization']

    self.assertEqual(expected_full_url, actual_full_url)
    self.assertEqual(expected_auth_header, actual_auth_header)
    self.assertEqual(expected_response, actual_response.data.decode('utf-8'))
    self.assertEqual(expected_data, actual_data)


if __name__ == '__main__':
  absltest.main()

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

"""Tests for OAuth flow."""

from unittest import mock

from absl import flags
from absl.testing import flagsaver
import google_auth_oauthlib
import oauthlib.oauth2.rfc6749.errors as auth_errors

from absl.testing import absltest
from keyword_platform.setup.utils import oauth_flow

FLAGS = flags.FLAGS

FLAGS.client_id = 'fake_client_id'
FLAGS.client_secret = 'fake_client_secret'
FLAGS.state = None

# Required flags have to be set before absltest.main(). So save initial
# values, set required to workaround value, then reset to initial values in
# setUp.
_INITIAL_FLAG_VALUES = flagsaver.save_flag_values()

_FAKE_CODE = '1/foo'

_FAKE_AUTH_URL_RESULT = f'http://localhost:8080/?state=bar&code={_FAKE_CODE}'


class OAuthFlowTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    flagsaver.restore_flag_values(_INITIAL_FLAG_VALUES)
    self.fake_flow = self.enter_context(
        mock.patch.object(google_auth_oauthlib, 'flow', autospec=True)
    )
    self.fake_flow.Flow.from_client_config.return_value.authorization_url.return_value = (
        'fake_authorization_url',
        None,
    )

  @mock.patch('builtins.input', lambda _: _FAKE_AUTH_URL_RESULT)
  def test_flow_fetches_code(self):
    self.fake_flow.Flow.from_client_config.return_value.fetch_token.return_value = (
        'fake_token'
    )
    oauth_flow.OAuthFlow(
        FLAGS.client_id, FLAGS.client_secret, FLAGS.state
    ).get_refresh_token_from_flow()

    self.fake_flow.Flow.from_client_config.return_value.fetch_token.assert_called_once_with(
        code=_FAKE_CODE
    )

  @mock.patch('builtins.input', lambda _: _FAKE_AUTH_URL_RESULT)
  def test_flow_raises_invalid_grant_error(self):
    self.fake_flow.Flow.from_client_config.return_value.fetch_token.side_effect = (
        auth_errors.InvalidGrantError()
    )

    with self.assertRaises(auth_errors.InvalidGrantError):
      oauth_flow.OAuthFlow(
          FLAGS.client_id, FLAGS.client_secret, FLAGS.state
      ).get_refresh_token_from_flow()

      # Still expecting three attempts.
      self.fake_flow.Flow.from_client_config.return_value.fetch_token.call_count = (
          3
      )

  @mock.patch('builtins.input', lambda _: _FAKE_AUTH_URL_RESULT)
  def test_flow_raises_missing_code_error(self):
    self.fake_flow.Flow.from_client_config.return_value.fetch_token.side_effect = (
        auth_errors.MissingCodeError()
    )

    with self.assertRaises(auth_errors.MissingCodeError):
      oauth_flow.OAuthFlow(
          FLAGS.client_id, FLAGS.client_secret, FLAGS.state
      ).get_refresh_token_from_flow()

      # Still expecting three attempts.
      self.fake_flow.Flow.from_client_config.return_value.fetch_token.call_count = (
          3
      )

  def test_write_refresh_token_to_file(self):
    mock_file_handle = mock.mock_open()

    with mock.patch('builtins.open', mock_file_handle, create=True):
      oauth_flow._write_refresh_token_to_file('fake_refresh_token')

    mock_file_handle.assert_called_once_with('refresh_token.txt', 'w')
    mock_file_handle().write.assert_called_once_with('fake_refresh_token')

  @mock.patch('builtins.input', lambda _: _FAKE_AUTH_URL_RESULT)
  def test_retry_on_failure(self):
    self.fake_flow.Flow.from_client_config.return_value.fetch_token.side_effect = [
        auth_errors.InvalidGrantError(),
        auth_errors.MissingCodeError(),
        'fake_token',
    ]

    oauth_flow.OAuthFlow(
        FLAGS.client_id, FLAGS.client_secret, FLAGS.state
    ).get_refresh_token_from_flow()

    # Expecting three attempts.
    self.fake_flow.Flow.from_client_config.return_value.fetch_token.assert_has_calls([
        mock.call(code=_FAKE_CODE),
        mock.call(code=_FAKE_CODE),
        mock.call(code=_FAKE_CODE),
    ])


if __name__ == '__main__':
  absltest.main()

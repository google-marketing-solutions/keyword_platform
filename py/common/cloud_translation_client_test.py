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

"""Tests for the CloudTranslationClient class."""

from unittest import mock

import pandas as pd

from absl.testing import absltest
from ..common import api_utils
from ..common import cloud_translation_client as cloud_translation_client_lib
from ..data_models import translation_frame as translation_frame_lib


class CloudTranslationClientTest(absltest.TestCase):

  def test_init_raises_exception_when_credentials_invalid(self):
    invalid_credentials = {
        'client_id': 'fake_client_id',
        'missing_client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'

    with self.assertRaises(AttributeError):
      cloud_translation_client_lib.CloudTranslationClient(
          credentials=invalid_credentials, gcp_project_name=gcp_project_name)

  @mock.patch.object(api_utils, 'refresh_access_token', autospec=True)
  @mock.patch.object(api_utils, 'send_api_request', autospec=True)
  def test_translate(self, mock_send_api_request, mock_refresh_access_token):
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    source_language = 'en'
    target_language = 'es'
    api_version = 3
    batch_char_limit = 10  # Set to smaller size for testing

    cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=credentials,
            gcp_project_name=gcp_project_name,
            api_version=api_version,
            batch_char_limit=batch_char_limit))

    translation_frame = translation_frame_lib.TranslationFrame({
        'email': [(0, 'Keyword'), (2, 'Keyword')],
        'fast': [(1, 'Keyword')],
        'efficient': [(2, 'Keyword')],
    })

    expected_translated_df = pd.DataFrame({
        'source_term': ['email', 'fast', 'efficient'],
        'target_terms': [{'es': 'correo electrónico'},
                         {'es': 'rápido'},
                         {'es': 'eficiente'}],
        'dataframe_locations': [
            [(0, 'Keyword'), (2, 'Keyword')],
            [(1, 'Keyword')],
            [(2, 'Keyword')]],
        })

    mock_send_api_request.side_effect = [
        {'translations': [
            {'translatedText': 'correo electrónico'},
            {'translatedText': 'rápido'}]},
        {'translations': [
            {'translatedText': 'eficiente'}]}]

    mock_refresh_access_token.return_value = 'fake_access_token'

    expected_api_calls = [
        mock.call(
            ('https://translate.googleapis.com/v3/projects/fake_gcp_project'
             ':translateText'),
            {
                'contents': ['email', 'fast'],
                'mimeType': 'text/plain',
                'parent': 'projects/fake_gcp_project',
                'source_language_code': 'en',
                'target_language_code': 'es',
            },
            {
                'Authorization': 'Bearer fake_access_token',
                'Content-Type': 'application/json',
            }),
        mock.call(
            ('https://translate.googleapis.com/v3/projects/fake_gcp_project'
             ':translateText'),
            {
                'contents': ['efficient'],
                'mimeType': 'text/plain',
                'parent': 'projects/fake_gcp_project',
                'source_language_code': 'en',
                'target_language_code': 'es',
            },
            {
                'Authorization': 'Bearer fake_access_token',
                'Content-Type': 'application/json',
            })
    ]

    cloud_translation_client.translate(
        translation_frame=translation_frame,
        source_language_code=source_language,
        target_language_code=target_language)

    actual_translated_df = translation_frame.df()

    # Asserts expected translations added to translation frame
    pd.util.testing.assert_frame_equal(
        expected_translated_df, actual_translated_df, check_index_type=False)

    # Asserts mock calls (covering batching logic)
    mock_send_api_request.assert_has_calls(expected_api_calls, any_order=True)


if __name__ == '__main__':
  absltest.main()

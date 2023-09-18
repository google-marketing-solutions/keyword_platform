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
import requests

from absl.testing import absltest
from common import api_utils
from common import cloud_translation_client as cloud_translation_client_lib
from common import vertex_client
from data_models import translation_frame as translation_frame_lib
from data_models import translation_metadata


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
        'email': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Keyword'), (2, 'Keyword')],
            char_limit=90),
        'fast': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')], char_limit=90),
        'efficient': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(2, 'Keyword')], char_limit=90),
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
        'char_limit': [90, 90, 90],
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
    pd.testing.assert_frame_equal(
        expected_translated_df, actual_translated_df, check_index_type=False)

    # Asserts mock calls (covering batching logic)
    mock_send_api_request.assert_has_calls(expected_api_calls, any_order=True)

  @mock.patch.object(api_utils, 'refresh_access_token', autospec=True)
  @mock.patch.object(api_utils, 'send_api_request', autospec=True)
  def test_translate_exits_early_on_api_error(
      self, mock_send_api_request, mock_refresh_access_token):
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
        'email': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Keyword'), (2, 'Keyword')],
            char_limit=90),
        'fast': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')], char_limit=90),
        'efficient': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(2, 'Keyword')], char_limit=90),
    })

    expected_translated_df = pd.DataFrame({
        'source_term': ['email', 'fast', 'efficient'],
        'target_terms': [{'es': 'correo electrónico'},
                         {'es': 'rápido'},
                         {}],
        'dataframe_locations': [
            [(0, 'Keyword'), (2, 'Keyword')],
            [(1, 'Keyword')],
            [(2, 'Keyword')]],
        'char_limit': [90, 90, 90],
        })

    mock_send_api_request.side_effect = [
        {'translations': [
            {'translatedText': 'correo electrónico'},
            {'translatedText': 'rápido'}]},
        requests.exceptions.HTTPError()]

    mock_refresh_access_token.return_value = 'fake_access_token'

    try:
      cloud_translation_client.translate(
          translation_frame=translation_frame,
          source_language_code=source_language,
          target_language_code=target_language)
    except requests.exceptions.HTTPError:
      # Simulating a caller catching the error and patching in the partially
      # complete data.
      print('Skipping exception')

    actual_translated_df = translation_frame.df()

    # Asserts expected translations added to translation frame
    pd.testing.assert_frame_equal(
        expected_translated_df, actual_translated_df, check_index_type=False)
    # Asserts the number of characters sent to the Cloud Translation API.
    self.assertEqual(cloud_translation_client.get_translated_characters(), 9)

  @mock.patch.object(api_utils, 'refresh_access_token', autospec=True)
  @mock.patch.object(api_utils, 'send_api_request', autospec=True)
  def test_translate_shortens_translations(
      self, mock_send_api_request, mock_refresh_access_token):
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    source_language = 'en'
    target_language = 'es'
    api_version = 3
    batch_char_limit = 2500

    mock_vertex_client = mock.create_autospec(vertex_client.VertexClient)
    mock_vertex_client.shorten_text_to_char_limit.side_effect = [
        ['shortened1'],
        ['shortened2', 'shortened3'],
    ]

    cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=credentials,
            gcp_project_name=gcp_project_name,
            api_version=api_version,
            batch_char_limit=batch_char_limit,
            vertex_client=mock_vertex_client,
        )
    )

    translation_frame = translation_frame_lib.TranslationFrame({
        'term_to_overflow_1': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Keyword'), (2, 'Keyword')],
            char_limit=10),
        'term_that_fits_1': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')], char_limit=90),
        'term_to_overflow_2': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(3, 'Keyword')], char_limit=15),
        'term_that_fits_2': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(4, 'Keyword')], char_limit=90),
        'term_to_overflow_3': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(5, 'Keyword')], char_limit=15),
    })

    expected_translated_df = pd.DataFrame({
        'source_term': ['term_to_overflow_1',
                        'term_that_fits_1',
                        'term_to_overflow_2',
                        'term_that_fits_2',
                        'term_to_overflow_3'],
        'target_terms': [{'es': 'shortened1'},
                         {'es': 'untruncated_translation_1'},
                         {'es': 'shortened2'},
                         {'es': 'untruncated_translation_2'},
                         {'es': 'shortened3'}],
        'dataframe_locations': [
            [(0, 'Keyword'), (2, 'Keyword')],
            [(1, 'Keyword')],
            [(3, 'Keyword')],
            [(4, 'Keyword')],
            [(5, 'Keyword')]],
        'char_limit': [10, 90, 15, 90, 15],
        })

    mock_send_api_request.side_effect = [
        {'translations': [
            {'translatedText': 'some long overflowing translation 1'},
            {'translatedText': 'untruncated_translation_1'},
            {'translatedText': 'some long overflowing translation 2'},
            {'translatedText': 'untruncated_translation_2'},
            {'translatedText': 'some long overflowing translation 3'}]},]

    mock_refresh_access_token.return_value = 'fake_access_token'

    cloud_translation_client.translate(
        translation_frame=translation_frame,
        source_language_code=source_language,
        target_language_code=target_language)

    actual_translated_df = translation_frame.df()

    # Asserts expected translations added to translation frame.
    pd.testing.assert_frame_equal(
        expected_translated_df, actual_translated_df, check_index_type=False)
    # Asserts the number of characters sent to the Cloud Translation API.
    self.assertEqual(cloud_translation_client.get_translated_characters(), 86)

if __name__ == '__main__':
  absltest.main()

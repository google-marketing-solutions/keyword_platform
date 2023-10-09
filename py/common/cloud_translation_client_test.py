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
import os
from unittest import mock

import pandas as pd
import requests

from absl.testing import absltest
from absl.testing import parameterized
from common import api_utils
from common import cloud_translation_client as cloud_translation_client_lib
from common import vertex_client
from data_models import translation_frame as translation_frame_lib
from data_models import translation_metadata


class CloudTranslationClientTest(parameterized.TestCase):

  def test_init_raises_exception_when_credentials_invalid(self):
    invalid_credentials = {
        'client_id': 'fake_client_id',
        'missing_client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    gcp_region = 'fake_gcp_region'

    with self.assertRaises(AttributeError):
      cloud_translation_client_lib.CloudTranslationClient(
          credentials=invalid_credentials,
          gcp_project_name=gcp_project_name,
          gcp_region=gcp_region,
      )

  @parameterized.named_parameters(
      {
          'testcase_name': 'without_glossary',
          'mock_glossary_id': '',
          'expected_api_calls': [
              mock.call(
                  (
                      'https://translate.googleapis.com/v3/projects/fake_gcp_project/'
                      'locations/fake_gcp_region:translateText'
                  ),
                  {
                      'contents': ['email', 'fast'],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake_gcp_project',
                      'source_language_code': 'en',
                      'target_language_code': 'available_language',
                  },
                  {
                      'Authorization': 'Bearer fake_access_token',
                      'Content-Type': 'application/json',
                  },
              ),
              mock.call(
                  (
                      'https://translate.googleapis.com/v3/projects/fake_gcp_project/'
                      'locations/fake_gcp_region:translateText'
                  ),
                  {
                      'contents': ['efficient'],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake_gcp_project',
                      'source_language_code': 'en',
                      'target_language_code': 'available_language',
                  },
                  {
                      'Authorization': 'Bearer fake_access_token',
                      'Content-Type': 'application/json',
                  },
              ),
          ],
      },
      {
          'testcase_name': 'with_glossary',
          'mock_glossary_id': 'en-to-available_language-glossary',
          'expected_api_calls': [
              mock.call(
                  (
                      'https://translate.googleapis.com/v3/projects/fake_gcp_project/'
                      'locations/fake_gcp_region:translateText'
                  ),
                  {
                      'contents': ['email', 'fast'],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake_gcp_project',
                      'source_language_code': 'en',
                      'target_language_code': 'available_language',
                      'glossaryConfig': {
                          'glossary': 'projects/fake_gcp_project/locations/fake_gcp_region/glossaries/en-to-available_language-glossary',
                          'ignore_case': False,
                      },
                  },
                  {
                      'Authorization': 'Bearer fake_access_token',
                      'Content-Type': 'application/json',
                  },
              ),
              mock.call(
                  (
                      'https://translate.googleapis.com/v3/projects/fake_gcp_project/'
                      'locations/fake_gcp_region:translateText'
                  ),
                  {
                      'contents': ['efficient'],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake_gcp_project',
                      'source_language_code': 'en',
                      'target_language_code': 'available_language',
                      'glossaryConfig': {
                          'glossary': 'projects/fake_gcp_project/locations/fake_gcp_region/glossaries/en-to-available_language-glossary',
                          'ignore_case': False,
                      },
                  },
                  {
                      'Authorization': 'Bearer fake_access_token',
                      'Content-Type': 'application/json',
                  },
              ),
          ],
      },
  )
  @mock.patch.object(api_utils, 'refresh_access_token', autospec=True)
  @mock.patch.object(api_utils, 'send_api_request', autospec=True)
  def test_translate(
      self,
      mock_send_api_request,
      mock_refresh_access_token,
      mock_glossary_id,
      expected_api_calls,
  ):
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    gcp_region = 'fake_gcp_region'
    source_language = 'en'
    target_language = 'available_language'
    api_version = 3
    batch_char_limit = 10  # Set to smaller size for testing

    cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=credentials,
            gcp_project_name=gcp_project_name,
            gcp_region=gcp_region,
            api_version=api_version,
            batch_char_limit=batch_char_limit,
        )
    )

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
        'target_terms': [
            {'available_language': 'correo electrónico'},
            {'available_language': 'rápido'},
            {'available_language': 'eficiente'},
        ],
        'dataframe_locations': [
            [(0, 'Keyword'), (2, 'Keyword')],
            [(1, 'Keyword')],
            [(2, 'Keyword')],
        ],
        'char_limit': [90, 90, 90],
    })

    mock_send_api_request.side_effect = [
        {
            'translations': [
                {'translatedText': 'correo electrónico'},
                {'translatedText': 'rápido'},
            ],
            'glossaryTranslations': [
                {'translatedText': 'correo electrónico'},
                {'translatedText': 'rápido'},
            ],
        },
        {
            'translations': [{'translatedText': 'eficiente'}],
            'glossaryTranslations': [{'translatedText': 'eficiente'}],
        },
    ]

    mock_refresh_access_token.return_value = 'fake_access_token'

    with mock.patch.object(
        vertex_client,
        'AVAILABLE_LANGUAGES',
        new=frozenset(['available_language']),
    ):
      cloud_translation_client.translate(
          translation_frame=translation_frame,
          source_language_code=source_language,
          target_language_code=target_language,
          glossary_id=mock_glossary_id,
      )

    actual_translated_df = translation_frame.df()

    # Asserts expected translations added to translation frame
    pd.testing.assert_frame_equal(
        expected_translated_df, actual_translated_df, check_index_type=False)

    # Asserts mock calls (covering batching logic)
    mock_send_api_request.assert_has_calls(expected_api_calls, any_order=True)

  @mock.patch.object(api_utils, 'refresh_access_token', autospec=True)
  @mock.patch.object(api_utils, 'send_api_request', autospec=True)
  def test_translate_exits_early_on_api_error(
      self,
      mock_send_api_request,
      mock_refresh_access_token,
  ):
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    gcp_region = 'fake_gcp_region'
    source_language = 'en'
    target_language = 'available_language'
    api_version = 3
    batch_char_limit = 10  # Set to smaller size for testing

    cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=credentials,
            gcp_project_name=gcp_project_name,
            gcp_region=gcp_region,
            api_version=api_version,
            batch_char_limit=batch_char_limit,
        )
    )

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
        'target_terms': [
            {'available_language': 'correo electrónico'},
            {'available_language': 'rápido'},
            {},
        ],
        'dataframe_locations': [
            [(0, 'Keyword'), (2, 'Keyword')],
            [(1, 'Keyword')],
            [(2, 'Keyword')],
        ],
        'char_limit': [90, 90, 90],
    })

    mock_send_api_request.side_effect = [
        {'translations': [
            {'translatedText': 'correo electrónico'},
            {'translatedText': 'rápido'}]},
        requests.exceptions.HTTPError()]

    mock_refresh_access_token.return_value = 'fake_access_token'

    with mock.patch.object(
        vertex_client,
        'AVAILABLE_LANGUAGES',
        new=frozenset(['available_language']),
    ):
      try:
        cloud_translation_client.translate(
            translation_frame=translation_frame,
            source_language_code=source_language,
            target_language_code=target_language,
        )
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
      self,
      mock_send_api_request,
      mock_refresh_access_token,
  ):
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    gcp_region = 'fake_gcp_region'
    source_language = 'en'
    target_language = 'available_language'
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
            gcp_region=gcp_region,
            api_version=api_version,
            batch_char_limit=batch_char_limit,
            vertex_client=mock_vertex_client,
            shorten_translations_to_char_limit=True,
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
        'source_term': [
            'term_to_overflow_1',
            'term_that_fits_1',
            'term_to_overflow_2',
            'term_that_fits_2',
            'term_to_overflow_3',
        ],
        'target_terms': [
            {'available_language': 'shortened1'},
            {'available_language': 'untruncated_translation_1'},
            {'available_language': 'shortened2'},
            {'available_language': 'untruncated_translation_2'},
            {'available_language': 'shortened3'},
        ],
        'dataframe_locations': [
            [(0, 'Keyword'), (2, 'Keyword')],
            [(1, 'Keyword')],
            [(3, 'Keyword')],
            [(4, 'Keyword')],
            [(5, 'Keyword')],
        ],
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

    with mock.patch.object(
        vertex_client,
        'AVAILABLE_LANGUAGES',
        new=frozenset(['available_language']),
    ):
      cloud_translation_client.translate(
          translation_frame=translation_frame,
          source_language_code=source_language,
          target_language_code=target_language,
      )

    actual_translated_df = translation_frame.df()

    # Asserts expected translations added to translation frame.
    pd.testing.assert_frame_equal(
        expected_translated_df, actual_translated_df, check_index_type=False)
    # Asserts the number of characters sent to the Cloud Translation API.
    self.assertEqual(cloud_translation_client.get_translated_characters(), 86)

  @parameterized.named_parameters(
      {
          'testcase_name': 'unsupported_language',
          'mock_target_language': 'unsupported_language',
          'mock_shorten_translations_to_char_limit': True,
      },
      {
          'testcase_name': 'opted_out_of_shorten_overflowing_translations',
          'mock_target_language': 'available_language',
          'mock_shorten_translations_to_char_limit': False,
      },
  )
  @mock.patch.object(api_utils, 'refresh_access_token', autospec=True)
  @mock.patch.object(api_utils, 'send_api_request', autospec=True)
  def test_shorten_text_to_char_limit_not_called_unsupported_language(
      self,
      mock_send_api_request,
      mock_refresh_access_token,
      mock_target_language,
      mock_shorten_translations_to_char_limit,
  ):
    del mock_send_api_request, mock_refresh_access_token
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    gcp_region = 'fake_gcp_region'
    source_language = 'en'
    target_language = mock_target_language
    shorten_translations_to_char_limit = mock_shorten_translations_to_char_limit
    api_version = 3
    batch_char_limit = 10  # Set to smaller size for testing

    with mock.patch.object(
        vertex_client,
        'AVAILABLE_LANGUAGES',
        new=frozenset(['available_language']),
    ):
      cloud_translation_client = cloud_translation_client_lib.CloudTranslationClient(
          credentials=credentials,
          gcp_project_name=gcp_project_name,
          gcp_region=gcp_region,
          api_version=api_version,
          batch_char_limit=batch_char_limit,
          shorten_translations_to_char_limit=shorten_translations_to_char_limit,
      )

    translation_frame = translation_frame_lib.TranslationFrame({
        'email': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Keyword'), (2, 'Keyword')],
            char_limit=90,
        ),
        'fast': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')], char_limit=90
        ),
        'efficient': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(2, 'Keyword')], char_limit=90
        ),
    })

    cloud_translation_client.translate(
        translation_frame=translation_frame,
        source_language_code=source_language,
        target_language_code=target_language,
    )

    mock_vertex_client = mock.create_autospec(vertex_client.VertexClient)
    mock_vertex_client.shorten_text_to_char_limit.assert_not_called()

  @parameterized.named_parameters(
      {
          'testcase_name': 'glossaries_exist',
          'expected_response': {
              'glossaries': [
                  {
                      'name': 'projects/fake-project-id/locations/fake-region/glossaries/fake-glosssary-1',
                      'languagePair': {
                          'sourceLanguageCode': 'en',
                          'targetLanguageCode': 'ru',
                      },
                      'inputConfig': {
                          'gcsSource': {
                              'inputUri': (
                                  'gs://bucket-name/glossary-file-name-1'
                              )
                          }
                      },
                      'entryCount': 9603,
                  },
                  {
                      'name': 'projects/fake-project-id/locations/fake-region/glossaries/fake-glosssary-2',
                      'languagePair': {
                          'sourceLanguageCode': 'en',
                          'targetLanguageCode': 'es',
                      },
                      'inputConfig': {
                          'gcsSource': {
                              'inputUri': (
                                  'gs://bucket-name/glossary-file-name-2'
                              )
                          }
                      },
                      'entryCount': 9604,
                  },
              ]
          },
          'expected_result': ['fake-glosssary-1', 'fake-glosssary-2'],
      },
      {
          'testcase_name': 'glossaries_does_not_exist',
          'expected_response': {'glossaries': []},
          'expected_result': [],
      },
  )
  @mock.patch.object(api_utils, 'refresh_access_token', autospec=True)
  @mock.patch.object(api_utils, 'send_api_request', autospec=True)
  def test_list_glossaies(
      self,
      mock_send_api_request,
      mock_refresh_access_token,
      expected_response,
      expected_result,
  ):
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    gcp_region = 'fake_gcp_region'
    api_version = 3
    mock_refresh_access_token.return_value = 'fake_access_token'
    mock_send_api_request.return_value = expected_response
    cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=credentials,
            gcp_project_name=gcp_project_name,
            gcp_region=gcp_region,
            api_version=api_version,
        )
    )
    actual_result = cloud_translation_client.list_glossaries()

    self.assertEqual(actual_result, expected_result)


if __name__ == '__main__':
  absltest.main()

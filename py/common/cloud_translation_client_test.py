# Copyright 2024 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the CloudTranslationClient class."""
import os
from unittest import mock

import google.api_core
import pandas as pd
import requests

from absl.testing import absltest
from absl.testing import parameterized
from common import api_utils
from common import cloud_translation_client as cloud_translation_client_lib
from common import vertex_client
from data_models import translation_frame as translation_frame_lib
from data_models import translation_metadata


_FAKE_PROJECT = 'fake-gcp-project'
_FAKE_BUCKET = 'fake-bucket'
_FAKE_REGION = 'fake-gcp-region'
_FAKE_PARENT = f'projects/{_FAKE_PROJECT}/locations/{_FAKE_REGION}'
_FAKE_GLOSSARY_ID = 'en-to-de-glossary'
_FAKE_GLOSSARY_NAME = f'{_FAKE_PARENT}/glossaries/{_FAKE_GLOSSARY_ID}'
_FAKE_API_VERSION = '3'
_FAKE_CREDENTIALS = {
    'client_id': 'fake_client_id',
    'client_secret': 'fake_client_secret',
    'refresh_token': 'fake_refresh_token',
}
_FAKE_BATCH_CHAR_LIMIT = 10
_FAKE_ACCESS_TOKEN = 'fake_access_token'
_FAKE_GLOSSARY_URI = f'gs://{_FAKE_BUCKET}/{_FAKE_GLOSSARY_ID}.csv'


class CloudTranslationClientTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    self.mock_refresh_access_token = self.enter_context(
        mock.patch.object(
            api_utils,
            'refresh_access_token',
            autospec=True,
            return_value=_FAKE_ACCESS_TOKEN,
        )
    )
    self.mock_send_api_request = self.enter_context(
        mock.patch.object(api_utils, 'send_api_request', autospec=True)
    )
    self.cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=_FAKE_CREDENTIALS,
            gcp_project_name=_FAKE_PROJECT,
            gcp_region=_FAKE_REGION,
            api_version=_FAKE_API_VERSION,
            batch_char_limit=_FAKE_BATCH_CHAR_LIMIT,
        )
    )

  def test_init_raises_exception_when_credentials_invalid(self):
    invalid_credentials = {
        'client_id': 'fake_client_id',
        'missing_client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }

    with self.assertRaises(AttributeError):
      cloud_translation_client_lib.CloudTranslationClient(
          credentials=invalid_credentials,
          gcp_project_name=_FAKE_PROJECT,
          gcp_region=_FAKE_REGION,
      )

  @parameterized.named_parameters(
      {
          'testcase_name': 'without_glossary',
          'mock_glossary_id': '',
          'expected_api_calls': [
              mock.call(
                  (
                      'https://translate.googleapis.com/v3/projects/fake-gcp-project/'
                      'locations/fake-gcp-region:translateText'
                  ),
                  {
                      'contents': ['email', 'fast'],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake-gcp-project',
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
                      'https://translate.googleapis.com/v3/projects/fake-gcp-project/'
                      'locations/fake-gcp-region:translateText'
                  ),
                  {
                      'contents': ['efficient'],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake-gcp-project',
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
                      'https://translate.googleapis.com/v3/projects/fake-gcp-project/'
                      'locations/fake-gcp-region:translateText'
                  ),
                  {
                      'contents': ['email', 'fast'],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake-gcp-project',
                      'source_language_code': 'en',
                      'target_language_code': 'available_language',
                      'glossaryConfig': {
                          'glossary': 'projects/fake-gcp-project/locations/fake-gcp-region/glossaries/en-to-available_language-glossary',
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
                      'https://translate.googleapis.com/v3/projects/fake-gcp-project/'
                      'locations/fake-gcp-region:translateText'
                  ),
                  {
                      'contents': ['efficient'],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake-gcp-project',
                      'source_language_code': 'en',
                      'target_language_code': 'available_language',
                      'glossaryConfig': {
                          'glossary': 'projects/fake-gcp-project/locations/fake-gcp-region/glossaries/en-to-available_language-glossary',
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
  def test_translate(
      self,
      mock_glossary_id,
      expected_api_calls,
  ):
    source_language = 'en'
    target_language = 'available_language'

    translation_frame = translation_frame_lib.TranslationFrame({
        'email': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Keyword'), (2, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
        'fast': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
        'efficient': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(2, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
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
        'keyword_insertion_keys': [{}, {}, {}],
    })

    self.mock_send_api_request.side_effect = [
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

    with mock.patch.object(
        vertex_client,
        'AVAILABLE_LANGUAGES',
        new=frozenset(['available_language']),
    ):
      self.cloud_translation_client.translate(
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
    self.mock_send_api_request.assert_has_calls(
        expected_api_calls, any_order=True
    )

  @parameterized.named_parameters(
      {
          'testcase_name': 'without_glossary',
          'mock_glossary_id': '',
          'expected_api_calls': [
              mock.call(
                  (
                      'https://translate.googleapis.com/v3/projects/fake-gcp-project/'
                      'locations/fake-gcp-region:translateText'
                  ),
                  {
                      'contents': [
                          'Buy {0: now}',
                          (
                              'Data centers located in {0:denver}, {1: austin},'
                              ' and {2: kansas city }'
                          ),
                          'Sign up now',
                      ],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake-gcp-project',
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
                      'https://translate.googleapis.com/v3/projects/fake-gcp-project/'
                      'locations/fake-gcp-region:translateText'
                  ),
                  {
                      'contents': ['Get {KeyWord: now}'],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake-gcp-project',
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
                      'https://translate.googleapis.com/v3/projects/fake-gcp-project/'
                      'locations/fake-gcp-region:translateText'
                  ),
                  {
                      'contents': [
                          'Buy {0: now}',
                          (
                              'Data centers located in {0:denver}, {1: austin},'
                              ' and {2: kansas city }'
                          ),
                          'Sign up now',
                      ],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake-gcp-project',
                      'source_language_code': 'en',
                      'target_language_code': 'available_language',
                      'glossaryConfig': {
                          'glossary': 'projects/fake-gcp-project/locations/fake-gcp-region/glossaries/en-to-available_language-glossary',
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
                      'https://translate.googleapis.com/v3/projects/fake-gcp-project/'
                      'locations/fake-gcp-region:translateText'
                  ),
                  {
                      'contents': ['Get {KeyWord: now}'],
                      'mimeType': 'text/plain',
                      'parent': 'projects/fake-gcp-project',
                      'source_language_code': 'en',
                      'target_language_code': 'available_language',
                      'glossaryConfig': {
                          'glossary': 'projects/fake-gcp-project/locations/fake-gcp-region/glossaries/en-to-available_language-glossary',
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
  def test_translate_keyword_insertion(
      self,
      mock_glossary_id,
      expected_api_calls,
  ):
    source_language = 'en'
    target_language = 'available_language'

    translation_frame = translation_frame_lib.TranslationFrame({
        'Buy {0: now}': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Headline 1'), (2, 'Keyword')],
            char_limit=30,
            keyword_insertion_keys={'0': 'Keyword'},
        ),
        (
            'Data centers located in {0:denver}, {1: austin}, and {2: kansas'
            ' city }'
        ): translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Description 1')],
            char_limit=90,
            keyword_insertion_keys={
                '0': 'Keyword',
                '1': 'Keyword',
                '2': 'KeyWord',
            },
        ),
        'Sign up now': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(2, 'Headline 1')],
            char_limit=30,
            keyword_insertion_keys={},
        ),
        'Get {KeyWord: now}': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(3, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
    })

    expected_translated_df = pd.DataFrame({
        'source_term': [
            'Buy {0: now}',
            (
                'Data centers located in {0:denver}, {1: austin}, and {2:'
                ' kansas city }'
            ),
            'Sign up now',
            'Get {KeyWord: now}',
        ],
        'target_terms': [
            {'available_language': 'Comprar {0: ahora}'},
            {
                'available_language': (
                    'Centros de datos ubicados en {0:denver}, {1: austin} y {2:'
                    ' kansas city}'
                )
            },
            {'available_language': 'Regístrese Ahora'},
            {'available_language': 'Obtenga {Palabra clave: ahora}'},
        ],
        'dataframe_locations': [
            [(0, 'Headline 1'), (2, 'Keyword')],
            [(1, 'Description 1')],
            [(2, 'Headline 1')],
            [(3, 'Keyword')],
        ],
        'char_limit': [30, 90, 30, 90],
        'keyword_insertion_keys': [
            {'0': 'Keyword'},
            {
                '0': 'Keyword',
                '1': 'Keyword',
                '2': 'KeyWord',
            },
            {},
            {},
        ],
    })

    self.mock_send_api_request.side_effect = [
        {
            'translations': [
                {'translatedText': 'Comprar {0: ahora}'},
                {
                    'translatedText': (
                        'Centros de datos ubicados en {0:denver}, {1: austin} y'
                        ' {2: kansas city}'
                    )
                },
                {'translatedText': 'Regístrese Ahora'},
            ],
            'glossaryTranslations': [
                {'translatedText': 'Comprar {0: ahora}'},
                {
                    'translatedText': (
                        'Centros de datos ubicados en {0:denver}, {1: austin} y'
                        ' {2: kansas city}'
                    )
                },
                {'translatedText': 'Regístrese Ahora'},
            ],
        },
        {
            'translations': [
                {'translatedText': 'Obtenga {Palabra clave: ahora}'}
            ],
            'glossaryTranslations': [
                {'translatedText': 'Obtenga {Palabra clave: ahora}'}
            ],
        },
    ]

    with mock.patch.object(
        vertex_client,
        'AVAILABLE_LANGUAGES',
        new=frozenset(['available_language']),
    ):
      self.cloud_translation_client._batch_char_limit = 93
      self.cloud_translation_client.translate(
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
    self.mock_send_api_request.assert_has_calls(
        expected_api_calls, any_order=True
    )

  def test_translate_exits_early_on_api_error(self):
    source_language = 'en'
    target_language = 'available_language'

    translation_frame = translation_frame_lib.TranslationFrame({
        'email': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Keyword'), (2, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
        'fast': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
        'efficient': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(2, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
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
        'keyword_insertion_keys': [{}, {}, {}],
    })

    self.mock_send_api_request.side_effect = [
        {
            'translations': [
                {'translatedText': 'correo electrónico'},
                {'translatedText': 'rápido'},
            ]
        },
        requests.exceptions.HTTPError(),
    ]

    with mock.patch.object(
        vertex_client,
        'AVAILABLE_LANGUAGES',
        new=frozenset(['available_language']),
    ):
      try:
        self.cloud_translation_client.translate(
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
    self.assertEqual(
        self.cloud_translation_client.get_translated_characters(), 9
    )

  def test_translate_shortens_translations(self):
    source_language = 'en'
    target_language = 'available_language'

    mock_vertex_client = mock.create_autospec(vertex_client.VertexClient)
    mock_vertex_client.shorten_text_to_char_limit.side_effect = [
        ['shortened1'],
        ['shortened2'],
    ]

    translation_frame = translation_frame_lib.TranslationFrame({
        'term_to_overflow_1': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Headline 1'), (2, 'Keyword')],
            char_limit=10,
            keyword_insertion_keys={},
        ),
        'term_that_fits_1': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
        'term_to_overflow_2': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(3, 'Headline 1')],
            char_limit=15,
            keyword_insertion_keys={},
        ),
        'term_that_fits_2': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(4, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
        'term_to_overflow_{0:3}': (
            translation_metadata.TranslationMetadata(
                dataframe_rows_and_cols=[(5, 'Headline 1')],
                char_limit=15,
                keyword_insertion_keys={'0': 'keyword'},
            )
        ),
    })

    expected_translated_df = pd.DataFrame({
        'source_term': [
            'term_to_overflow_1',
            'term_that_fits_1',
            'term_to_overflow_2',
            'term_that_fits_2',
            'term_to_overflow_{0:3}',
        ],
        'target_terms': [
            {'available_language': 'shortened1'},
            {'available_language': 'untruncated_translation_1'},
            {'available_language': 'shortened2'},
            {'available_language': 'untruncated_translation_2'},
            {'available_language': 'untruncated_translation_{0:3}'},
        ],
        'dataframe_locations': [
            [(0, 'Headline 1'), (2, 'Keyword')],
            [(1, 'Keyword')],
            [(3, 'Headline 1')],
            [(4, 'Keyword')],
            [(5, 'Headline 1')],
        ],
        'char_limit': [10, 90, 15, 90, 15],
        'keyword_insertion_keys': [{}, {}, {}, {}, {'0': 'keyword'}],
    })

    self.mock_send_api_request.side_effect = [
        {'translations': [
            {'translatedText': 'some long overflowing translation 1'},
            {'translatedText': 'untruncated_translation_1'},
            {'translatedText': 'some long overflowing translation 2'},
            {'translatedText': 'untruncated_translation_2'},
            {'translatedText': 'untruncated_translation_{0:3}'}]},]

    with mock.patch.object(
        vertex_client,
        'AVAILABLE_LANGUAGES',
        new=frozenset(['available_language']),
    ):
      self.cloud_translation_client._batch_char_limit = 2500
      self.cloud_translation_client._shorten_translations_to_char_limit = True
      self.cloud_translation_client._vertex_client = mock_vertex_client
      self.cloud_translation_client.translate(
          translation_frame=translation_frame,
          source_language_code=source_language,
          target_language_code=target_language,
      )

    actual_translated_df = translation_frame.df()

    # Asserts expected translations added to translation frame.
    pd.testing.assert_frame_equal(
        expected_translated_df, actual_translated_df, check_index_type=False
    )
    # Asserts the number of characters sent to the Cloud Translation API.
    self.assertEqual(
        self.cloud_translation_client.get_translated_characters(), 90
    )

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
  def test_shorten_text_to_char_limit_not_called_unsupported_language(
      self,
      mock_target_language,
      mock_shorten_translations_to_char_limit,
  ):
    source_language = 'en'
    target_language = mock_target_language
    shorten_translations_to_char_limit = mock_shorten_translations_to_char_limit

    with mock.patch.object(
        vertex_client,
        'AVAILABLE_LANGUAGES',
        new=frozenset(['available_language']),
    ):
      self.cloud_translation_client._shorten_translations_to_char_limit = (
          shorten_translations_to_char_limit
      )

    translation_frame = translation_frame_lib.TranslationFrame({
        'email': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Keyword'), (2, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
        'fast': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
        'efficient': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(2, 'Keyword')],
            char_limit=90,
            keyword_insertion_keys={},
        ),
    })


    self.cloud_translation_client.translate(
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
                      'name': 'projects/fake-project-id/locations/fake-region/glossaries/fake-glossary-1',
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
                      'name': 'projects/fake-project-id/locations/fake-region/glossaries/fake-glossary-2',
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
          'expected_result': [
              cloud_translation_client_lib.Glossary(
                  id='fake-glossary-1',
                  name='projects/fake-project-id/locations/fake-region/glossaries/fake-glossary-1',
                  display_name='fake-glossary-1',
              ),
              cloud_translation_client_lib.Glossary(
                  id='fake-glossary-2',
                  name='projects/fake-project-id/locations/fake-region/glossaries/fake-glossary-2',
                  display_name='fake-glossary-2',
              ),
          ],
      },
      {
          'testcase_name': 'glossaries_does_not_exist',
          'expected_response': {'glossaries': []},
          'expected_result': [],
      },
  )
  def test_list_glossaies(
      self,
      expected_response,
      expected_result,
  ):
    self.mock_send_api_request.return_value = expected_response
    actual_result = self.cloud_translation_client.list_glossaries()

    self.assertEqual(actual_result, expected_result)

  @parameterized.named_parameters(
      {
          'testcase_name': 'bad_file_name',
          'bad_file_name': 'maleformatted-to-de-glossary-test.csv',
      },
      {
          'testcase_name': 'wrong_extension',
          'bad_file_name': 'en-to-de-glossary-test.json',
      },
  )
  def test_get_glossary_info_from_cloud_event_data_raises_error(
      self, bad_file_name
  ):
    fake_event_data = {
        'name': bad_file_name,
    }

    with self.assertRaises(cloud_translation_client_lib.GlossaryError):
      self.cloud_translation_client.get_glossary_info_from_cloud_event_data(
          fake_event_data
      )

  def test_get_glossary_info_from_cloud_event_data(self):
    fake_event_data = {
        'name': f'{_FAKE_GLOSSARY_ID}.csv',
        'selfLink': (
            'https://www.googleapis.com/storage/v1/b/'
            f'{_FAKE_BUCKET}/o/{_FAKE_GLOSSARY_ID}.csv'
        ),
    }
    expected_result = (
        _FAKE_GLOSSARY_ID,
        'en',
        'de',
        _FAKE_GLOSSARY_URI,
    )

    actual_result = (
        self.cloud_translation_client.get_glossary_info_from_cloud_event_data(
            fake_event_data
        )
    )

    self.assertEqual(expected_result, actual_result)

  def test_create_or_replace_glossary(self):
    expected_response = {
        'name': 'projects/fake-project-id/locations/fake-region/operations/fake-operation-id',
        'metadata': {
            '@type': 'type.googleapis.com/google.cloud.translation.v3beta1.CreateGlossaryMetadata',
            'name': _FAKE_GLOSSARY_NAME,
            'state': 'SUCCEEDED',
            'submitTime': '2023-10-17T19:05:10.650047636Z',
        },
        'done': True,
    }
    expected_create_url = (
        'https://translate.googleapis.com/v3/projects/fake-gcp-project/'
        'locations/fake-gcp-region/glossaries'
    )
    expected_create_params = {
        'name': _FAKE_GLOSSARY_NAME,
        'language_pair': {
            'source_language_code': 'en',
            'target_language_code': 'de',
        },
        'input_config': {'gcs_source': {'input_uri': _FAKE_GLOSSARY_URI}},
    }

    expected_operation_url = (
        'https://translate.googleapis.com/v3/projects/fake-project-id/'
        'locations/fake-region/operations/fake-operation-id:wait'
    )
    expected_operation_params = {'timeout': '300s'}
    expected_delete_url = os.path.join(expected_create_url, _FAKE_GLOSSARY_ID)
    expected_header = {
        'Authorization': 'Bearer fake_access_token',
        'Content-Type': 'application/json',
    }
    self.mock_send_api_request.side_effect = [
        '',
        expected_response,
        expected_response,
    ]
    self.cloud_translation_client.create_or_replace_glossary(
        glossary_id=_FAKE_GLOSSARY_ID,
        source_language='en',
        target_language='de',
        input_uri=_FAKE_GLOSSARY_URI,
    )
    # Expecting 3 calls: First call will be to try and delete the glossary if it
    # exists. The second call is to create the glossary and the third is to wait
    # for the glossary operation to succeed.
    self.mock_send_api_request.assert_has_calls([
        # First call will be to try and delete the glossary if it exists.
        mock.call(
            expected_delete_url,
            None,  # Parameters are empty for a delete request.
            expected_header,
            'DELETE',
        ),
        mock.call(expected_create_url, expected_create_params, expected_header),
        mock.call(
            expected_operation_url,
            expected_operation_params,
            expected_header,
        ),
    ])

  def test_create_or_replace_glossary_raises_http_error(self):
    response = requests.Response()
    response.status_code = 400
    error = requests.exceptions.HTTPError(response=response)
    self.mock_send_api_request.side_effect = error
    with self.assertRaises(cloud_translation_client_lib.GlossaryError):
      self.cloud_translation_client.create_or_replace_glossary(
          glossary_id=_FAKE_GLOSSARY_ID,
          source_language='en',
          target_language='de',
          input_uri=_FAKE_GLOSSARY_URI,
      )


if __name__ == '__main__':
  absltest.main()

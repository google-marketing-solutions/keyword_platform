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

"""Defines the CloudTranslationClient class.

See class doctring for more details.
"""
from absl import logging
import pandas as pd
import requests

from common import api_utils
from common import vertex_client as vertex_client_lib
from data_models import translation_frame as translation_frame_lib

TRANSLATE_API_BASE_URL = 'https://translate.googleapis.com'

TRANSLATE_TEXT_ENDPOINT = (
    TRANSLATE_API_BASE_URL
    + '/v{api_version}/projects/{gcp_project_name}:translateText'
)

_API_VERSION = '3'

_CREDENTIAL_REQUIRED_KEYS = (
    'client_id',
    'client_secret',
    'refresh_token',
)


# Max batch size for the Cloud Translation API V3 is 5000 code points.
# Setting the batch too high could result in long response times, and some chars
# may be represented by 3 code points, so 1500 keeps response times short in the
# average case, and stops us exceeding limits in the worst case of all chars
# being represented by multiple code points.
_DEFAULT_BATCH_CHAR_LIMIT = 1500


class CloudTranslationClient:
  """A client for translating data via the Google Cloud Translation API.

  The credentials need to be provided as a dictionary see details below:

  Sample usage:
    credentials = {
      'client_id': <client_id>,
      'client_secret': <client_secret>,
      'refresh_token': <refresh_token>,
    }

    cloud_translation_client = CloudTranslationClient(credentials, 'my_project')
    cloud_translation_client.translate(
        translation_frame=<TranslationFrame>,
        source_language_code='EN',
        target_language_code='DE',
        )

    The TranslationFrame object will be mutated to add translations in-place.
  """

  def __init__(
      self,
      credentials: dict[str, str],
      gcp_project_name: str,
      api_version: str = _API_VERSION,
      batch_char_limit: int = _DEFAULT_BATCH_CHAR_LIMIT,
      vertex_client: vertex_client_lib.VertexClient | None = None,
  ) -> None:
    """Instantiates the Clound Translation client.

    Args:
      credentials: The Cloud API credentials as dict. Should contain client_id,
        client_secret, and refresh_token keys.
      gcp_project_name: The name or ID of the Google Cloud Project associated
        with the credentials.
      api_version: The Cloud Translate API API Version.
      batch_char_limit: The size of content batches to send to the translation
        API, in chars.
      vertex_client: An instance of the Vertex client for accessing LLM APIs.
    """
    self.api_version = api_version
    self.batch_char_limit = batch_char_limit
    self.credentials = credentials
    self.gcp_project_name = gcp_project_name
    # The access_token be lazily loaded and cached when the API is called to
    # ensure token is fresh and won't be retrieved repeatedly.
    self.access_token = None
    self._vertex_client = vertex_client
    api_utils.validate_credentials(self.credentials, _CREDENTIAL_REQUIRED_KEYS)
    logging.info('Successfully initialized CloudTranslationClient.')

  def translate(
      self,
      translation_frame: translation_frame_lib.TranslationFrame,
      source_language_code: str,
      target_language_code: str) -> None:
    """Translates the terms in a translation frame in place.

    The translations will be added to the 'target_terms' column of the
    translation_frame.

    Args:
      translation_frame: The terms to translate.
      source_language_code: The language to translate from.
      target_language_code: The language to translate to.
    """
    logging.info('Starting translation for %d terms.', translation_frame.size())

    batch_start = 0
    parent = f'projects/{self.gcp_project_name}'

    while batch_start < translation_frame.size():

      batch, next_batch_index = translation_frame.get_term_batch(
          batch_start, self.batch_char_limit)

      params = {
          'contents': batch,
          'mimeType': 'text/plain',
          'parent': parent,
          'source_language_code': source_language_code,
          'target_language_code': target_language_code,
      }

      url = TRANSLATE_TEXT_ENDPOINT.format(
          api_version=self.api_version, gcp_project_name=self.gcp_project_name)

      try:
        response = api_utils.send_api_request(
            url, params, self._get_http_header())
      except requests.exceptions.HTTPError as http_error:
        # If the translation API requests still fail after retries, it's likely
        # we may have hit project quota. In this case, exit early so we can
        # just write the data we did get instead of losing everything.
        logging.exception(
            'Encountered error during calls to Translation API: %s', http_error)
        return

      logging.info('Got responses for terms %d-%d of %d',
                   batch_start,
                   batch_start + len(batch) - 1, translation_frame.size())

      translations = [t['translatedText'] for t in response['translations']]

      translation_frame.add_translations(
          start_index=batch_start,
          target_language_code=target_language_code,
          translations=translations,
      )

      batch_start = next_batch_index

    logging.info(
        'Completed translation for %d terms.', translation_frame.size())

    self._shorten_overflowing_translations(
        translation_frame, target_language_code)

  def _get_http_header(self) -> dict[str, str]:
    """Get the Authorization HTTP header.

    Returns:
      The authorization HTTP header.
    """
    if not self.access_token:
      self.access_token = api_utils.refresh_access_token(self.credentials)
    return {
        'Authorization': f'Bearer {self.access_token}',
        'Content-Type': 'application/json',
    }

  def _shorten_overflowing_translations(
      self,
      translation_frame: translation_frame_lib.TranslationFrame,
      target_language_code: str) -> None:
    """Uses VertexAI API to fix overflowing translations in-place.

    Args:
      translation_frame: The translation frame to shorten overflowing
        translations for.
      target_language_code: The language to translate to.
    """
    if not self._vertex_client:
      logging.info('Skipping VertexAI shortening: No client initialized.')
      return

    logging.info('Shortening translations with VertexAI...')

    overflowing_translations = self._get_overflowing_translations(
        translation_frame, target_language_code)

    if overflowing_translations.empty:
      logging.info('No overflowing translations found. Returning...')
      return

    logging.info(
        'Found %d overflowing translations.', len(overflowing_translations)
    )

    # Different rows may have different char limits, so we need to process
    # each group of unique char limits separately.
    unique_char_limits = overflowing_translations[
        translation_frame_lib.CHAR_LIMIT
    ].unique()

    for char_limit in unique_char_limits:
      logging.info('Shortening translations for char limit: %d.', char_limit)
      translations_with_this_char_limit = overflowing_translations[
          overflowing_translations[translation_frame_lib.CHAR_LIMIT]
          == char_limit
      ]

      # Gets the translations to shorten as a list.
      translations = translations_with_this_char_limit[
          translation_frame_lib.TARGET_TERMS
      ].tolist()

      translations = [
          translation[target_language_code] for translation in translations]

      logging.info('Translations to shorten: %s', translations)

      shortened_translations = self._vertex_client.shorten_text_to_char_limit(
          text_list=translations,
          language_code=target_language_code,
          char_limit=char_limit,
      )

      logging.info('Shortened translations: %s', shortened_translations)

      # Finally, updates the original DataFrame.
      translation_index = 0
      for row_number, _ in translations_with_this_char_limit.iterrows():
        old_translation = translation_frame.df().loc[
            row_number, translation_frame_lib.TARGET_TERMS
        ][target_language_code]
        new_translation = shortened_translations[translation_index]
        logging.info(
            'Replacing %s (%d chars) with %s (%d chars).',
            old_translation, len(old_translation),
            new_translation,
            len(new_translation),
        )
        translation_frame.df().loc[
            row_number, translation_frame_lib.TARGET_TERMS
        ][target_language_code] = new_translation
        translation_index += 1

    logging.info('Finished shortening translations with VertexAI.')

  def _get_overflowing_translations(
      self,
      translation_frame: translation_frame_lib.TranslationFrame,
      target_language_code: str,
  ) -> pd.DataFrame:
    """Gets a DataFrame containing translations that are > char_limit.

    Args:
      translation_frame: A frame containing translations that may be too long.
      target_language_code: The language to translate to.

    Returns:
      A DataFrame
    """
    # Gets the length of translations.
    translation_lengths = [
        len(target_term[target_language_code])
        for target_term in translation_frame.df()[
            translation_frame_lib.TARGET_TERMS
        ]
    ]

    # Gets translations that are > the char limit.
    return translation_frame.df()[
        translation_lengths
        > translation_frame.df()[translation_frame_lib.CHAR_LIMIT]
    ]

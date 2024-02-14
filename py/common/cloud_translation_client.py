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

"""Defines the CloudTranslationClient class.

See class doctring for more details.
"""
import dataclasses
import os
import re
from typing import Any

from absl import logging
import google.api_core
import pandas as pd
import requests

from common import api_utils
from common import vertex_client as vertex_client_lib
from data_models import translation_frame as translation_frame_lib

TRANSLATE_API_BASE_URL = 'https://translate.googleapis.com'

TRANSLATE_TEXT_ENDPOINT = (
    TRANSLATE_API_BASE_URL
    + '/v{api_version}/projects/{gcp_project_name}/locations/{gcp_region}:translateText'
)

GLOSSARIES_ENDPOINT = (
    TRANSLATE_API_BASE_URL
    + '/v{api_version}/projects/{gcp_project_name}/locations/{gcp_region}/glossaries'
)

OPERATION_ENDPOINT = (
    TRANSLATE_API_BASE_URL + '/v{api_version}/{operation_name}:{method}'
)

_GLOSSARY_PATH = 'projects/{gcp_project_name}/locations/{gcp_region}/glossaries/{glossary_id}'

_API_VERSION = '3'

_CREDENTIAL_REQUIRED_KEYS = (
    'client_id',
    'client_secret',
    'refresh_token',
)

_GLOSSARY_FILE_VALIDATION_REGEX = r'^[a-z]{2}-to-[a-z]{2}-.+\.csv$'

# Max batch size for the Cloud Translation API V3 is 5000 code points.
# Setting the batch too high could result in long response times, and some chars
# may be represented by 3 code points, so 1500 keeps response times short in the
# average case, and stops us exceeding limits in the worst case of all chars
# being represented by multiple code points.
_DEFAULT_BATCH_CHAR_LIMIT = 1500


@dataclasses.dataclass
class Glossary:
  """A class to represent a Glossary."""

  id: str = dataclasses.field(default_factory=str)
  name: str = dataclasses.field(default_factory=str)
  display_name: str = dataclasses.field(default_factory=str)


class GlossaryError(Exception):
  """An error occurred while creating or deleting Glossaries."""


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
      gcp_project_name: str,
      gcp_region: str,
      credentials: dict[str, str] | None = None,
      api_version: str = _API_VERSION,
      batch_char_limit: int = _DEFAULT_BATCH_CHAR_LIMIT,
      vertex_client: vertex_client_lib.VertexClient | None = None,
      shorten_translations_to_char_limit: bool = False,
  ) -> None:
    """Instantiates the Clound Translation client.

    Args:
      gcp_project_name: The name or ID of the Google Cloud Project associated
        with the credentials.
      gcp_region: The Google Cloud Project region.
      credentials: The Cloud API credentials as dict. Should contain client_id,
        client_secret, and refresh_token keys.
      api_version: The Cloud Translate API API Version.
      batch_char_limit: The size of content batches to send to the translation
        API, in chars.
      vertex_client: An instance of the Vertex client for accessing LLM APIs.
      shorten_translations_to_char_limit: Whether or not to shorten overflowing
        translations.
    """
    self._api_version = api_version
    self._batch_char_limit = batch_char_limit
    self._gcp_project_name = gcp_project_name
    self._gcp_region = gcp_region
    self._credentials = credentials
    # The access_token be lazily loaded and cached when the API is called to
    # ensure token is fresh and won't be retrieved repeatedly.
    self._access_token = None
    self._vertex_client = vertex_client
    self._shorten_translations_to_char_limit = (
        shorten_translations_to_char_limit
    )
    self._translated_characters = 0
    api_utils.validate_credentials(self._credentials, _CREDENTIAL_REQUIRED_KEYS)
    logging.info('Successfully initialized CloudTranslationClient.')

  def translate(
      self,
      translation_frame: translation_frame_lib.TranslationFrame,
      source_language_code: str,
      target_language_code: str,
      glossary_id: str = '',
  ) -> None:
    """Translates the terms in a translation frame in place.

    The translations will be added to the 'target_terms' column of the
    translation_frame.

    Args:
      translation_frame: The terms to translate.
      source_language_code: The language to translate from.
      target_language_code: The language to translate to.
      glossary_id: The glossary to use during tranlsation.
    """
    logging.info('Starting translation for %d terms.', translation_frame.size())

    batch_start = 0
    parent = f'projects/{self._gcp_project_name}'

    while batch_start < translation_frame.size():

      batch, next_batch_index = translation_frame.get_term_batch(
          batch_start, self._batch_char_limit
      )

      params = {
          'contents': batch,
          'mimeType': 'text/plain',
          'parent': parent,
          'source_language_code': source_language_code,
          'target_language_code': target_language_code,
      }
      response_key = 'translations'
      if glossary_id:
        logging.info('Translating with glossary: %s', glossary_id)
        glossary = (
            f'{parent}/locations/{self._gcp_region}/glossaries/{glossary_id}'
        )
        params['glossaryConfig'] = {
            'glossary': glossary,
            'ignore_case': False,
        }

        response_key = 'glossaryTranslations'

      url = TRANSLATE_TEXT_ENDPOINT.format(
          api_version=self._api_version,
          gcp_project_name=self._gcp_project_name,
          gcp_region=self._gcp_region,
      )

      try:
        response = api_utils.send_api_request(
            url, params, self._get_http_header())
        self._translated_characters += sum([len(item) for item in batch])
      except requests.exceptions.HTTPError as http_error:
        # If the translation API requests still fail after retries, it's likely
        # we may have hit project quota. In this case, exit early so we can
        # just write the data we did get instead of losing everything.
        logging.exception(
            'Encountered error during calls to Translation API: %s', http_error)
        raise

      logging.info('Got responses for terms %d-%d of %d',
                   batch_start,
                   batch_start + len(batch) - 1, translation_frame.size())

      translations = [t['translatedText'] for t in response[response_key]]

      translation_frame.add_translations(
          start_index=batch_start,
          target_language_code=target_language_code,
          translations=translations,
      )

      batch_start = next_batch_index

    logging.info(
        'Completed translation for %d terms.', translation_frame.size())

    if (
        target_language_code in vertex_client_lib.AVAILABLE_LANGUAGES
        and self._shorten_translations_to_char_limit
    ):
      self._shorten_overflowing_translations(
          translation_frame, target_language_code
      )
    else:
      logging.warning(
          'Language %s not supported for shortening or user opted out.',
          target_language_code,
      )

  def get_translated_characters(self) -> int:
    """Gets the number of characters sent to the translation API."""
    return self._translated_characters

  def _get_http_header(self) -> dict[str, str]:
    """Get the Authorization HTTP header.

    Returns:
      The authorization HTTP header.
    """
    if not self._access_token:
      self._access_token = api_utils.refresh_access_token(self._credentials)
    return {
        'Authorization': f'Bearer {self._access_token}',
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
    translation_lengths = []
    for _, row in translation_frame.df().iterrows():
      target_term = row[translation_frame_lib.TARGET_TERMS]
      keyword_insertion_keys = row[translation_frame_lib.KEYWORD_INSERTION_KEYS]
      # TODO(): Shorten text that include keyword insertion tags for
      # ads translations.
      #
      # Only append target term lengths to list when text has no keyword
      # insertion tags (which is identified when key insertion keys in the
      # dataframe are not empty) because the text shortener may remove the tags.
      # For example, "Data centers in {0:denver}" may resolve to
      # "Denver data centers".
      if not keyword_insertion_keys:
        translation_lengths.append(len(target_term[target_language_code]))
      else:
        translation_lengths.append(0)

    # Gets translations that are > the char limit.
    # TODO(): Change how translation lengths and character limits
    # logic omits text with keyword insertion tags.
    return translation_frame.df()[
        translation_lengths
        > translation_frame.df()[translation_frame_lib.CHAR_LIMIT]
    ]

  def list_glossaries(self) -> list[Glossary]:
    """Gets a list of available glossaries.

    Returns:
      A list of glossary objects.
    """
    glossaries = []
    url = GLOSSARIES_ENDPOINT.format(
        api_version=self._api_version,
        gcp_project_name=self._gcp_project_name,
        gcp_region=self._gcp_region,
    )
    try:
      response = api_utils.send_api_request(
          url, None, self._get_http_header(), method='GET'
      )
    except requests.exceptions.HTTPError as http_error:
      logging.exception(
          'Encountered error during calls to Translation API: %s', http_error
      )
      raise
    for glossary in response['glossaries']:
      id = glossary['name'].split('/')[-1]
      glossaries.append(Glossary(id=id, name=glossary['name'], display_name=id))
    return glossaries

  def get_glossary_info_from_cloud_event_data(
      self,
      cloud_event_data: dict[str, Any],
  ) -> tuple[str, str, str, str]:
    """Gets glossary info from cloud event data.

    The cloud event name has to be of the format:
      [source_language]-[target_language]-[glossary-id].csv

    Args:
      cloud_event_data: A cloud event object.

    Returns:
      A tuple with the glossary id, source, target language and URI.

    Raises:
      GlossaryError: If the glossary file provided does not have the right name.
    """
    file_name = cloud_event_data['name']
    if not re.fullmatch(_GLOSSARY_FILE_VALIDATION_REGEX, file_name):
      raise GlossaryError(
          'Glossary needs to have the format:'
          ' [source_language]-to-[target_language]-[glossary-id].csv.'
      )
    glossary_id, _ = os.path.splitext(cloud_event_data['name'])
    source_language, _, target_language = glossary_id.split('-')[:3]
    glossary_uri = (
        cloud_event_data['selfLink']
        .replace('https://www.googleapis.com/storage/v1/b/', 'gs://')
        .replace('/o/', '/')
    )
    logging.info(
        'Glossary file has id: %s, source language: %s, target language: %s.'
        ' Located under %s',
        glossary_id,
        source_language,
        target_language,
        glossary_uri,
    )
    return glossary_id, source_language, target_language, glossary_uri

  def create_or_replace_glossary(
      self,
      glossary_id: str,
      source_language: str,
      target_language: str,
      input_uri: str,
      timeout_sec: int = 300,
  ) -> Any:
    """Creates or replaces a Glossary.

    A Glossary is created from a CSV file stored in a GCS bucket that is used to
    make specific translations when making calls to the Cloud Translate API.

    Args:
      glossary_id: The ID of the glossary.
      source_language: The source language code.
      target_language: The target language code.
      input_uri: The URI of the glossary CSV file in Google Cloud Storage.
      timeout_sec: The timeout in seconds.

    Returns:
      The Glossary Operation response.
    """

    try:
      self._delete_glossary(glossary_id)
    except google.api_core.exceptions.NotFound:
      logging.info('Creating glossary with id %s', glossary_id)

    try:
      operation = self._create_glossary(
          glossary_id, source_language, target_language, input_uri, timeout_sec
      )
    except GlossaryError:
      logging.exception('Failed to create glossary with id %s', glossary_id)
      raise
    return operation

  def _create_glossary(
      self,
      glossary_id: str,
      source_language: str,
      target_language: str,
      input_uri: str,
      timeout_sec: int = 300,
  ) -> Any:
    """Creates a new Glossary.

    Args:
      glossary_id: The ID of the glossary.
      source_language: The source language code.
      target_language: The target language code.
      input_uri: The URI of the glossary CSV file in Google Cloud Storage.
      timeout_sec: Timeout in seconds.

    Returns:
      A create glossary long running operation response.
    """
    url = GLOSSARIES_ENDPOINT.format(
        api_version=self._api_version,
        gcp_project_name=self._gcp_project_name,
        gcp_region=self._gcp_region,
    )
    name = _GLOSSARY_PATH.format(
        gcp_project_name=self._gcp_project_name,
        gcp_region=self._gcp_region,
        glossary_id=glossary_id,
    )
    params = {
        'name': name,
        'language_pair': {
            'source_language_code': source_language,
            'target_language_code': target_language,
        },
        'input_config': {'gcs_source': {'input_uri': input_uri}},
    }

    try:
      operation = api_utils.send_api_request(
          url, params, self._get_http_header()
      )
      logging.info(
          'Started glossary operation: %s from %s',
          operation['name'],
          input_uri,
      )
      url = OPERATION_ENDPOINT.format(
          api_version=self._api_version,
          operation_name=operation['name'],
          method='wait',
      )
      params = {'timeout': f'{timeout_sec}s'}
      finished_operation = api_utils.send_api_request(
          url, params, self._get_http_header()
      )
      logging.info('Finished glossary operation: %s.', finished_operation)
    except requests.exceptions.HTTPError as http_error:
      logging.exception(
          'Encountered error during calls to Translation API: %s', http_error
      )
      raise GlossaryError(
          f'Failed to create glossary with id {glossary_id}: {http_error}'
      ) from http_error

    return finished_operation

  def _delete_glossary(self, glossary_id: str) -> None:
    """Deletes a Glossary.

    Args:
      glossary_id: The ID of the glossary.
    """
    url = os.path.join(
        GLOSSARIES_ENDPOINT.format(
            api_version=self._api_version,
            gcp_project_name=self._gcp_project_name,
            gcp_region=self._gcp_region,
        ),
        glossary_id,
    )

    try:
      api_utils.send_api_request(url, None, self._get_http_header(), 'DELETE')
      logging.info('Deleted glossary with id %s', glossary_id)
    except requests.exceptions.HTTPError as http_error:
      if http_error.response.status_code == 404:
        logging.info('Glossary with id %s not found.', glossary_id)
      else:
        logging.exception(
            'Encountered error during calls to Translation API: %s', http_error
        )
        raise GlossaryError(
            f'Failed to delete glossary with id {glossary_id}: {http_error}'
        ) from http_error

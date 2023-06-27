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

from py.common import api_utils
from py.data_models import translation_frame as translation_frame_lib

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

# TODO():
_TRANSLATE_BATCH_SIZE = 128


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
      batch_size: int = _TRANSLATE_BATCH_SIZE,
  ) -> None:
    """Instantiates the Clound Translation client.

    Args:
      credentials: The Cloud API credentials as dict. Should contain client_id,
        client_secret, and refresh_token keys.
      gcp_project_name: The name or ID of the Google Cloud Project associated
        with the credentials.
      api_version: The Cloud Translate API API Version.
      batch_size: The size of content batches to send to the translation API.
    """
    self.api_version = api_version
    self.batch_size = batch_size
    self.credentials = credentials
    self.gcp_project_name = gcp_project_name
    # The access_token be lazily loaded and cached when the API is called to
    # ensure token is fresh and won't be retrieved repeatedly.
    self.access_token = None
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
      batch_end = (batch_start + self.batch_size) - 1  # Account for 0 indexing
      batch = translation_frame.get_terms(batch_start, batch_end)

      params = {
          'contents': batch,
          'mimeType': 'text/plain',
          'parent': parent,
          'source_language_code': source_language_code,
          'target_language_code': target_language_code,
      }

      url = TRANSLATE_TEXT_ENDPOINT.format(
          api_version=self.api_version, gcp_project_name=self.gcp_project_name)

      response = api_utils.send_api_request(
          url, params, self._get_http_header())

      logging.info('Got responses for terms %d-%d of %d',
                   batch_start, batch_end, translation_frame.size())

      translations = [t['translatedText'] for t in response['translations']]

      translation_frame.add_translations(
          start_index=batch_start,
          target_language_code=target_language_code,
          translations=translations,
      )

      batch_start = batch_end + 1

    logging.info(
        'Completed translation for %d terms.', translation_frame.size())

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


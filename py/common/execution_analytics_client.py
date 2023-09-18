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

"""Reports backend usage to Google Analytics."""

import json
import math
import os
import time
from typing import Any

from absl import logging
import requests

from data_models import settings as settings_lib
from workers import worker_result as worker_result_lib

_GA4_UPLOAD_URL = 'https://www.google-analytics.com/mp/collect'
_GA4_DEBUG_URL = 'https://www.google-analytics.com/debug/mp/collect'


class ExecutionAnalyticsClient:
  """Reports worker results and run settings to Google Analytics.

  Example Usage:
    execution_analytics_client = ExecutionAnalyticsClient(
        settings, worker_result)
    execution_analytics_client.send_execution_results()
  """

  def __init__(self, settings: settings_lib.Settings) -> None:
    """Initializes the execution analytics client.

    Args:
      settings: The execution settings object.
    """
    self._settings = settings
    self._measurement_id = os.getenv('GA_MEASUREMENT_ID', '')
    self._api_secret = os.getenv('GA_API_SECRET', '')
    self._version = os.getenv('VERSION', 'unset')
    self._project_id = os.getenv('GCP_PROJECT', '')
    self._url = (
        f'{_GA4_UPLOAD_URL}?measurement_id={self._measurement_id}&'
        f'api_secret={self._api_secret}'
    )
    self._debug_url = (
        f'{_GA4_DEBUG_URL}?measurement_id={self._measurement_id}&'
        f'api_secret={self._api_secret}'
    )

  def send_worker_result(
      self, worker_id: str, worker_result: worker_result_lib.WorkerResult
  ) -> Any:
    """Send a GA4 measurement protocol hit.

    The hit contains information about the execution settings and its result.

    Args:
      worker_id: The worker to send results for.
      worker_result: A WorkerResult object.

    Returns:
      The response from Measurement Protocol endpoint. Returns a 200 HTTP status
      code, if the hit was accepted and logs validation errors otherwise.
    """
    now_ms = math.floor(time.time() * 1000)
    qs = {
        'client_id': self._settings.client_id,
        'timestamp_micros': now_ms,
        'non_personalized_ads': 'false',
        'events': [{
            'name': 'execution',
            'params': {
                'campaign_ids': ','.join(self._settings.campaigns),
                'customer_ids': ','.join(self._settings.customer_ids),
                'keywords_modified': worker_result.keywords_modified,
                'ads_modified': worker_result.ads_modified,
                'worker': worker_id,
                'version': self._version,
                'cloud_project_id': self._project_id,
                'translation_characters': worker_result.translation_chars_sent,
                'genai_characters': worker_result.genai_chars_sent,
                'engagement_time_msec': now_ms,
                'session_id': now_ms,
                'duration_msec': worker_result.duration_ms,
                'source_language': self._settings.source_language_code,
                'target_language': self._settings.target_language_codes[0],
                'backend_errors': 1 if worker_result.error_msg else 0,
            },
        }],
    }
    if self._is_valid_hit(qs):
      return requests.post(self._url, json=qs)

  def _is_valid_hit(self, qs: dict[str, Any]) -> bool:
    """Returns True if the hit is valid.

    Args:
      qs: The query string to be sent to the Measurement Protocol endpoint.
    """
    is_valid_hit = True
    debug_response = requests.post(self._debug_url, json=qs)
    validation_messages = json.loads(debug_response.text)['validationMessages']
    if validation_messages:
      logging.debug('GA4 hit not valid: %s', validation_messages)
      is_valid_hit = False
    return is_valid_hit

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

"""Tests for analytics_client."""
import json
import os
import time
from unittest import mock
import requests_mock
from absl.testing import absltest
from common import execution_analytics_client as execution_analytics_client_lib
from common import gcloud_client as gcloud_client_lib
from data_models import settings as settings_lib
from workers import worker_result as worker_result_lib


_FAKE_WORKER_RESULT = worker_result_lib.WorkerResult(
    status=worker_result_lib.Status.SUCCESS,
    keywords_modified=1,
    ads_modified=1,
    translation_chars_sent=10,
    genai_chars_sent=10,
    duration_ms=4300,
)

_FAKE_SETTINGS = settings_lib.Settings(
    source_language_code='en',
    target_language_codes=['de'],
    customer_ids=['fake_customer_id'],
    campaigns=['fake_campaign_id'],
    credentials={'fake_credentials': 'fake_credentials'},
    workers_to_run=['fake_worker_id'],
    multiple_templates=False,
    client_id='fake_client_id',
    translate_ads=False,
    translate_keywords=True,
    translate_extensions=False,
)


class ExecutionAnalyticsClientTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.mock_os = self.enter_context(
        mock.patch.object(os, 'getenv', autospec=True)
    )
    self.mock_os.side_effect = [
        'fake_measurement_id',
        'fake_api_secret',
        'fake_cloud_project_id',
    ]
    self.enter_context(
        mock.patch.object(time, 'time', autospec=True, return_value=1)
    )
    self.mock_gcloud_client = self.enter_context(
        mock.patch.object(gcloud_client_lib, 'GcloudClient', autospec=True)
    )
    self.mock_gcloud_client.return_value.get_run_service_ref_name.return_value = (
        'fake_version'
    )

  def test_send_execution_results(self):
    expected = {
        'client_id': 'fake_client_id',
        'timestamp_micros': 1000000,
        'non_personalized_ads': 'false',
        'events': [{
            'name': 'select_item',
            'params': {
                'keywords_modified': 1,
                'ads_modified': 1,
                'worker': 'fake_worker_id',
                'version': 'fake_version',
                'cloud_project_id': 'fake_cloud_project_id',
                'translation_characters': 10,
                'genai_characters': 10,
                'engagement_time_msec': 4300,
                'session_id': 'fake_client_id',
                'duration_msec': 4300,
                'source_language': 'en',
                'target_language': 'de',
                'backend_errors': 0,
                'items': [
                    {'item_id': 'fake_campaign_id', 'affiliation': 'campaign'},
                    {'item_id': 'fake_customer_id', 'affiliation': 'customer'},
                ],
                'translate_ads': 0,
                'translate_keywords': 1,
                'translate_extensions': 0,
            },
        }],
    }
    with requests_mock.mock() as mock_request:
      mock_request.post(
          (
              'https://www.google-analytics.com/debug/mp/collect?'
              'measurement_id=fake_measurement_id&api_secret=fake_api_secret'
          ),
          status_code=200,
          text='{"validationMessages": [ ]}',
      )
      mock_request.post(
          (
              'https://www.google-analytics.com/mp/collect?'
              'measurement_id=fake_measurement_id&api_secret=fake_api_secret'
          ),
          status_code=200,
      )

      response = execution_analytics_client_lib.ExecutionAnalyticsClient(
          settings=_FAKE_SETTINGS
      ).send_worker_result('fake_worker_id', _FAKE_WORKER_RESULT)

    self.assertEqual(response.status_code, 200)
    self.assertEqual(True, mock_request.called)
    self.assertEqual(
        (
            'https://www.google-analytics.com/mp/collect?'
            'measurement_id=fake_measurement_id&api_secret=fake_api_secret'
        ),
        mock_request.last_request.url,
    )
    self.assertEqual(
        expected,
        json.loads(mock_request.last_request.text),
    )


if __name__ == '__main__':
  absltest.main()

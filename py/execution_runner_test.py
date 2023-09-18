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

"""Tests for the ExecutionRunner class."""

import os
from unittest import mock

import google.auth
from google.cloud import secretmanager

from absl.testing import absltest
from absl.testing import parameterized
import execution_runner as execution_runner_lib
from common import cloud_translation_client
from common import execution_analytics_client
from common import google_ads_client
from common import storage_client
from common import vertex_client as vertex_client_lib
from data_models import accounts as accounts_lib
from data_models import ads
from data_models import google_ads_objects as google_ads_objects_lib
from data_models import keywords
from data_models import settings as settings_lib
from workers import translation_worker


# TODO()
_FAKE_CREDENTIALS = {
    'developer_token': 'fake_developer_token',
    'client_id': 'fake_client_id',
    'client_secret': 'fake_client_secret',
    'refresh_token': 'fake_refresh_token',
    'login_customer_id': 'fake_login_customer_id',
}

_ACCOUNTS_RESPONSES = [{
        'results': [
            {
                'customerClient': {
                    'resourceName': (
                        'customers/8056520078/customerClients/5459155099'
                    ),
                    'descriptiveName': 'Account 1',
                    'id': '5459155099',
                }
            },
            {
                'customerClient': {
                    'resourceName': (
                        'customers/8056520078/customerClients/8647404629'
                    ),
                    'descriptiveName': 'Account 2',
                    'id': '8647404629',
                }
            },
        ],
        'fieldMask': 'customerClient.id,customerClient.descriptiveName',
        'requestId': 'fake_req_id',
    }]

_EXPECTED_ACCOUNTS_LIST = list([
    accounts_lib.Account(id='5459155099', name='Account 1'),
    accounts_lib.Account(id='8647404629', name='Account 2'),
])

_CAMPAIGNS_RESPONSES = [
    [{
        'results': [
            {
                'campaign': {
                    'resourceName': 'customers/1234456789/campaigns/11123',
                    'advertisingChannelType': 'SEARCH',
                    'biddingStrategyType': 'TARGET_SPEND',
                    'name': 'Test Campaign 0',
                    'id': '11123',
                }
            }
        ],
        'fieldMask': (
            'campaign.id,campaign.name,campaign.advertisingChannelType,'
            'campaign.biddingStrategyType'
        ),
        'requestId': 'fake_req_id',
    }],
    [{
        'results': [
            {
                'campaign': {
                    'resourceName': 'customers/1234456789/campaigns/12345',
                    'advertisingChannelType': 'SEARCH',
                    'biddingStrategyType': 'TARGET_SPEND',
                    'name': 'Test Campaign 1',
                    'id': '11124',
                }
            },
            {
                'campaign': {
                    'resourceName': 'customers/1234456789/campaigns/67890',
                    'advertisingChannelType': 'SEARCH',
                    'biddingStrategyType': 'MAXIMIZE_CONVERSIONS',
                    'name': 'Test Campaign 2',
                    'id': '11125',
                }
            },
        ],
        'fieldMask': (
            'campaign.id,campaign.name,campaign.advertisingChannelType,'
            'campaign.biddingStrategyType'
        ),
        'requestId': 'fake_req_id',
    }],
]

_EXPECTED_CAMPAIGNS_LIST = list([
    {
        'id': '11123',
        'name': 'Test Campaign 0',
    },
    {
        'id': '11124',
        'name': 'Test Campaign 1',
    },
    {
        'id': '11125',
        'name': 'Test Campaign 2',
    },
])


class ExecutionRunnerTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()

    self.enter_context(
        mock.patch.dict(os.environ, {'GCP_PROJECT': 'fake_gcp_project'})
    )
    self.enter_context(
        mock.patch.dict(os.environ, {'BUCKET_NAME': 'fake_bucket_name'})
    )
    self.mock_ga_opt_out = self.enter_context(
        mock.patch.dict(os.environ, {'GA_OPT_OUT': 'false'})
    )
    self.mock_storage_client = self.enter_context(
        mock.patch.object(storage_client, 'StorageClient', autospec=True)
    )
    self.enter_context(
        mock.patch.object(
            cloud_translation_client, 'CloudTranslationClient', autospec=True
        )
    )
    self.mock_google_ads_client = self.enter_context(
        mock.patch.object(google_ads_client, 'GoogleAdsClient', autospec=True)
    )
    self.mock_execution_analytics_client = self.enter_context(
        mock.patch.object(
            execution_analytics_client,
            'ExecutionAnalyticsClient',
            autospec=True,
        )
    )
    self.mock_secret_manager = self.enter_context(
        mock.patch.object(
            secretmanager, 'SecretManagerServiceClient', autospec=True
        )
    )

    self.mock_vertex_client = self.enter_context(
        mock.patch.object(vertex_client_lib, 'VertexClient', autospec=True)
    )

  # TODO: b/299618202 - Test return types in worker results
  def test_run_workers(self):
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        customer_ids=[123, 456],
        campaigns=[789, 101],
        workers_to_run=['translationWorker'],
    )

    # The ads API should be called for each customer ID in the request.
    expected_get_campaign_calls = [
        mock.call(123, [789, 101]),
        mock.call(456, [789, 101]),
    ]
    expected_get_ads_data_calls = [mock.call(123, settings.campaigns),
                                   mock.call(456, settings.campaigns)]
    expected_get_keywords_calls = [
        mock.call(123, settings.campaigns),
        mock.call(456, settings.campaigns),
    ]

    self.mock_storage_client.return_value.export_google_ads_objects_to_gcs.return_value = {
        'csv': ['some_url', 'some_url'],
        'xlsx': ['some_url', 'some_url'],
    }

    expected_worker_results = {
        'worker_results': mock.ANY,
        'asset_urls': {
            'csv': ['some_url', 'some_url'],
            'xlsx': ['some_url', 'some_url'],
        },
    }

    # Due to the way workers are dynamically loaded, they need to be mocked
    # using mock.path.dict.
    mock_translation_worker = mock.create_autospec(
        translation_worker.TranslationWorker)

    with mock.patch.dict(execution_runner_lib._WORKERS, {
        'translationWorker': mock_translation_worker}):
      execution_runner = execution_runner_lib.ExecutionRunner(settings)
      worker_results = execution_runner.run_workers()

      self.assertEqual(worker_results, expected_worker_results)

      # Asserts settings were built
      self.assertNotEmpty(settings.credentials)

      # Asserts Google Ads client called
      self.mock_google_ads_client.return_value.get_campaigns_for_account.assert_has_calls(
          expected_get_campaign_calls, any_order=True
      )
      self.mock_google_ads_client.return_value.get_ads_data_for_campaigns.assert_has_calls(
          expected_get_ads_data_calls, any_order=True
      )
      self.mock_google_ads_client.return_value.get_keywords_data_for_campaigns.assert_has_calls(
          expected_get_keywords_calls, any_order=True
      )

      # Asserts translation worker called
      mock_translation_worker.return_value.execute.assert_called_once()

      # Asserts storage client called
      self.mock_storage_client.return_value.export_google_ads_objects_to_gcs.assert_called_once()

  def test_run_no_workers_set_returns_early(self):
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        customer_ids=[123, 456],
        campaigns=[789, 101],
        workers_to_run=[],
    )

    # Due to the way workers are dynamically loaded, they need to be mocked
    # using mock.path.dict.
    mock_translation_worker = mock.create_autospec(
        translation_worker.TranslationWorker)

    with mock.patch.dict(execution_runner_lib._WORKERS, {
        'translationWorker': mock_translation_worker}):
      execution_runner = execution_runner_lib.ExecutionRunner(settings)
      execution_runner.run_workers()

      # Asserts translation worker called
      mock_translation_worker.return_value.execute.assert_not_called()

  def test_get_accounts(self):
    self.mock_google_ads_client.return_value.get_accounts.return_value = (
        _ACCOUNTS_RESPONSES
    )

    settings = settings_lib.Settings(credentials=_FAKE_CREDENTIALS)

    execution_runner = execution_runner_lib.ExecutionRunner(settings)
    accounts_list = execution_runner.get_accounts()

    self.assertListEqual(_EXPECTED_ACCOUNTS_LIST, accounts_list)
    self.mock_google_ads_client.return_value.get_accounts.assert_called_once()

  def test_get_campaigns_for_selected_accounts_has_expected_calls(self):
    self.mock_google_ads_client.return_value.get_campaigns_for_account.side_effect = (
        _CAMPAIGNS_RESPONSES[0],
        _CAMPAIGNS_RESPONSES[1],
    )

    settings = settings_lib.Settings(credentials=_FAKE_CREDENTIALS)

    execution_runner = execution_runner_lib.ExecutionRunner(settings)
    campaigns_list = execution_runner.get_campaigns_for_selected_accounts(
        ['123', '456']
    )

    self.assertListEqual(_EXPECTED_CAMPAIGNS_LIST, campaigns_list)
    # Expecting 2 calls.
    self.mock_google_ads_client.return_value.get_campaigns_for_account.assert_has_calls(
        (mock.call(customer_id='123'), mock.call(customer_id='456')),
    )

  def test_vertex_client_init(self):
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        customer_ids=[123, 456],
        campaigns=[789, 101],
        workers_to_run=['translationWorker'],
    )

    # Due to the way workers are dynamically loaded, they need to be mocked
    # using mock.path.dict.
    mock_translation_worker = mock.create_autospec(
        translation_worker.TranslationWorker
    )

    with mock.patch.dict(
        execution_runner_lib._WORKERS,
        {'translationWorker': mock_translation_worker},
    ):
      execution_runner_lib.ExecutionRunner(settings)

    self.mock_vertex_client.assert_called_once_with()

  def test_vertex_client_does_not_initialize(self):
    self.mock_vertex_client.side_effect = (
        google.api_core.exceptions.PermissionDenied(message='Permission denied')
    )
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        customer_ids=[123, 456],
        campaigns=[789, 101],
        workers_to_run=['translationWorker'],
    )

    # Due to the way workers are dynamically loaded, they need to be mocked
    # using mock.path.dict.
    mock_translation_worker = mock.create_autospec(
        translation_worker.TranslationWorker
    )

    with mock.patch.dict(
        execution_runner_lib._WORKERS,
        {'translationWorker': mock_translation_worker},
    ):
      execution_runner = execution_runner_lib.ExecutionRunner(settings)

    self.assertIsNone(execution_runner._vertex_client)

  @mock.patch.object(
      execution_runner_lib.ExecutionRunner,
      '_build_google_ads_objects',
      autospec=True)
  def test_get_cost_estimate(self, mock_build_google_ads_objects):
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        customer_ids=[123, 456],
        campaigns=[789, 101],
        workers_to_run=[''],
    )

    mock_ads = mock.create_autospec(ads.Ads)
    mock_keywords = mock.create_autospec(keywords.Keywords)

    mock_ads.char_count.return_value = 12000
    mock_keywords.char_count.return_value = 3000

    mock_build_google_ads_objects.return_value = (
        google_ads_objects_lib.GoogleAdsObjects(
            ads=mock_ads,
            keywords=mock_keywords,
        )
    )

    expected_cost_estimate_msg = (
        'Estimated cost: $0.30 USD. '
        '(12000 ad chars + 3000 keyword chars) * $0.000020/char.)')

    execution_runner = execution_runner_lib.ExecutionRunner(settings)
    actual_cost_estimate_msg = execution_runner.get_cost_estimate()

    self.assertEqual(expected_cost_estimate_msg, actual_cost_estimate_msg)

  def test_execution_analytics_init(self):
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        customer_ids=[123, 456],
        campaigns=[789, 101],
        workers_to_run=['translationWorker'],
    )

    # Due to the way workers are dynamically loaded, they need to be mocked
    # using mock.path.dict.
    mock_translation_worker = mock.create_autospec(
        translation_worker.TranslationWorker
    )

    with mock.patch.dict(
        execution_runner_lib._WORKERS,
        {'translationWorker': mock_translation_worker},
    ):
      execution_runner_lib.ExecutionRunner(settings)

    self.mock_execution_analytics_client.assert_called_once_with(
        settings=settings
    )

  def test_execution_analytics_not_initialized(self):
    self.mock_ga_opt_out = self.enter_context(
        mock.patch.dict(os.environ, {'GA_OPT_OUT': 'true'})
    )
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        customer_ids=[123, 456],
        campaigns=[789, 101],
        workers_to_run=['translationWorker'],
    )

    # Due to the way workers are dynamically loaded, they need to be mocked
    # using mock.path.dict.
    mock_translation_worker = mock.create_autospec(
        translation_worker.TranslationWorker
    )

    with mock.patch.dict(
        execution_runner_lib._WORKERS,
        {'translationWorker': mock_translation_worker},
    ):
      execution_runner_lib.ExecutionRunner(settings)

    self.mock_execution_analytics_client.assert_not_called()


if __name__ == '__main__':
  absltest.main()

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

from google.cloud import secretmanager

from absl.testing import absltest
from py import execution_runner as execution_runner_lib
from py.common import cloud_translation_client
from py.common import google_ads_client
from py.common import storage_client
from py.data_models import accounts as accounts_lib
from py.data_models import settings as settings_lib
from py.workers import translation_worker

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


class ExecutionRunnerTest(absltest.TestCase):

  def setUp(self):
    super().setUp()

    self.enter_context(
        mock.patch.dict(os.environ, {'GCP_PROJECT': 'fake_gcp_project'})
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
    self.enter_context(
        mock.patch.object(
            secretmanager, 'SecretManagerServiceClient', autospec=True
        )
    )

  def test_run_workers(self):
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        customer_ids=[123, 456],
        campaigns=[789, 101],
        workers_to_run=['translationWorker'],
    )

    # The ads API should be called for each customer ID in the request.
    expected_get_campaign_calls = [mock.call(123), mock.call(456)]
    expected_get_ads_data_calls = [mock.call(123, settings.campaigns),
                                   mock.call(456, settings.campaigns)]
    expected_get_keywords_calls = [mock.call(123), mock.call(456)]

    # Due to the way workers are dynamically loaded, they need to be mocked
    # using mock.path.dict.
    mock_translation_worker = mock.create_autospec(
        translation_worker.TranslationWorker)

    with mock.patch.dict(execution_runner_lib._WORKERS, {
        'translationWorker': mock_translation_worker}):
      execution_runner = execution_runner_lib.ExecutionRunner(settings)
      execution_runner.run_workers()

      # Asserts settings were built
      self.assertNotEmpty(settings.credentials)

      # Asserts Google Ads client called
      self.mock_google_ads_client.return_value.get_campaigns_for_account.assert_has_calls(
          expected_get_campaign_calls, any_order=True
      )
      self.mock_google_ads_client.return_value.get_ads_data_for_campaigns.assert_has_calls(
          expected_get_ads_data_calls, any_order=True
      )
      self.mock_google_ads_client.return_value.get_active_keywords_for_account.assert_has_calls(
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


if __name__ == '__main__':
  absltest.main()

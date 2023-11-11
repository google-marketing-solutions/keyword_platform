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
    accounts_lib.Account(
        id='5459155099', name='Account 1', display_name='[5459155099] Account 1'
    ),
    accounts_lib.Account(
        id='8647404629', name='Account 2', display_name='[8647404629] Account 2'
    ),
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
        'display_name': '[11123] Test Campaign 0',
    },
    {
        'id': '11124',
        'name': 'Test Campaign 1',
        'display_name': '[11124] Test Campaign 1',
    },
    {
        'id': '11125',
        'name': 'Test Campaign 2',
        'display_name': '[11125] Test Campaign 2',
    },
])

_EXTENSIONS_RESPONSE = [
    [{
        'results': [
            {
                'campaign': {
                    'resourceName': 'customers/123/campaigns/789',
                    'name': 'Campaign 1',
                },
                'adGroup': {
                    'resourceName': 'customers/123/adGroups/139665100522',
                    'name': 'Ad group 1',
                },
                'asset': {
                    'resourceName': 'customers/123/assets/110379943909',
                    'type': 'STRUCTURED_SNIPPET',
                    'structuredSnippetAsset': {
                        'header': 'Brands',
                        'values': ['Google', 'Pixel', 'Android'],
                    },
                },
                'adGroupAsset': {
                    'resourceName': (
                        'customers/123/adGroupAssets/139665100522'
                        '~110379943909~STRUCTURED_SNIPPET'
                    ),
                    'status': 'ENABLED',
                },
            },
            {
                'campaign': {
                    'resourceName': 'customers/123/campaigns/789',
                    'name': 'Campaign 1',
                },
                'adGroup': {
                    'resourceName': 'customers/123/adGroups/139665100522',
                    'name': 'Ad group 1',
                },
                'asset': {
                    'resourceName': 'customers/123/assets/110373249611',
                    'type': 'SITELINK',
                    'finalUrls': ['https://www.google.com/gmail'],
                    'sitelinkAsset': {
                        'linkText': 'This is a link text',
                        'description1': 'This is a Description 1',
                        'description2': 'This is a Description 2',
                    },
                },
                'adGroupAsset': {
                    'resourceName': (
                        'customers/123/adGroupAssets/139665100522'
                        '~110373249611~SITELINK'
                    ),
                    'status': 'ENABLED',
                },
            },
            {
                'campaign': {
                    'resourceName': 'customers/123/campaigns/789',
                    'name': 'Campaign 1',
                },
                'adGroup': {
                    'resourceName': 'customers/123/adGroups/139665100522',
                    'name': 'Ad group 1',
                },
                'asset': {
                    'resourceName': 'customers/123/assets/110380162771',
                    'type': 'CALLOUT',
                    'calloutAsset': {'calloutText': 'Buy my product now'},
                },
                'adGroupAsset': {
                    'resourceName': (
                        'customers/123/adGroupAssets/139665100522'
                        '~110380162771~CALLOUT'
                    ),
                    'status': 'ENABLED',
                },
            },
        ],
        'fieldMask': (
            'campaign.name,adGroup.campaign,'
            'asset.type,asset.structuredSnippetAsset.header,'
            'asset.structuredSnippetAsset.values,'
            'asset.calloutAsset.calloutText,asset.sitelinkAsset.description1,'
            'asset.sitelinkAsset.description2,asset.sitelinkAsset.linkText,'
            'adGroupAsset.status,adGroup.name'
        ),
        'requestId': 'fake_request_id',
    }],
    [{
        'results': [
            {
                'campaign': {
                    'resourceName': 'customers/123/campaigns/789',
                    'name': 'Campaign 1',
                },
                'asset': {
                    'resourceName': 'customers/123/assets/110379943909',
                    'type': 'STRUCTURED_SNIPPET',
                    'structuredSnippetAsset': {
                        'header': 'Brands',
                        'values': ['Google', 'Pixel', 'Android'],
                    },
                },
                'campaignAsset': {
                    'resourceName': (
                        'customers/123/campaignAssets/987'
                        '~110379943909~STRUCTURED_SNIPPET'
                    ),
                    'status': 'ENABLED',
                },
            },
            {
                'campaign': {
                    'resourceName': 'customers/123/campaigns/789',
                    'name': 'Campaign 1',
                },
                'asset': {
                    'resourceName': 'customers/123/assets/110373249611',
                    'type': 'SITELINK',
                    'finalUrls': ['https://www.google.com/gmail'],
                    'sitelinkAsset': {
                        'linkText': 'This is a link text',
                        'description1': 'This is a Description 1',
                        'description2': 'This is a Description 2',
                    },
                },
                'campaignAsset': {
                    'resourceName': (
                        'customers/123/campaignAssets/987~110373249611~SITELINK'
                    ),
                    'status': 'ENABLED',
                },
            },
            {
                'campaign': {
                    'resourceName': 'customers/123/campaigns/789',
                    'name': 'Campaign 1',
                },
                'asset': {
                    'resourceName': 'customers/123/assets/110373390950',
                    'type': 'SITELINK',
                    'finalUrls': ['https://www.google.com/gmail'],
                    'sitelinkAsset': {
                        'linkText': 'Calendar',
                        'description1': 'Open Calendar',
                        'description2': 'Calendar open',
                    },
                },
                'campaignAsset': {
                    'resourceName': (
                        'customers/123/campaignAssets/987~110373390950~SITELINK'
                    ),
                    'status': 'ENABLED',
                },
            },
            {
                'campaign': {
                    'resourceName': 'customers/123/campaigns/789',
                    'name': 'Campaign 1',
                },
                'asset': {
                    'resourceName': 'customers/123/assets/110380162771',
                    'type': 'CALLOUT',
                    'calloutAsset': {'calloutText': 'Buy my product now'},
                },
                'campaignAsset': {
                    'resourceName': (
                        'customers/123/campaignAssets/987~110380162771~CALLOUT'
                    ),
                    'status': 'ENABLED',
                },
            },
        ],
        'fieldMask': (
            'campaign.name,campaign.resourceName,asset.type,'
            'asset.structuredSnippetAsset.header,'
            'asset.structuredSnippetAsset.values,'
            'asset.calloutAsset.calloutText,asset.sitelinkAsset.description1,'
            'asset.sitelinkAsset.description2,asset.sitelinkAsset.linkText,'
            'campaignAsset.status'
        ),
        'requestId': 'fake_request_id',
    }],
]

_ADS_RESPONSE = [{
    'results': [{
        'customer': {'resourceName': 'customers/123', 'id': '123'},
        'campaign': {
            'resourceName': 'customers/123/campaigns/456',
            'name': 'Gmail Test Campaign',
        },
        'adGroup': {
            'resourceName': 'customers/123/adGroups/789',
            'name': 'Ad group 1',
        },
        'adGroupAd': {
            'resourceName': 'customers/123/adGroupAds/789~1011',
            'ad': {
                'responsiveSearchAd': {
                    'headlines': [{
                        'text': 'Email Login',
                        'assetPerformanceLabels': 'PENDING',
                        'policySummaryInfo': {
                            'reviewStatus': 'REVIEWED',
                            'approvalStatus': 'APPROVED',
                        },
                    }],
                    'descriptions': [{
                        'text': 'Amazing email!',
                        'assetPerformanceLabels': 'PENDING',
                        'policySummaryInfo': {
                            'reviewStatus': 'REVIEWED',
                            'approvalStatus': 'APPROVED',
                        },
                    }],
                },
                'resourceName': 'customers/123/ads/1011',
                'finalUrls': ['https://mail.google.com/'],
            },
        },
    }],
    'fieldMask': (
        'customer.id,campaign.name,adGroup.name,'
        'adGroupAd.ad.responsiveSearchAd.headlines,'
        'adGroupAd.ad.responsiveSearchAd.descriptions,'
        'adGroupAd.ad.finalUrls'
    ),
    'requestId': 'fake_request_id',
}]

_KEYWORDS_RESPONSE = ([{'results':
      [{'customer':
        {'resourceName': 'customers/123',
         'id': '123'},
        'campaign':
        {'resourceName': 'customers/123/campaigns/456',
         'advertisingChannelType': 'SEARCH',
         'biddingStrategyType': 'TARGET_SPEND',
         'name': 'Gmail Test Campaign'},
        'adGroup':
        {'resourceName': 'customers/123/adGroups/789',
         'name': 'Ad group 1'},
        'adGroupCriterion':
        {'resourceName': 'customers/123/adGroupCriteria/789~1112',
         'keyword':
         {'matchType': 'BROAD', 'text': 'e mail'}
        },
        'keywordView':
        {'resourceName': 'customers/123/keywordViews/789~1112'}
       },
       {'customer':
        {'resourceName': 'customers/123',
         'id': '123'},
        'campaign':
        {'resourceName': 'customers/123/campaigns/456',
         'advertisingChannelType': 'SEARCH',
         'biddingStrategyType': 'TARGET_SPEND',
         'name': 'Gmail Test Campaign'},
        'adGroup':
        {'resourceName': 'customers/123/adGroups/789',
         'name': 'Ad group 1'},
        'adGroupCriterion':
        {'resourceName': 'customers/123/adGroupCriteria/789~1314',
         'keyword':
         {'matchType': 'BROAD', 'text': 'email'}
        },
        'keywordView':
        {'resourceName': 'customers/123/keywordViews/789~1314'}
        }
       ],
      'fieldMask': ('customer.id,campaign.name,campaign.advertisingChannelType,'
                    'campaign.biddingStrategyType,adGroup.name,'
                    'adGroupCriterion.keyword.text,'
                    'adGroupCriterion.keyword.matchType'),
      'requestId': 'fake_req_id'}])


class ExecutionRunnerTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()

    self.enter_context(
        mock.patch.dict(os.environ, {'GCP_PROJECT': 'fake_gcp_project'})
    )
    self.enter_context(
        mock.patch.dict(os.environ, {'GCP_REGION': 'fake_gcp_region'})
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
    self.cloud_translation_client_mock = self.enter_context(
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
        translate_ads=True,
        translate_extensions=True,
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
    expected_get_extensions_calls = [
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
      self.mock_google_ads_client.return_value.get_extensions_for_campaigns.assert_has_calls(
          expected_get_extensions_calls, any_order=True
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

  @parameterized.named_parameters(
      {
          'testcase_name': 'permission_denied',
          'error': google.api_core.exceptions.PermissionDenied(
              message='Permission denied'
          ),
      },
      {
          'testcase_name': 'internal_server_error',
          'error': google.api_core.exceptions.InternalServerError(
              message='Internal server error'
          ),
      },
  )
  def test_vertex_client_does_not_initialize(self, error):
    self.mock_vertex_client.side_effect = error
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
        translate_ads=True,
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
        translate_ads=True,
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
        translate_ads=True,
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

  @parameterized.named_parameters(
      {
          'testcase_name': 'translate_ads_false',
          'mock_translate_ads': False,
          'mock_translate_keywords': True,
          'expected_cost_estimate_msg': (
              'Estimated cost: $0.00 USD. '
              '(0 ad chars + 20 keyword chars) * $0.000020/char.)'
          ),
      },
      {
          'testcase_name': 'translate_keywords_false',
          'mock_translate_ads': True,
          'mock_translate_keywords': False,
          'expected_cost_estimate_msg': (
              'Estimated cost: $0.00 USD. '
              '(46 ad chars + 0 keyword chars) * $0.000020/char.)'
          ),
      },
      {
          'testcase_name': 'translate_ads_and_keywords_false',
          'mock_translate_ads': False,
          'mock_translate_keywords': False,
          'expected_cost_estimate_msg': (
              'Estimated cost: $0.00 USD. '
              '(0 ad chars + 0 keyword chars) * $0.000020/char.)'
          ),
      },
  )
  def test_translate_ads_setting_equals_false_does_not_fetch_ads_data(
      self,
      mock_translate_ads,
      mock_translate_keywords,
      expected_cost_estimate_msg,
  ):
    """Tests GoogleAdsObjects.Ads is not populated when translate_ads is False.

    This is tricky to test as still make the API call to populate AdGroups, and
    the Ads field is protected. So I make sure some data is returned from the
    API mock call, but that the Ads object has 0 characters in a get_cost()
    call.
    """
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        customer_ids=[123, 456],
        campaigns=[789, 101],
        workers_to_run=['translationWorker'],
        translate_ads=mock_translate_ads,
        translate_keywords=mock_translate_keywords,
    )

    self.mock_google_ads_client.return_value.get_keywords_data_for_campaigns.return_value = (
        _KEYWORDS_RESPONSE
    )

    self.mock_google_ads_client.return_value.get_ads_data_for_campaigns.return_value = (
        _ADS_RESPONSE
    )

    execution_runner = execution_runner_lib.ExecutionRunner(settings)
    actual_cost_estimate_msg = execution_runner.get_cost_estimate()

    self.assertEqual(expected_cost_estimate_msg, actual_cost_estimate_msg)

  def test_translate_extensions_setting_equals_false_does_not_fetch_extensions_data(
      self,
  ):
    """Tests Extensions object is not populated when translate_extensions is False."""
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        customer_ids=[123, 456],
        campaigns=[789, 101],
        workers_to_run=['translationWorker'],
        translate_extensions=False,
    )

    self.mock_google_ads_client.return_value.get_extensions_for_campaigns.return_value = (
        _EXTENSIONS_RESPONSE
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
      execution_runner.run_workers()

    self.mock_google_ads_client.return_value.get_extensions_for_campaigns.assert_not_called()

  def test_create_or_replace_glossary(self):
    settings = settings_lib.Settings()
    self.cloud_translation_client_mock.return_value.get_glossary_info_from_cloud_event_data.return_value = (
        'fake_glossary_id',
        'en',
        'de',
        'fake_path',
    )
    execution_runner_lib.ExecutionRunner(settings).create_or_replace_glossary(
        'fake_event_data'
    )
    self.cloud_translation_client_mock.return_value.get_glossary_info_from_cloud_event_data.assert_called_once_with(
        'fake_event_data'
    )
    self.cloud_translation_client_mock.return_value.create_or_replace_glossary.assert_called_once_with(
        'fake_glossary_id', 'en', 'de', 'fake_path'
    )


if __name__ == '__main__':
  absltest.main()

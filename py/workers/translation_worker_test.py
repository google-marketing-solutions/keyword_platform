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

"""Tests for the TranslationWorker class.
"""
from unittest import mock

import pandas as pd

from common import api_utils
from common import cloud_translation_client as cloud_translation_client_lib
from data_models import ads as ads_lib
from data_models import google_ads_objects as google_ads_objects_lib
from data_models import keywords as keywords_lib
from data_models import settings as settings_lib
from workers import translation_worker as translation_worker_lib
from workers import worker_result
from absl.testing import absltest

_KEYWORDS_GOOGLE_ADS_API_RESPONSE = ([
    [{'results':
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
         {'matchType': 'BROAD', 'text': 'fast'}
        },
        'keywordView':
        {'resourceName': 'customers/123/keywordViews/789~1314'}
        }
       ],
      'fieldMask': ('customer.id,campaign.name,campaign.advertisingChannelType,'
                    'campaign.biddingStrategyType,adGroup.name,'
                    'adGroupCriterion.keyword.text,'
                    'adGroupCriterion.keyword.matchType'),
      'requestId': 'fake_req_id'}]])

_ADS_DATA_GOOGLE_ADS_API_RESPONSE = [
    [{'results': [
        {'customer':
         {'resourceName': 'customers/123',
          'id': '123'},
         'campaign':
         {'resourceName': 'customers/123/campaigns/456',
          'name': 'Gmail Test Campaign'},
         'adGroup':
         {'resourceName': 'customers/123/adGroups/789',
          'name': 'Ad group 1'},
         'adGroupAd':
         {'resourceName': 'customers/123/adGroupAds/789~1011',
          'ad':
          {'responsiveSearchAd':
           {'headlines':
            [{'text': 'Email Login',
              'assetPerformanceLabel': 'PENDING',
              'policySummaryInfo':
              {'reviewStatus': 'REVIEWED',
               'approvalStatus': 'APPROVED'}},
             {'text': 'Online Email',
              'assetPerformanceLabel': 'PENDING',
              'policySummaryInfo':
              {'reviewStatus': 'REVIEWED',
               'approvalStatus': 'APPROVED'}},
             {'text': 'Sign in',
              'assetPerformanceLabel': 'PENDING',
              'policySummaryInfo':
              {'reviewStatus': 'REVIEWED',
               'approvalStatus': 'APPROVED'}}],
            'descriptions':
            [{'text': 'Email thats intuitive, efficient, and useful',
              'assetPerformanceLabel': 'PENDING',
              'policySummaryInfo':
              {'reviewStatus': 'REVIEWED',
               'approvalStatus': 'APPROVED'}},
             {'text': '15 GB of storage, less spam, and mobile access',
              'assetPerformanceLabel': 'PENDING',
              'policySummaryInfo':
              {'reviewStatus': 'REVIEWED',
               'approvalStatus': 'APPROVED'}}]},
           'resourceName': 'customers/123/ads/1011',
           'finalUrls': ['https://mail.google.com/']}}},
        {'customer':
         {'resourceName': 'customers/123',
          'id': '123'},
         'campaign':
         {'resourceName': 'customers/123/campaigns/1213',
          'name': 'Analytics Test Campaign'},
         'adGroup':
         {'resourceName': 'customers/123/adGroups/1415',
          'name': 'Ad group 1'},
         'adGroupAd':
         {'resourceName':
          'customers/123/adGroupAds/1415~1617',
          'ad':
          {'responsiveSearchAd':
           {'headlines':
            [{'text': 'Official Website',
              'assetPerformanceLabel': 'PENDING',
              'policySummaryInfo':
              {'reviewStatus': 'REVIEWED',
               'approvalStatus': 'APPROVED'}},
             {'text': 'Official Site',
              'assetPerformanceLabel': 'PENDING',
              'policySummaryInfo':
              {'reviewStatus': 'REVIEWED',
               'approvalStatus': 'APPROVED'}},
             {'text': 'High Quality Products',
              'assetPerformanceLabel': 'PENDING',
              'policySummaryInfo':
              {'reviewStatus': 'REVIEWED',
               'approvalStatus': 'APPROVED'}}],
            'descriptions':
            [{'text': 'Google Analytics',
              'assetPerformanceLabel': 'PENDING',
              'policySummaryInfo':
              {'reviewStatus': 'REVIEWED',
               'approvalStatus': 'APPROVED'}},
             {'text': 'Try Analytics today!',
              'assetPerformanceLabel': 'PENDING',
              'policySummaryInfo':
              {'reviewStatus': 'REVIEWED',
               'approvalStatus': 'APPROVED'}}]},
           'resourceName': 'customers/123/ads/1617',
           'finalUrls': ['http://analytics.google.com']}}}],
      'fieldMask': ('customer.id,campaign.name,adGroup.name,'
                    'adGroupAd.ad.responsiveSearchAd.headlines,'
                    'adGroupAd.ad.responsiveSearchAd.descriptions,'
                    'adGroupAd.ad.finalUrls'),
      'requestId': 'fake_request_id'}]]

_EXPECTED_KEYWORDS_DF = pd.DataFrame(
    {'Action': ['Add', 'Add'],
     'Customer ID': ['Enter customer ID', 'Enter customer ID'],
     'Campaign': ['Gmail Test Campaign (es)', 'Gmail Test Campaign (es)'],
     'Ad group': ['Ad group 1 (es)', 'Ad group 1 (es)'],
     'Keyword': ['correo electrónico', 'rápido'],
     'Original Keyword': ['e mail', 'fast'],
     'Match Type': ['BROAD', 'BROAD'],
     'Keyword status': ['Paused', 'Paused'],
     'Updates applied': [[], []]},
)

_EXPECTED_ADS_DF = pd.DataFrame(
    {
        'Action': ['Add', 'Add'],
        'Customer ID': ['Enter customer ID', 'Enter customer ID'],
        'Ad status': ['Paused', 'Paused'],
        'Campaign': [
            'Gmail Test Campaign (es)',
            'Analytics Test Campaign (es)',
        ],
        'Ad group': ['Ad group 1 (es)', 'Ad group 1 (es)'],
        'Ad type': ['Responsive search ad', 'Responsive search ad'],
        'Headline 1': [
            'Inicio de sesión de correo electrónico',
            'Página web oficial',
        ],
        'Original Headline 1': ['Email Login', 'Official Website'],
        'Headline 2': ['Correo electrónico en línea', 'Sitio oficial'],
        'Original Headline 2': ['Online Email', 'Official Site'],
        'Headline 3': ['Iniciar sesión', 'Productos de alta calidad'],
        'Original Headline 3': ['Sign in', 'High Quality Products'],
        'Headline 4': ['', ''],
        'Original Headline 4': ['', ''],
        'Headline 5': ['', ''],
        'Original Headline 5': ['', ''],
        'Headline 6': ['', ''],
        'Original Headline 6': ['', ''],
        'Headline 7': ['', ''],
        'Original Headline 7': ['', ''],
        'Headline 8': ['', ''],
        'Original Headline 8': ['', ''],
        'Headline 9': ['', ''],
        'Original Headline 9': ['', ''],
        'Headline 10': ['', ''],
        'Original Headline 10': ['', ''],
        'Headline 11': ['', ''],
        'Original Headline 11': ['', ''],
        'Headline 12': ['', ''],
        'Original Headline 12': ['', ''],
        'Headline 13': ['', ''],
        'Original Headline 13': ['', ''],
        'Headline 14': ['', ''],
        'Original Headline 14': ['', ''],
        'Headline 15': ['', ''],
        'Original Headline 15': ['', ''],
        'Description 1': [
            'Correo electrónico intuitivo y útil',
            'Google analitico',
        ],
        'Original Description 1': [
            'Email thats intuitive, efficient, and useful',
            'Google Analytics',
        ],
        'Description 2': [
            '15 GB de almacenamiento y acceso móvil',
            '¡Pruebe Analytics hoy!',
        ],
        'Original Description 2': [
            '15 GB of storage, less spam, and mobile access',
            'Try Analytics today!',
        ],
        'Description 3': ['', ''],
        'Original Description 3': ['', ''],
        'Description 4': ['', ''],
        'Original Description 4': ['', ''],
        'Final URL': [
            'https://mail.google.com/',
            'http://analytics.google.com',
        ],
        'Label': ['Keyword Translator', 'Keyword Translator'],
        'Updates applied': [[], []],
    },
)


class TranslationWorkerTest(absltest.TestCase):

  @mock.patch.object(api_utils, 'refresh_access_token', autospec=True)
  @mock.patch.object(api_utils, 'send_api_request', autospec=True)
  def test_execute(self, mock_send_api_request, mock_refresh_access_token):
    # Arranges mock translation API
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    api_version = 3

    cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=credentials,
            gcp_project_name=gcp_project_name,
            api_version=api_version))

    mock_send_api_request.side_effect = [
        {'translations': [
            {'translatedText': 'correo electrónico'},
            {'translatedText': 'rápido'}]},
        {'translations': [
            {'translatedText': 'Inicio de sesión de correo electrónico'},
            {'translatedText': 'Correo electrónico en línea'},
            {'translatedText': 'Iniciar sesión'},
            {'translatedText': 'Correo electrónico intuitivo y útil'},
            {'translatedText': '15 GB de almacenamiento y acceso móvil'},
            {'translatedText': 'Página web oficial'},
            {'translatedText': 'Sitio oficial'},
            {'translatedText': 'Productos de alta calidad'},
            {'translatedText': 'Google analitico'},
            {'translatedText': '¡Pruebe Analytics hoy!'},
            ]}]

    mock_refresh_access_token.return_value = 'fake_access_token'

    # Arranges settings
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
    )

    # Arranges google ads objects
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        ads=ads_lib.Ads(_ADS_DATA_GOOGLE_ADS_API_RESPONSE),
        keywords=keywords_lib.Keywords(_KEYWORDS_GOOGLE_ADS_API_RESPONSE))

    # Arranges translation worker
    translation_worker = translation_worker_lib.TranslationWorker(
        cloud_translation_client=cloud_translation_client)

    # Act
    result = translation_worker.execute(
        settings=settings, google_ads_objects=google_ads_objects)

    # Asserts result
    self.assertEqual(2, result.keywords_modified)
    self.assertEqual(worker_result.Status.SUCCESS, result.status)

    # Asserts keywords translated
    actual_keywords_df = google_ads_objects.keywords.df()

    pd.testing.assert_frame_equal(
        actual_keywords_df, _EXPECTED_KEYWORDS_DF, check_index_type=False)

    # Asserts ads translated
    actual_ads_df = google_ads_objects.ads.df()

    pd.testing.assert_frame_equal(
        actual_ads_df, _EXPECTED_ADS_DF, check_index_type=False)

  def test_execute_empty_objects_returns_failure(self):
    # Arranges mock translation API
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    api_version = 3

    cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=credentials,
            gcp_project_name=gcp_project_name,
            api_version=api_version))

    # Arranges settings
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
    )

    # Arranges google ads objects
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects()

    # Arranges translation worker
    translation_worker = translation_worker_lib.TranslationWorker(
        cloud_translation_client=cloud_translation_client)

    # Act
    result = translation_worker.execute(
        settings=settings, google_ads_objects=google_ads_objects)

    # Asserts result
    self.assertEqual(worker_result.Status.FAILURE, result.status)


if __name__ == '__main__':
  absltest.main()

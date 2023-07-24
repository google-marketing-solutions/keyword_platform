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

"""Tests for the Ads data model class."""

import time
from unittest import mock

import pandas as pd

from py.data_models import ads as ads_lib
from absl.testing import absltest
from absl.testing import parameterized

_GOOGLE_ADS_RESPONSE = [
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

_EMPTY_GOOGLE_ADS_RESPONSE = [[
    {'results': [],
     'fieldMask': ('customer.id,campaign.name,adGroup.name,'
                   'adGroupAd.ad.responsiveSearchAd.headlines,'
                   'adGroupAd.ad.responsiveSearchAd.descriptions,'
                   'adGroupAd.ad.finalUrls'),
     'requestId': 'fake_request_id'}]]

_EXPECTED_DF = pd.DataFrame(
    {
        'Action': ['Add', 'Add'],
        'Customer ID': ['Enter customer ID', 'Enter customer ID'],
        'Ad status': ['Paused', 'Paused'],
        'Campaign': ['Gmail Test Campaign', 'Analytics Test Campaign'],
        'Ad group': ['Ad group 1', 'Ad group 1'],
        'Ad type': ['Responsive search ad', 'Responsive search ad'],
        'Headline 1': ['Email Login', 'Official Website'],
        'Original Headline 1': ['Email Login', 'Official Website'],
        'Headline 2': ['Online Email', 'Official Site'],
        'Original Headline 2': ['Online Email', 'Official Site'],
        'Headline 3': ['Sign in', 'High Quality Products'],
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
            'Email thats intuitive, efficient, and useful',
            'Google Analytics',
        ],
        'Original Description 1': [
            'Email thats intuitive, efficient, and useful',
            'Google Analytics',
        ],
        'Description 2': [
            '15 GB of storage, less spam, and mobile access',
            'Try Analytics today!',
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

_EXPECTED_CSV_DATA = (
    'Action,Customer ID,Ad status,Campaign,Ad group,Ad type,Headline 1,Original'
    ' Headline 1,Headline 2,Original Headline 2,Headline 3,Original Headline'
    ' 3,Headline 4,Original Headline 4,Headline 5,Original Headline 5,Headline'
    ' 6,Original Headline 6,Headline 7,Original Headline 7,Headline 8,Original'
    ' Headline 8,Headline 9,Original Headline 9,Headline 10,Original Headline'
    ' 10,Headline 11,Original Headline 11,Headline 12,Original Headline'
    ' 12,Headline 13,Original Headline 13,Headline 14,Original Headline'
    ' 14,Headline 15,Original Headline 15,Description 1,Original Description'
    ' 1,Description 2,Original Description 2,Description 3,Original Description'
    ' 3,Description 4,Original Description 4,Final URL,Label,Updates'
    ' applied\nAdd,Enter customer ID,Paused,Gmail Test Campaign,Ad group'
    ' 1,Responsive search ad,Email Login,Email Login,Online Email,Online'
    ' Email,Sign in,Sign in,,,,,,,,,,,,,,,,,,,,,,,,,"Email thats intuitive,'
    ' efficient, and useful","Email thats intuitive, efficient, and useful","15'
    ' GB of storage, less spam, and mobile access","15 GB of storage, less'
    ' spam, and mobile access",,,,,https://mail.google.com/,Keyword'
    ' Translator,[]\nAdd,Enter customer ID,Paused,Analytics Test Campaign,Ad'
    ' group 1,Responsive search ad,Official Website,Official Website,Official'
    ' Site,Official Site,High Quality Products,High Quality'
    ' Products,,,,,,,,,,,,,,,,,,,,,,,,,Google Analytics,Google Analytics,Try'
    ' Analytics today!,Try Analytics'
    ' today!,,,,,http://analytics.google.com,Keyword Translator,[]\n'
)

_EXPECTED_DF_AFTER_UPDATE = pd.DataFrame(
    {
        'Action': ['Add', 'Add'],
        'Customer ID': ['Enter customer ID', 'Enter customer ID'],
        'Ad status': ['Paused', 'Paused'],
        'Campaign': ['Gmail Test Campaign', 'Analytics Test Campaign'],
        'Ad group': ['Ad group 1', 'Ad group 1'],
        'Ad type': ['Responsive search ad', 'Responsive search ad'],
        'Headline 1': ['Email Login', 'Official Website'],
        'Original Headline 1': ['Email Login', 'Official Website'],
        'Headline 2': ['Online Email', 'Official Site'],
        'Original Headline 2': ['Online Email', 'Official Site'],
        'Headline 3': ['Sign in', 'High Quality Products'],
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
            'Email thats intuitive, efficient, and useful',
            'Google Analytics',
        ],
        'Original Description 1': [
            'Email thats intuitive, efficient, and useful',
            'Google Analytics',
        ],
        'Description 2': [
            '15 GB of storage, less spam, and mobile access',
            'Try Analytics today!',
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
        'Updates applied': [['Translated'], ['Translated']],
    },
)

_EXPECTED_DF_AFTER_CAMPAIGN_AND_AD_GROUP_UPDATE = pd.DataFrame(
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
        'Headline 1': ['Email Login', 'Official Website'],
        'Original Headline 1': ['Email Login', 'Official Website'],
        'Headline 2': ['Online Email', 'Official Site'],
        'Original Headline 2': ['Online Email', 'Official Site'],
        'Headline 3': ['Sign in', 'High Quality Products'],
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
            'Email thats intuitive, efficient, and useful',
            'Google Analytics',
        ],
        'Original Description 1': [
            'Email thats intuitive, efficient, and useful',
            'Google Analytics',
        ],
        'Description 2': [
            '15 GB of storage, less spam, and mobile access',
            'Try Analytics today!',
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

_EXPECTED_DF_EMPTY = pd.DataFrame(
    {
        'Action': pd.Series([], dtype='object'),
        'Customer ID': pd.Series([], dtype='object'),
        'Ad status': pd.Series([], dtype='object'),
        'Campaign': pd.Series([], dtype='object'),
        'Ad group': pd.Series([], dtype='object'),
        'Ad type': pd.Series([], dtype='object'),
        'Headline 1': pd.Series([], dtype='object'),
        'Original Headline 1': pd.Series([], dtype='object'),
        'Headline 2': pd.Series([], dtype='object'),
        'Original Headline 2': pd.Series([], dtype='object'),
        'Headline 3': pd.Series([], dtype='object'),
        'Original Headline 3': pd.Series([], dtype='object'),
        'Headline 4': pd.Series([], dtype='object'),
        'Original Headline 4': pd.Series([], dtype='object'),
        'Headline 5': pd.Series([], dtype='object'),
        'Original Headline 5': pd.Series([], dtype='object'),
        'Headline 6': pd.Series([], dtype='object'),
        'Original Headline 6': pd.Series([], dtype='object'),
        'Headline 7': pd.Series([], dtype='object'),
        'Original Headline 7': pd.Series([], dtype='object'),
        'Headline 8': pd.Series([], dtype='object'),
        'Original Headline 8': pd.Series([], dtype='object'),
        'Headline 9': pd.Series([], dtype='object'),
        'Original Headline 9': pd.Series([], dtype='object'),
        'Headline 10': pd.Series([], dtype='object'),
        'Original Headline 10': pd.Series([], dtype='object'),
        'Headline 11': pd.Series([], dtype='object'),
        'Original Headline 11': pd.Series([], dtype='object'),
        'Headline 12': pd.Series([], dtype='object'),
        'Original Headline 12': pd.Series([], dtype='object'),
        'Headline 13': pd.Series([], dtype='object'),
        'Original Headline 13': pd.Series([], dtype='object'),
        'Headline 14': pd.Series([], dtype='object'),
        'Original Headline 14': pd.Series([], dtype='object'),
        'Headline 15': pd.Series([], dtype='object'),
        'Original Headline 15': pd.Series([], dtype='object'),
        'Description 1': pd.Series([], dtype='object'),
        'Original Description 1': pd.Series([], dtype='object'),
        'Description 2': pd.Series([], dtype='object'),
        'Original Description 2': pd.Series([], dtype='object'),
        'Description 3': pd.Series([], dtype='object'),
        'Original Description 3': pd.Series([], dtype='object'),
        'Description 4': pd.Series([], dtype='object'),
        'Original Description 4': pd.Series([], dtype='object'),
        'Final URL': pd.Series([], dtype='object'),
        'Label': pd.Series([], dtype='object'),
        'Updates applied': pd.Series([], dtype='object'),
    },
)

_EXPECTED_CSV_DATA_EMPTY = (
    'Action,Customer ID,Ad status,Campaign,Ad group,Ad type,Headline 1,Original'
    ' Headline 1,Headline 2,Original Headline 2,Headline 3,Original Headline'
    ' 3,Headline 4,Original Headline 4,Headline 5,Original Headline 5,Headline'
    ' 6,Original Headline 6,Headline 7,Original Headline 7,Headline 8,Original'
    ' Headline 8,Headline 9,Original Headline 9,Headline 10,Original Headline'
    ' 10,Headline 11,Original Headline 11,Headline 12,Original Headline'
    ' 12,Headline 13,Original Headline 13,Headline 14,Original Headline'
    ' 14,Headline 15,Original Headline 15,Description 1,Original Description'
    ' 1,Description 2,Original Description 2,Description 3,Original Description'
    ' 3,Description 4,Original Description 4,Final URL,Label,Updates applied\n'
)

_EXPECTED_DF_AFTER_TRANSLATION = pd.DataFrame(
    {
        'Action': ['Add', 'Add'],
        'Customer ID': ['Enter customer ID', 'Enter customer ID'],
        'Ad status': ['Paused', 'Paused'],
        'Campaign': ['Gmail Test Campaign', 'Analytics Test Campaign'],
        'Ad group': ['Ad group 1', 'Ad group 1'],
        'Ad type': ['Responsive search ad', 'Responsive search ad'],
        'Headline 1': ['E-Mail-Login', 'Offizielle Website'],
        'Original Headline 1': ['Email Login', 'Official Website'],
        'Headline 2': ['Online-E-Mail', 'Offizielle Seite'],
        'Original Headline 2': ['Online Email', 'Official Site'],
        'Headline 3': ['anmelden', 'Produkte mit hoher Qualität'],
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
            'E-Mail, die intuitiv, effizient und nützlich ist',
            'Google Analytics',
        ],
        'Original Description 1': [
            'Email thats intuitive, efficient, and useful',
            'Google Analytics',
        ],
        'Description 2': [
            '15 GB Speicherplatz, weniger Spam und mobiler Zugriff',
            'Probieren Sie Analytics noch heute aus!',
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

_EXPECTED_DF_AFTER_TRANSLATION_WITH_AD_GROUP_UPDATE = pd.DataFrame(
    {
        'Action': ['Add', 'Add'],
        'Customer ID': ['Enter customer ID', 'Enter customer ID'],
        'Ad status': ['Paused', 'Paused'],
        'Campaign': [
            'Gmail Test Campaign (de)',
            'Analytics Test Campaign (de)',
        ],
        'Ad group': ['Ad group 1 (de)', 'Ad group 1 (de)'],
        'Ad type': ['Responsive search ad', 'Responsive search ad'],
        'Headline 1': ['E-Mail-Login', 'Offizielle Website'],
        'Original Headline 1': ['Email Login', 'Official Website'],
        'Headline 2': ['Online-E-Mail', 'Offizielle Seite'],
        'Original Headline 2': ['Online Email', 'Official Site'],
        'Headline 3': ['anmelden', 'Produkte mit hoher Qualität'],
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
            'E-Mail, die intuitiv, effizient und nützlich ist',
            'Google Analytics',
        ],
        'Original Description 1': [
            'Email thats intuitive, efficient, and useful',
            'Google Analytics',
        ],
        'Description 2': [
            '15 GB Speicherplatz, weniger Spam und mobiler Zugriff',
            'Probieren Sie Analytics noch heute aus!',
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


class AdsTest(parameterized.TestCase):

  @parameterized.named_parameters(
      {
          'testcase_name': 'response_with_ad_data',
          'google_ads_api_response': _GOOGLE_ADS_RESPONSE,
          'expected_df': _EXPECTED_DF,
      },
      {
          'testcase_name': 'no_ad_data',
          'google_ads_api_response': _EMPTY_GOOGLE_ADS_RESPONSE,
          'expected_df': _EXPECTED_DF_EMPTY,
      },
  )
  def test_df(self, google_ads_api_response, expected_df):
    ads = ads_lib.Ads(google_ads_api_response)
    actual_df = ads.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  @parameterized.named_parameters(
      {
          'testcase_name': 'response_with_ad_data',
          'google_ads_api_response': _GOOGLE_ADS_RESPONSE,
          'expected_csv_data': _EXPECTED_CSV_DATA,
      },
      {
          'testcase_name': 'no_ad_data',
          'google_ads_api_response': _EMPTY_GOOGLE_ADS_RESPONSE,
          'expected_csv_data': _EXPECTED_CSV_DATA_EMPTY,
      },
  )
  def test_csv_data(self, google_ads_api_response, expected_csv_data):
    ads = ads_lib.Ads(google_ads_api_response)
    actual_csv_data = ads.csv_data()

    self.assertEqual(actual_csv_data, expected_csv_data)

  @mock.patch.object(time, 'strftime', return_value='19700101-000000')
  def test_csv_file_name(self, _):
    expected_file_name = 'ads_19700101-000000.csv'
    ads = ads_lib.Ads(_GOOGLE_ADS_RESPONSE)
    actual_file_name = ads.csv_file_name()

    self.assertEqual(actual_file_name, expected_file_name)

  def test_add_update(self):
    expected_df = _EXPECTED_DF_AFTER_UPDATE

    ads = ads_lib.Ads(_GOOGLE_ADS_RESPONSE)
    ads.add_update(update='Translated')
    actual_df = ads.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  def test_columns(self):
    expected_columns = [
        'Action',
        'Customer ID',
        'Ad status',
        'Campaign',
        'Ad group',
        'Ad type',
        'Headline 1',
        'Original Headline 1',
        'Headline 2',
        'Original Headline 2',
        'Headline 3',
        'Original Headline 3',
        'Headline 4',
        'Original Headline 4',
        'Headline 5',
        'Original Headline 5',
        'Headline 6',
        'Original Headline 6',
        'Headline 7',
        'Original Headline 7',
        'Headline 8',
        'Original Headline 8',
        'Headline 9',
        'Original Headline 9',
        'Headline 10',
        'Original Headline 10',
        'Headline 11',
        'Original Headline 11',
        'Headline 12',
        'Original Headline 12',
        'Headline 13',
        'Original Headline 13',
        'Headline 14',
        'Original Headline 14',
        'Headline 15',
        'Original Headline 15',
        'Description 1',
        'Original Description 1',
        'Description 2',
        'Original Description 2',
        'Description 3',
        'Original Description 3',
        'Description 4',
        'Original Description 4',
        'Final URL',
        'Label',
        'Updates applied',
    ]

    ads = ads_lib.Ads(_GOOGLE_ADS_RESPONSE)
    actual_columns = ads.columns()

    self.assertEqual(actual_columns, expected_columns)

  def test_size(self):
    expected_size = 2

    ads = ads_lib.Ads(_GOOGLE_ADS_RESPONSE)
    actual_size = ads.size()

    self.assertEqual(actual_size, expected_size)

  def test_add_campaign_and_ad_group_suffixes(self):
    expected_df = _EXPECTED_DF_AFTER_CAMPAIGN_AND_AD_GROUP_UPDATE

    ads = ads_lib.Ads(_GOOGLE_ADS_RESPONSE)
    ads.add_campaign_and_ad_group_suffixes(suffix='(es)')
    actual_df = ads.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  def test_get_translation_frame(self):
    expected_df = pd.DataFrame(
        {
            'source_term': ['Email Login',
                            'Online Email',
                            'Sign in',
                            'Email thats intuitive, efficient, and useful',
                            '15 GB of storage, less spam, and mobile access',
                            'Official Website',
                            'Official Site',
                            'High Quality Products',
                            'Google Analytics',
                            'Try Analytics today!'],
            'target_terms': [{}, {}, {}, {}, {}, {}, {}, {}, {}, {}],
            'dataframe_locations': [
                [(0, 'Headline 1')],
                [(0, 'Headline 2')],
                [(0, 'Headline 3')],
                [(0, 'Description 1')],
                [(0, 'Description 2')],
                [(1, 'Headline 1')],
                [(1, 'Headline 2')],
                [(1, 'Headline 3')],
                [(1, 'Description 1')],
                [(1, 'Description 2')]],
            })

    ads = ads_lib.Ads(_GOOGLE_ADS_RESPONSE)
    actual_df = ads.get_translation_frame().df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  @parameterized.named_parameters(
      {
          'testcase_name': 'skip_ad_group_and_campaign_update',
          'update_ad_group_and_campaign_names': False,
          'expected_df': _EXPECTED_DF_AFTER_TRANSLATION,
      },
      {
          'testcase_name': 'apply_ad_group_and_campaign_update',
          'update_ad_group_and_campaign_names': True,
          'expected_df': _EXPECTED_DF_AFTER_TRANSLATION_WITH_AD_GROUP_UPDATE,
      },
  )
  def test_apply_translations(
      self, update_ad_group_and_campaign_names, expected_df):
    ads = ads_lib.Ads(_GOOGLE_ADS_RESPONSE)
    translation_frame = ads.get_translation_frame()

    translation_frame.add_translations(
        start_index=0,
        target_language_code='de',
        translations=[
            'E-Mail-Login',
            'Online-E-Mail',
            'anmelden',
            'E-Mail, die intuitiv, effizient und nützlich ist',
            '15 GB Speicherplatz, weniger Spam und mobiler Zugriff',
            'Offizielle Website',
            'Offizielle Seite',
            'Produkte mit hoher Qualität',
            'Google Analytics',
            'Probieren Sie Analytics noch heute aus!',
            ])

    ads.apply_translations(
        target_language='de',
        translation_frame=translation_frame,
        update_ad_group_and_campaign_names=update_ad_group_and_campaign_names)
    actual_df = ads.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)


if __name__ == '__main__':
  absltest.main()

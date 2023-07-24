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

"""Tests for the Ad Groups data model class."""

import time
from unittest import mock

import pandas as pd

from data_models import ad_groups as ad_groups_lib
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
               'approvalStatus': 'APPROVED'}}],
            'descriptions':
            [{'text': 'Amazing email!',
              'assetPerformanceLabel': 'PENDING',
              'policySummaryInfo':
              {'reviewStatus': 'REVIEWED',
               'approvalStatus': 'APPROVED'}}]},
           'resourceName': 'customers/123/ads/1011',
           'finalUrls': ['https://mail.google.com/']}}}],
      'fieldMask': ('customer.id,campaign.name,adGroup.name,'
                    'adGroupAd.ad.responsiveSearchAd.headlines,'
                    'adGroupAd.ad.responsiveSearchAd.descriptions,'
                    'adGroupAd.ad.finalUrls'),
      'requestId': 'fake_request_id'}],
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
            [{'text': 'Email that’s intuitive, efficient, and useful',
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

_EMPTY_GOOGLE_ADS_RESPONSE = [
    [{'results': [],
      'fieldMask': ('customer.id,campaign.name,adGroup.name,'
                    'adGroupAd.ad.responsiveSearchAd.headlines,'
                    'adGroupAd.ad.responsiveSearchAd.descriptions,'
                    'adGroupAd.ad.finalUrls'),
      'requestId': 'fake_request_id'}]]

_EXPECTED_DF = pd.DataFrame(
    {'Action': ['Add', 'Add', 'Add'],
     'Customer ID': [
         'Enter customer ID', 'Enter customer ID', 'Enter customer ID'],
     'Campaign': [
         'Gmail Test Campaign',
         'Gmail Test Campaign',
         'Analytics Test Campaign'],
     'Ad group': ['Ad group 1', 'Ad group 1', 'Ad group 1'],
     'Status': ['Paused', 'Paused', 'Paused'],
     'Label': [
         'Keyword Translator', 'Keyword Translator', 'Keyword Translator'],
     'Updates applied': [[], [], []]},
)

_EXPECTED_CSV_DATA = (
    'Action,Customer ID,Campaign,Ad group,Status,Label,Updates'
    ' applied\nAdd,Enter customer ID,Gmail Test Campaign,Ad group'
    ' 1,Paused,Keyword Translator,[]\nAdd,Enter customer ID,Gmail Test'
    ' Campaign,Ad group 1,Paused,Keyword Translator,[]\nAdd,Enter customer'
    ' ID,Analytics Test Campaign,Ad group 1,Paused,Keyword Translator,[]\n'
)

_EXPECTED_DF_AFTER_UPDATE = pd.DataFrame(
    {'Action': ['Add', 'Add', 'Add'],
     'Customer ID': [
         'Enter customer ID', 'Enter customer ID', 'Enter customer ID'],
     'Campaign': [
         'Gmail Test Campaign',
         'Gmail Test Campaign',
         'Analytics Test Campaign'],
     'Ad group': ['Ad group 1', 'Ad group 1', 'Ad group 1'],
     'Status': ['Paused', 'Paused', 'Paused'],
     'Label': [
         'Keyword Translator', 'Keyword Translator', 'Keyword Translator'],
     'Updates applied': [['Translated'], ['Translated'], ['Translated']]},
)

_EXPECTED_DF_AFTER_AD_GROUP_UPDATE = pd.DataFrame(
    {'Action': ['Add', 'Add', 'Add'],
     'Customer ID': [
         'Enter customer ID', 'Enter customer ID', 'Enter customer ID'],
     'Campaign': [
         'Gmail Test Campaign',
         'Gmail Test Campaign',
         'Analytics Test Campaign'],
     'Ad group': ['Ad group 1 (es)', 'Ad group 1 (es)', 'Ad group 1 (es)'],
     'Status': ['Paused', 'Paused', 'Paused'],
     'Label': [
         'Keyword Translator', 'Keyword Translator', 'Keyword Translator'],
     'Updates applied': [[], [], []]},
)

_EXPECTED_DF_EMPTY = pd.DataFrame(
    {'Action': pd.Series([], dtype='object'),
     'Customer ID': pd.Series([], dtype='object'),
     'Campaign': pd.Series([], dtype='object'),
     'Ad group': pd.Series([], dtype='object'),
     'Status': pd.Series([], dtype='object'),
     'Label': pd.Series([], dtype='object'),
     'Updates applied': pd.Series([], dtype='object')},
)

_EXPECTED_CSV_DATA_EMPTY = (
    'Action,Customer ID,Campaign,Ad group,Status,Label,Updates applied\n'
)


class AdGroupsTest(parameterized.TestCase):

  @parameterized.named_parameters(
      {
          'testcase_name': 'response_with_ad_group_data',
          'google_ads_api_response': _GOOGLE_ADS_RESPONSE,
          'expected_df': _EXPECTED_DF,
      },
      {
          'testcase_name': 'no_ad_group_data',
          'google_ads_api_response': _EMPTY_GOOGLE_ADS_RESPONSE,
          'expected_df': _EXPECTED_DF_EMPTY,
      },
  )
  def test_df(self, google_ads_api_response, expected_df):
    ad_groups = ad_groups_lib.AdGroups(google_ads_api_response)
    actual_df = ad_groups.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  @parameterized.named_parameters(
      {
          'testcase_name': 'response_with_ad_group_data',
          'google_ads_api_response': _GOOGLE_ADS_RESPONSE,
          'expected_csv_data': _EXPECTED_CSV_DATA,
      },
      {
          'testcase_name': 'no_ad_group_data',
          'google_ads_api_response': _EMPTY_GOOGLE_ADS_RESPONSE,
          'expected_csv_data': _EXPECTED_CSV_DATA_EMPTY,
      },
  )
  def test_csv_data(self, google_ads_api_response, expected_csv_data):
    ad_groups = ad_groups_lib.AdGroups(google_ads_api_response)
    actual_csv_data = ad_groups.csv_data()

    self.assertEqual(actual_csv_data, expected_csv_data)

  @mock.patch.object(time, 'strftime', return_value='19700101-000000')
  def test_csv_file_name(self, _):
    expected_file_name = 'ad_groups_19700101-000000.csv'
    ad_groups = ad_groups_lib.AdGroups(_GOOGLE_ADS_RESPONSE)
    actual_file_name = ad_groups.csv_file_name()

    self.assertEqual(actual_file_name, expected_file_name)

  def test_add_update(self):
    expected_df = _EXPECTED_DF_AFTER_UPDATE

    ad_groups = ad_groups_lib.AdGroups(_GOOGLE_ADS_RESPONSE)
    ad_groups.add_update(update='Translated')
    actual_df = ad_groups.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  def test_columns(self):
    expected_columns = [
        'Action',
        'Customer ID',
        'Campaign',
        'Ad group',
        'Status',
        'Label',
        'Updates applied',
    ]

    ad_groups = ad_groups_lib.AdGroups(_GOOGLE_ADS_RESPONSE)
    actual_columns = ad_groups.columns()

    self.assertEqual(actual_columns, expected_columns)

  def test_size(self):
    expected_size = 3

    ad_groups = ad_groups_lib.AdGroups(_GOOGLE_ADS_RESPONSE)
    actual_size = ad_groups.size()

    self.assertEqual(actual_size, expected_size)

  def test_add_ad_group_suffix(self):
    expected_df = _EXPECTED_DF_AFTER_AD_GROUP_UPDATE

    ad_groups = ad_groups_lib.AdGroups(_GOOGLE_ADS_RESPONSE)
    ad_groups.add_ad_group_suffix(suffix='(es)')
    actual_df = ad_groups.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)


if __name__ == '__main__':
  absltest.main()

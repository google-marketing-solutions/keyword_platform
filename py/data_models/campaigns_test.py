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

"""Tests for the Campaigns data model class."""

import time
from unittest import mock

import pandas as pd

from absl.testing import absltest
from absl.testing import parameterized
from py.data_models import campaigns as campaigns_lib


_GOOGLE_ADS_RESPONSE = [
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

_EMPTY_GOOGLE_ADS_RESPONSE = [[{
    'results': [],
    'fieldMask': (
        'campaign.id,campaign.name,campaign.advertisingChannelType,'
        'campaign.biddingStrategyType'
    ),
    'requestId': 'fake_req_id',
}]]

_EXPECTED_DF = pd.DataFrame(
    {'Action': ['Add', 'Add', 'Add'],
     'Campaign status': ['Paused', 'Paused', 'Paused'],
     'Customer ID': [
         'Enter customer ID', 'Enter customer ID', 'Enter customer ID'],
     'Campaign': ['Test Campaign 0', 'Test Campaign 1', 'Test Campaign 2'],
     'Campaign type': ['SEARCH', 'SEARCH', 'SEARCH'],
     'Bid strategy type': [
         'TARGET_SPEND', 'TARGET_SPEND', 'MAXIMIZE_CONVERSIONS'],
     'Label': [
         'Keyword Translator', 'Keyword Translator', 'Keyword Translator'],
     'Updates applied': [[], [], []]},
)

_EXPECTED_CSV_DATA = (
    'Action,Campaign status,Customer ID,Campaign,Campaign type,Bid strategy'
    ' type,Label,Updates applied\nAdd,Paused,Enter customer ID,Test Campaign'
    ' 0,SEARCH,TARGET_SPEND,Keyword Translator,[]\nAdd,Paused,Enter customer'
    ' ID,Test Campaign 1,SEARCH,TARGET_SPEND,Keyword'
    ' Translator,[]\nAdd,Paused,Enter customer ID,Test Campaign'
    ' 2,SEARCH,MAXIMIZE_CONVERSIONS,Keyword Translator,[]\n'
)

_EXPECTED_DF_EMPTY = pd.DataFrame(
    {'Action': pd.Series([], dtype='object'),
     'Campaign status': pd.Series([], dtype='object'),
     'Customer ID': pd.Series([], dtype='object'),
     'Campaign': pd.Series([], dtype='object'),
     'Campaign type': pd.Series([], dtype='object'),
     'Bid strategy type': pd.Series([], dtype='object'),
     'Label': pd.Series([], dtype='object'),
     'Updates applied': pd.Series([], dtype='object')},
)

_EXPECTED_CSV_DATA_EMPTY = (
    'Action,Campaign status,Customer ID,Campaign,Campaign type,Bid strategy'
    ' type,Label,Updates applied\n'
)

_EXPECTED_DF_AFTER_UPDATE = pd.DataFrame(
    {'Action': ['Add', 'Add', 'Add'],
     'Campaign status': ['Paused', 'Paused', 'Paused'],
     'Customer ID': [
         'Enter customer ID', 'Enter customer ID', 'Enter customer ID'],
     'Campaign': ['Test Campaign 0', 'Test Campaign 1', 'Test Campaign 2'],
     'Campaign type': ['SEARCH', 'SEARCH', 'SEARCH'],
     'Bid strategy type': [
         'TARGET_SPEND', 'TARGET_SPEND', 'MAXIMIZE_CONVERSIONS'],
     'Label': [
         'Keyword Translator', 'Keyword Translator', 'Keyword Translator'],
     'Updates applied': [['Translated'], ['Translated'], ['Translated']]},
)

_EXPECTED_LIST = list([
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

_EXPECTED_LIST_EMPTY = list()


class CampaignsTest(parameterized.TestCase):

  @parameterized.named_parameters(
      {
          'testcase_name': 'response_with_campaign_data',
          'google_ads_api_response': _GOOGLE_ADS_RESPONSE,
          'expected_df': _EXPECTED_DF,
      },
      {
          'testcase_name': 'no_campaign_data',
          'google_ads_api_response': _EMPTY_GOOGLE_ADS_RESPONSE,
          'expected_df': _EXPECTED_DF_EMPTY,
      },
  )
  def test_df(self, google_ads_api_response, expected_df):
    campaigns = campaigns_lib.Campaigns(google_ads_api_response)
    actual_df = campaigns.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  @parameterized.named_parameters(
      {
          'testcase_name': 'response_with_campaign_data',
          'google_ads_api_response': _GOOGLE_ADS_RESPONSE,
          'expected_list': _EXPECTED_LIST,
      },
      {
          'testcase_name': 'no_campaign_data',
          'google_ads_api_response': _EMPTY_GOOGLE_ADS_RESPONSE,
          'expected_list': _EXPECTED_LIST_EMPTY,
      },
  )
  def test_campaigns_list(self, google_ads_api_response, expected_list):
    campaigns = campaigns_lib.Campaigns(google_ads_api_response)
    actual_list = campaigns.campaigns_list()

    self.assertListEqual(actual_list, expected_list)

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
    campaigns = campaigns_lib.Campaigns(google_ads_api_response)
    actual_csv_data = campaigns.csv_data()

    self.assertEqual(actual_csv_data, expected_csv_data)

  @mock.patch.object(time, 'strftime', return_value='19700101-000000')
  def test_csv_file_name(self, _):
    expected_file_name = 'campaigns_19700101-000000.csv'
    campaigns = campaigns_lib.Campaigns(_GOOGLE_ADS_RESPONSE)
    actual_file_name = campaigns.csv_file_name()

    self.assertEqual(actual_file_name, expected_file_name)

  def test_add_update(self):
    expected_df = _EXPECTED_DF_AFTER_UPDATE

    campaigns = campaigns_lib.Campaigns(_GOOGLE_ADS_RESPONSE)
    campaigns.add_update(update='Translated')
    actual_df = campaigns.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  def test_columns(self):
    expected_columns = [
        'Action',
        'Campaign status',
        'Customer ID',
        'Campaign',
        'Campaign type',
        'Bid strategy type',
        'Label',
        'Updates applied',
    ]

    campaigns = campaigns_lib.Campaigns(_GOOGLE_ADS_RESPONSE)
    actual_columns = campaigns.columns()

    self.assertEqual(actual_columns, expected_columns)

  def test_size(self):
    expected_size = 3

    campaigns = campaigns_lib.Campaigns(_GOOGLE_ADS_RESPONSE)
    actual_size = campaigns.size()

    self.assertEqual(actual_size, expected_size)

  def test_campaign_names(self):
    expected_campaign_names = [
        'Test Campaign 0', 'Test Campaign 1', 'Test Campaign 2']

    campaigns = campaigns_lib.Campaigns(_GOOGLE_ADS_RESPONSE)
    actual_campaign_names = campaigns.campaign_names()

    self.assertEqual(actual_campaign_names, expected_campaign_names)


if __name__ == '__main__':
  absltest.main()

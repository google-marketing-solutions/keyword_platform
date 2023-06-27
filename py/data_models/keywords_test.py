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

"""Tests for the Keywords data model class."""

import time
from unittest import mock

import pandas as pd

from py.data_models import keywords as keywords_lib
from py.data_models import translation_frame as translation_frame_lib
from absl.testing import absltest
from absl.testing import parameterized

_GOOGLE_ADS_RESPONSE = ([
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
      'requestId': 'fake_req_id'}]])

_EMPTY_GOOGLE_ADS_RESPONSE = ([
    [{'results': [],
      'fieldMask': ('customer.id,campaign.name,campaign.advertisingChannelType,'
                    'campaign.biddingStrategyType,adGroup.name,'
                    'adGroupCriterion.keyword.text,'
                    'adGroupCriterion.keyword.matchType'),
      'requestId': 'fake_req_id'}]])

_EXPECTED_DF = pd.DataFrame(
    {'Action': ['Add', 'Add'],
     'Customer ID': ['Enter customer ID', 'Enter customer ID'],
     'Campaign': ['Gmail Test Campaign', 'Gmail Test Campaign'],
     'Ad group': ['Ad group 1', 'Ad group 1'],
     'Keyword': ['e mail', 'email'],
     'Original Keyword': ['e mail', 'email'],
     'Match Type': ['BROAD', 'BROAD'],
     'Keyword status': ['Paused', 'Paused'],
     'Updates applied': [[], []]},
)

_EXPECTED_CSV_DATA = (
    'Action,Customer ID,Campaign,Ad group,Keyword,Original Keyword,Match'
    ' Type,Keyword status,Updates applied\nAdd,Enter customer ID,Gmail Test'
    ' Campaign,Ad group 1,e mail,e mail,BROAD,Paused,[]\nAdd,Enter customer'
    ' ID,Gmail Test Campaign,Ad group 1,email,email,BROAD,Paused,[]\n'
)

_EXPECTED_DF_EMPTY = pd.DataFrame(
    {'Action': pd.Series([], dtype='object'),
     'Customer ID': pd.Series([], dtype='object'),
     'Campaign': pd.Series([], dtype='object'),
     'Ad group': pd.Series([], dtype='object'),
     'Keyword': pd.Series([], dtype='object'),
     'Original Keyword': pd.Series([], dtype='object'),
     'Match Type': pd.Series([], dtype='object'),
     'Keyword status': pd.Series([], dtype='object'),
     'Updates applied': pd.Series([], dtype='object')},
)

_EXPECTED_CSV_DATA_EMPTY = (
    'Action,Customer ID,Campaign,Ad group,Keyword,Original Keyword,Match'
    ' Type,Keyword status,Updates applied\n'
)

_EXPECTED_DF_AFTER_UPDATE = pd.DataFrame(
    {'Action': ['Add', 'Add'],
     'Customer ID': ['Enter customer ID', 'Enter customer ID'],
     'Campaign': ['Gmail Test Campaign', 'Gmail Test Campaign'],
     'Ad group': ['Ad group 1', 'Ad group 1'],
     'Keyword': ['e mail', 'email'],
     'Original Keyword': ['e mail', 'email'],
     'Match Type': ['BROAD', 'BROAD'],
     'Keyword status': ['Paused', 'Paused'],
     'Updates applied': [['Translated'], ['Translated']]},
)

_EXPECTED_DF_AFTER_AD_GROUP_UPDATE = pd.DataFrame(
    {'Action': ['Add', 'Add'],
     'Customer ID': ['Enter customer ID', 'Enter customer ID'],
     'Campaign': ['Gmail Test Campaign', 'Gmail Test Campaign'],
     'Ad group': ['Ad group 1 (es)', 'Ad group 1 (es)'],
     'Keyword': ['e mail', 'email'],
     'Original Keyword': ['e mail', 'email'],
     'Match Type': ['BROAD', 'BROAD'],
     'Keyword status': ['Paused', 'Paused'],
     'Updates applied': [[], []]},
)

_EXPECTED_DF_AFTER_TRANSLATION = pd.DataFrame(
    {'Action': ['Add', 'Add'],
     'Customer ID': ['Enter customer ID', 'Enter customer ID'],
     'Campaign': ['Gmail Test Campaign', 'Gmail Test Campaign'],
     'Ad group': ['Ad group 1', 'Ad group 1'],
     'Keyword': ['correo electrónico', 'c-electrónico'],
     'Original Keyword': ['e mail', 'email'],
     'Match Type': ['BROAD', 'BROAD'],
     'Keyword status': ['Paused', 'Paused'],
     'Updates applied': [[], []]},
)

_EXPECTED_DF_AFTER_TRANSLATION_WITH_AD_GROUP_UPDATE = pd.DataFrame(
    {'Action': ['Add', 'Add'],
     'Customer ID': ['Enter customer ID', 'Enter customer ID'],
     'Campaign': ['Gmail Test Campaign (es)', 'Gmail Test Campaign (es)'],
     'Ad group': ['Ad group 1 (es)', 'Ad group 1 (es)'],
     'Keyword': ['correo electrónico', 'c-electrónico'],
     'Original Keyword': ['e mail', 'email'],
     'Match Type': ['BROAD', 'BROAD'],
     'Keyword status': ['Paused', 'Paused'],
     'Updates applied': [[], []]},
)


class KeywordsTest(parameterized.TestCase):

  @parameterized.named_parameters(
      {
          'testcase_name': 'response_with_keywords_data',
          'google_ads_api_response': _GOOGLE_ADS_RESPONSE,
          'expected_df': _EXPECTED_DF,
      },
      {
          'testcase_name': 'no_keywords_data',
          'google_ads_api_response': _EMPTY_GOOGLE_ADS_RESPONSE,
          'expected_df': _EXPECTED_DF_EMPTY,
      },
  )
  def test_df(self, google_ads_api_response, expected_df):
    keywords = keywords_lib.Keywords(google_ads_api_response)
    actual_df = keywords.df()

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
    keywords = keywords_lib.Keywords(google_ads_api_response)
    actual_csv_data = keywords.csv_data()

    self.assertEqual(actual_csv_data, expected_csv_data)

  @mock.patch.object(time, 'strftime', return_value='19700101-000000')
  def test_csv_file_name(self, _):
    expected_file_name = 'campaigns_19700101-000000.csv'
    keywords = keywords_lib.Keywords(_GOOGLE_ADS_RESPONSE)
    actual_file_name = keywords.csv_file_name()

    self.assertEqual(actual_file_name, expected_file_name)

  def test_add_update(self):
    expected_df = _EXPECTED_DF_AFTER_UPDATE

    keywords = keywords_lib.Keywords(_GOOGLE_ADS_RESPONSE)
    keywords.add_update(update='Translated')
    actual_df = keywords.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  def test_columns(self):
    expected_columns = [
        'Action',
        'Customer ID',
        'Campaign',
        'Ad group',
        'Keyword',
        'Original Keyword',
        'Match Type',
        'Keyword status',
        'Updates applied',
    ]

    keywords = keywords_lib.Keywords(_GOOGLE_ADS_RESPONSE)
    actual_columns = keywords.columns()

    self.assertEqual(actual_columns, expected_columns)

  def test_size(self):
    expected_size = 2

    keywords = keywords_lib.Keywords(_GOOGLE_ADS_RESPONSE)
    actual_size = keywords.size()

    self.assertEqual(actual_size, expected_size)

  def test_set_keyword(self):
    expected_keyword = 'correo electrónico'

    keywords = keywords_lib.Keywords(_GOOGLE_ADS_RESPONSE)
    keywords.set_keyword(row=0, new_keyword='correo electrónico')
    actual_keyword = keywords.df().loc[0, 'Keyword']

    self.assertEqual(actual_keyword, expected_keyword)

  def test_add_ad_group_suffix(self):
    expected_df = _EXPECTED_DF_AFTER_AD_GROUP_UPDATE

    keywords = keywords_lib.Keywords(_GOOGLE_ADS_RESPONSE)
    keywords.add_ad_group_suffix(suffix='(es)')
    actual_df = keywords.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  def test_get_translation_frame(self):
    expected_df = pd.DataFrame(
        {
            'source_term': ['e mail', 'email'],
            'target_terms': [{}, {}],
            'dataframe_locations': [[(0, 'Keyword')], [(1, 'Keyword')]],
            })

    keywords = keywords_lib.Keywords(_GOOGLE_ADS_RESPONSE)
    actual_df = keywords.get_translation_frame().df()

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
    translation_frame = translation_frame_lib.TranslationFrame(
        {'e mail': [(0, 'Keyword')], 'email': [(1, 'Keyword')]})

    translation_frame.add_translations(
        start_index=0,
        target_language_code='es',
        translations=['correo electrónico', 'c-electrónico'])

    keywords = keywords_lib.Keywords(_GOOGLE_ADS_RESPONSE)
    keywords.apply_translations(
        target_language='es',
        translation_frame=translation_frame,
        update_ad_group_and_campaign_names=update_ad_group_and_campaign_names)
    actual_df = keywords.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)


if __name__ == '__main__':
  absltest.main()

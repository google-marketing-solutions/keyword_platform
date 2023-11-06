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

"""Tests for the Extensions data model class."""

import time
from unittest import mock

import pandas as pd

from absl.testing import absltest
from absl.testing import parameterized
from data_models import extensions as extensions_lib


_GOOGLE_ADS_RESPONSE = [
    [{
        'results': [
            {
                'campaign': {
                    'resourceName': (
                        'customers/8112880374/campaigns/17562611408'
                    ),
                    'name': 'Campaign 1',
                },
                'adGroup': {
                    'resourceName': (
                        'customers/8112880374/adGroups/139665100522'
                    ),
                    'name': 'Ad group 1',
                },
                'asset': {
                    'resourceName': 'customers/8112880374/assets/110379943909',
                    'type': 'STRUCTURED_SNIPPET',
                    'structuredSnippetAsset': {
                        'header': 'Brands',
                        'values': ['Google', 'Pixel', 'Android'],
                    },
                },
                'adGroupAsset': {
                    'resourceName': (
                        'customers/8112880374/adGroupAssets/139665100522'
                        '~110379943909~STRUCTURED_SNIPPET'
                    ),
                    'status': 'ENABLED',
                },
            },
            {
                'campaign': {
                    'resourceName': (
                        'customers/8112880374/campaigns/17562611408'
                    ),
                    'name': 'Campaign 1',
                },
                'adGroup': {
                    'resourceName': (
                        'customers/8112880374/adGroups/139665100522'
                    ),
                    'name': 'Ad group 1',
                },
                'asset': {
                    'resourceName': 'customers/8112880374/assets/110373249611',
                    'type': 'SITELINK',
                    'sitelinkAsset': {
                        'linkText': 'This is a link text',
                        'description1': 'This is a Description 1',
                        'description2': 'This is a Description 2',
                    },
                },
                'adGroupAsset': {
                    'resourceName': (
                        'customers/8112880374/adGroupAssets/139665100522'
                        '~110373249611~SITELINK'
                    ),
                    'status': 'ENABLED',
                },
            },
            {
                'campaign': {
                    'resourceName': (
                        'customers/8112880374/campaigns/17562611408'
                    ),
                    'name': 'Campaign 1',
                },
                'adGroup': {
                    'resourceName': (
                        'customers/8112880374/adGroups/139665100522'
                    ),
                    'name': 'Ad group 1',
                },
                'asset': {
                    'resourceName': 'customers/8112880374/assets/110380162771',
                    'type': 'CALLOUT',
                    'calloutAsset': {'calloutText': 'Buy my product now'},
                },
                'adGroupAsset': {
                    'resourceName': (
                        'customers/8112880374/adGroupAssets/139665100522'
                        '~110380162771~CALLOUT'
                    ),
                    'status': 'ENABLED',
                },
            },
        ],
        'fieldMask': (
            'campaign.name,asset.type,asset.structuredSnippetAsset.header,'
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
                    'resourceName': (
                        'customers/8112880374/campaigns/17562611408'
                    ),
                    'name': 'Campaign 1',
                },
                'asset': {
                    'resourceName': 'customers/8112880374/assets/110379943909',
                    'type': 'STRUCTURED_SNIPPET',
                    'structuredSnippetAsset': {
                        'header': 'Brands',
                        'values': ['Google', 'Pixel', 'Android'],
                    },
                },
                'campaignAsset': {
                    'resourceName': (
                        'customers/8112880374/campaignAssets/17562611408'
                        '~110379943909~STRUCTURED_SNIPPET'
                    ),
                    'status': 'ENABLED',
                },
            },
            {
                'campaign': {
                    'resourceName': (
                        'customers/8112880374/campaigns/17562611408'
                    ),
                    'name': 'Campaign 1',
                },
                'asset': {
                    'resourceName': 'customers/8112880374/assets/110373249611',
                    'type': 'SITELINK',
                    'sitelinkAsset': {
                        'linkText': 'This is a link text',
                        'description1': 'This is a Description 1',
                        'description2': 'This is a Description 2',
                    },
                },
                'campaignAsset': {
                    'resourceName': (
                        'customers/8112880374/campaignAssets/17562611408'
                        '~110373249611~SITELINK'
                    ),
                    'status': 'ENABLED',
                },
            },
            {
                'campaign': {
                    'resourceName': (
                        'customers/8112880374/campaigns/17562611408'
                    ),
                    'name': 'Campaign 1',
                },
                'asset': {
                    'resourceName': 'customers/8112880374/assets/110373390950',
                    'type': 'SITELINK',
                    'sitelinkAsset': {
                        'linkText': 'Calendar',
                        'description1': 'Open Calendar',
                        'description2': 'Calendar open',
                    },
                },
                'campaignAsset': {
                    'resourceName': (
                        'customers/8112880374/campaignAssets/17562611408'
                        '~110373390950~SITELINK'
                    ),
                    'status': 'ENABLED',
                },
            },
            {
                'campaign': {
                    'resourceName': (
                        'customers/8112880374/campaigns/17562611408'
                    ),
                    'name': 'Campaign 1',
                },
                'asset': {
                    'resourceName': 'customers/8112880374/assets/110380162771',
                    'type': 'CALLOUT',
                    'calloutAsset': {'calloutText': 'Buy my product now'},
                },
                'campaignAsset': {
                    'resourceName': (
                        'customers/8112880374/campaignAssets/17562611408'
                        '~110380162771~CALLOUT'
                    ),
                    'status': 'ENABLED',
                },
            },
        ],
        'fieldMask': (
            'campaign.name,asset.type,asset.structuredSnippetAsset.header,'
            'asset.structuredSnippetAsset.values,'
            'asset.calloutAsset.calloutText,asset.sitelinkAsset.description1,'
            'asset.sitelinkAsset.description2,asset.sitelinkAsset.linkText,'
            'campaignAsset.status'
        ),
        'requestId': 'fake_request_id',
    }],
]

_EMPTY_GOOGLE_ADS_RESPONSE = [[{
    'results': [],
    'fieldMask': (
        'campaign.name,asset.type,asset.structuredSnippetAsset.header,'
        'asset.structuredSnippetAsset.values,asset.calloutAsset.calloutText,'
        'asset.sitelinkAsset.description1,asset.sitelinkAsset.description2,'
        'asset.sitelinkAsset.linkText,adGroupAsset.status,adGroup.name'
    ),
    'requestId': 'fake_request_id',
}]]

_EXPECTED_DF = pd.DataFrame({
    'Action': ['Add', 'Add', 'Add', 'Add', 'Add', 'Add', 'Add'],
    'Customer ID': [
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
    ],
    'Campaign': [
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
    ],
    'Ad group': ['Ad group 1', 'Ad group 1', 'Ad group 1', '', '', '', ''],
    'Asset type': [
        'STRUCTURED_SNIPPET',
        'SITELINK',
        'CALLOUT',
        'STRUCTURED_SNIPPET',
        'SITELINK',
        'SITELINK',
        'CALLOUT',
    ],
    'Status': [
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
    ],
    'Structured snippet header': ['Brands', '', '', 'Brands', '', '', ''],
    'Structured snippet values': [
        'Google;Pixel;Android',
        '',
        '',
        'Google;Pixel;Android',
        '',
        '',
        '',
    ],
    'Original structured snippet values': [
        'Google;Pixel;Android',
        '',
        '',
        'Google;Pixel;Android',
        '',
        '',
        '',
    ],
    'Callout text': [
        '',
        '',
        'Buy my product now',
        '',
        '',
        '',
        'Buy my product now',
    ],
    'Original callout text': [
        '',
        '',
        'Buy my product now',
        '',
        '',
        '',
        'Buy my product now',
    ],
    'Sitelink description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Original sitelink description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Sitelink description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        'Calendar open',
        '',
    ],
    'Original sitelink description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        'Calendar open',
        '',
    ],
    'Sitelink link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Original sitelink link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Updates applied': [[], [], [], [], [], [], []],
})

_EXPECTED_CSV_DATA = (
    'Action,Customer ID,Campaign,Ad group,Asset type,Status,Structured snippet'
    ' header,Structured snippet values,Original structured snippet'
    ' values,Callout text,Original callout text,Sitelink description 1,Original'
    ' sitelink description 1,Sitelink description 2,Original sitelink'
    ' description 2,Sitelink link text,Original sitelink link text,Updates'
    ' applied\nAdd,Enter customer ID,Campaign 1,Ad group'
    ' 1,STRUCTURED_SNIPPET,ENABLED,Brands,Google;Pixel;Android,Google;Pixel;Android,,,,,,,,,[]\nAdd,Enter'
    ' customer ID,Campaign 1,Ad group 1,SITELINK,ENABLED,,,,,,This is a'
    ' Description 1,This is a Description 1,This is a Description 2,This is a'
    ' Description 2,This is a link text,This is a link text,[]\nAdd,Enter'
    ' customer ID,Campaign 1,Ad group 1,CALLOUT,ENABLED,,,,Buy my product'
    ' now,Buy my product now,,,,,,,[]\nAdd,Enter customer ID,Campaign'
    ' 1,,STRUCTURED_SNIPPET,ENABLED,Brands,Google;Pixel;Android,Google;Pixel;Android,,,,,,,,,[]\nAdd,Enter'
    ' customer ID,Campaign 1,,SITELINK,ENABLED,,,,,,This is a Description'
    ' 1,This is a Description 1,This is a Description 2,This is a Description'
    ' 2,This is a link text,This is a link text,[]\nAdd,Enter customer'
    ' ID,Campaign 1,,SITELINK,ENABLED,,,,,,Open Calendar,Open Calendar,Calendar'
    ' open,Calendar open,Calendar,Calendar,[]\nAdd,Enter customer ID,Campaign'
    ' 1,,CALLOUT,ENABLED,,,,Buy my product now,Buy my product now,,,,,,,[]\n'
)

_EXPECTED_DF_AFTER_UPDATE = pd.DataFrame({
    'Action': ['Add', 'Add', 'Add', 'Add', 'Add', 'Add', 'Add'],
    'Customer ID': [
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
    ],
    'Campaign': [
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
    ],
    'Ad group': ['Ad group 1', 'Ad group 1', 'Ad group 1', '', '', '', ''],
    'Asset type': [
        'STRUCTURED_SNIPPET',
        'SITELINK',
        'CALLOUT',
        'STRUCTURED_SNIPPET',
        'SITELINK',
        'SITELINK',
        'CALLOUT',
    ],
    'Status': [
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
    ],
    'Structured snippet header': ['Brands', '', '', 'Brands', '', '', ''],
    'Structured snippet values': [
        'Google;Pixel;Android',
        '',
        '',
        'Google;Pixel;Android',
        '',
        '',
        '',
    ],
    'Original structured snippet values': [
        'Google;Pixel;Android',
        '',
        '',
        'Google;Pixel;Android',
        '',
        '',
        '',
    ],
    'Callout text': [
        '',
        '',
        'Buy my product now',
        '',
        '',
        '',
        'Buy my product now',
    ],
    'Original callout text': [
        '',
        '',
        'Buy my product now',
        '',
        '',
        '',
        'Buy my product now',
    ],
    'Sitelink description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Original sitelink description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Sitelink description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        'Calendar open',
        '',
    ],
    'Original sitelink description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        'Calendar open',
        '',
    ],
    'Sitelink link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Original sitelink link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Updates applied': [
        ['Translated'],
        ['Translated'],
        ['Translated'],
        ['Translated'],
        ['Translated'],
        ['Translated'],
        ['Translated'],
    ],
})

_EXPECTED_DF_AFTER_CAMPAIGN_AND_AD_GROUP_UPDATE = pd.DataFrame({
    'Action': ['Add', 'Add', 'Add', 'Add', 'Add', 'Add', 'Add'],
    'Customer ID': [
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
    ],
    'Campaign': [
        'Campaign 1 (es)',
        'Campaign 1 (es)',
        'Campaign 1 (es)',
        'Campaign 1 (es)',
        'Campaign 1 (es)',
        'Campaign 1 (es)',
        'Campaign 1 (es)',
    ],
    'Ad group': [
        'Ad group 1 (es)',
        'Ad group 1 (es)',
        'Ad group 1 (es)',
        '',
        '',
        '',
        '',
    ],
    'Asset type': [
        'STRUCTURED_SNIPPET',
        'SITELINK',
        'CALLOUT',
        'STRUCTURED_SNIPPET',
        'SITELINK',
        'SITELINK',
        'CALLOUT',
    ],
    'Status': [
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
    ],
    'Structured snippet header': ['Brands', '', '', 'Brands', '', '', ''],
    'Structured snippet values': [
        'Google;Pixel;Android',
        '',
        '',
        'Google;Pixel;Android',
        '',
        '',
        '',
    ],
    'Original structured snippet values': [
        'Google;Pixel;Android',
        '',
        '',
        'Google;Pixel;Android',
        '',
        '',
        '',
    ],
    'Callout text': [
        '',
        '',
        'Buy my product now',
        '',
        '',
        '',
        'Buy my product now',
    ],
    'Original callout text': [
        '',
        '',
        'Buy my product now',
        '',
        '',
        '',
        'Buy my product now',
    ],
    'Sitelink description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Original sitelink description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Sitelink description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        'Calendar open',
        '',
    ],
    'Original sitelink description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        'Calendar open',
        '',
    ],
    'Sitelink link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Original sitelink link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Updates applied': [[], [], [], [], [], [], []],
})

_EXPECTED_DF_EMPTY = pd.DataFrame(
    {
        'Action': pd.Series([], dtype='object'),
        'Customer ID': pd.Series([], dtype='object'),
        'Campaign': pd.Series([], dtype='object'),
        'Ad group': pd.Series([], dtype='object'),
        'Asset type': pd.Series([], dtype='object'),
        'Status': pd.Series([], dtype='object'),
        'Structured snippet header': pd.Series([], dtype='object'),
        'Structured snippet values': pd.Series([], dtype='object'),
        'Original structured snippet values': pd.Series([], dtype='object'),
        'Callout text': pd.Series([], dtype='object'),
        'Original callout text': pd.Series([], dtype='object'),
        'Sitelink description 1': pd.Series([], dtype='object'),
        'Original sitelink description 1': pd.Series([], dtype='object'),
        'Sitelink description 2': pd.Series([], dtype='object'),
        'Original sitelink description 2': pd.Series([], dtype='object'),
        'Sitelink link text': pd.Series([], dtype='object'),
        'Original sitelink link text': pd.Series([], dtype='object'),
        'Updates applied': pd.Series([], dtype='object'),
    },
)

_EXPECTED_CSV_DATA_EMPTY = (
    'Action,Customer ID,Campaign,Ad group,Asset type,Status,Structured snippet'
    ' header,Structured snippet values,Original structured snippet'
    ' values,Callout text,Original callout text,Sitelink description 1,Original'
    ' sitelink description 1,Sitelink description 2,Original sitelink'
    ' description 2,Sitelink link text,Original sitelink link text,Updates'
    ' applied\n'
)

_EXPECTED_DF_AFTER_TRANSLATION = pd.DataFrame({
    'Action': ['Add', 'Add', 'Add', 'Add', 'Add', 'Add', 'Add'],
    'Customer ID': [
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
    ],
    'Campaign': [
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
        'Campaign 1',
    ],
    'Ad group': ['Ad group 1', 'Ad group 1', 'Ad group 1', '', '', '', ''],
    'Asset type': [
        'STRUCTURED_SNIPPET',
        'SITELINK',
        'CALLOUT',
        'STRUCTURED_SNIPPET',
        'SITELINK',
        'SITELINK',
        'CALLOUT',
    ],
    'Status': [
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
    ],
    'Structured snippet header': ['Brands', '', '', 'Brands', '', '', ''],
    'Structured snippet values': [
        'Google;Pixel;Android',
        '',
        '',
        'Google;Pixel;Android',
        '',
        '',
        '',
    ],
    'Original structured snippet values': [
        'Google;Pixel;Android',
        '',
        '',
        'Google;Pixel;Android',
        '',
        '',
        '',
    ],
    'Callout text': [
        '',
        '',
        'Kaufen Sie jetzt mein Produkt',
        '',
        '',
        '',
        'Kaufen Sie jetzt mein Produkt',
    ],
    'Original callout text': [
        '',
        '',
        'Buy my product now',
        '',
        '',
        '',
        'Buy my product now',
    ],
    'Sitelink description 1': [
        '',
        'Dies ist eine Beschreibung 1',
        '',
        '',
        'Dies ist eine Beschreibung 1',
        'Kalender öffnen',
        '',
    ],
    'Original sitelink description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Sitelink description 2': [
        '',
        'Dies ist eine Beschreibung 2',
        '',
        '',
        'Dies ist eine Beschreibung 2',
        'Kalender geöffnet',
        '',
    ],
    'Original sitelink description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        'Calendar open',
        '',
    ],
    'Sitelink link text': [
        '',
        'Dies ist ein Linktext',
        '',
        '',
        'Dies ist ein Linktext',
        'Kalender',
        '',
    ],
    'Original sitelink link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Updates applied': [[], [], [], [], [], [], []],
})

_EXPECTED_DF_AFTER_TRANSLATION_WITH_AD_GROUP_UPDATE = pd.DataFrame({
    'Action': ['Add', 'Add', 'Add', 'Add', 'Add', 'Add', 'Add'],
    'Customer ID': [
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
        'Enter customer ID',
    ],
    'Campaign': [
        'Campaign 1 (de)',
        'Campaign 1 (de)',
        'Campaign 1 (de)',
        'Campaign 1 (de)',
        'Campaign 1 (de)',
        'Campaign 1 (de)',
        'Campaign 1 (de)',
    ],
    'Ad group': [
        'Ad group 1 (de)',
        'Ad group 1 (de)',
        'Ad group 1 (de)',
        '',
        '',
        '',
        '',
    ],
    'Asset type': [
        'STRUCTURED_SNIPPET',
        'SITELINK',
        'CALLOUT',
        'STRUCTURED_SNIPPET',
        'SITELINK',
        'SITELINK',
        'CALLOUT',
    ],
    'Status': [
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
        'ENABLED',
    ],
    'Structured snippet header': ['Brands', '', '', 'Brands', '', '', ''],
    'Structured snippet values': [
        'Google;Pixel;Android',
        '',
        '',
        'Google;Pixel;Android',
        '',
        '',
        '',
    ],
    'Original structured snippet values': [
        'Google;Pixel;Android',
        '',
        '',
        'Google;Pixel;Android',
        '',
        '',
        '',
    ],
    'Callout text': [
        '',
        '',
        'Kaufen Sie jetzt mein Produkt',
        '',
        '',
        '',
        'Kaufen Sie jetzt mein Produkt',
    ],
    'Original callout text': [
        '',
        '',
        'Buy my product now',
        '',
        '',
        '',
        'Buy my product now',
    ],
    'Sitelink description 1': [
        '',
        'Dies ist eine Beschreibung 1',
        '',
        '',
        'Dies ist eine Beschreibung 1',
        'Kalender öffnen',
        '',
    ],
    'Original sitelink description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Sitelink description 2': [
        '',
        'Dies ist eine Beschreibung 2',
        '',
        '',
        'Dies ist eine Beschreibung 2',
        'Kalender geöffnet',
        '',
    ],
    'Original sitelink description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        'Calendar open',
        '',
    ],
    'Sitelink link text': [
        '',
        'Dies ist ein Linktext',
        '',
        '',
        'Dies ist ein Linktext',
        'Kalender',
        '',
    ],
    'Original sitelink link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Updates applied': [[], [], [], [], [], [], []],
})


class ExtensionsTest(parameterized.TestCase):

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
    extensions = extensions_lib.Extensions(google_ads_api_response)
    actual_df = extensions.df()

    pd.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False
    )

  @parameterized.named_parameters(
      {
          'testcase_name': 'response_with_extensions_data',
          'google_ads_api_response': _GOOGLE_ADS_RESPONSE,
          'expected_csv_data': _EXPECTED_CSV_DATA,
      },
      {
          'testcase_name': 'no_extensions_data',
          'google_ads_api_response': _EMPTY_GOOGLE_ADS_RESPONSE,
          'expected_csv_data': _EXPECTED_CSV_DATA_EMPTY,
      },
  )
  def test_csv_data(self, google_ads_api_response, expected_csv_data):
    extensions = extensions_lib.Extensions(google_ads_api_response)
    actual_csv_data = extensions.csv_data()

    self.assertEqual(actual_csv_data, expected_csv_data)

  @mock.patch.object(time, 'strftime', return_value='19700101-000000')
  def test_file_name(self, _):
    expected_file_name = 'extensions_19700101-000000'
    extensions = extensions_lib.Extensions(_GOOGLE_ADS_RESPONSE)
    actual_file_name = extensions.file_name()

    self.assertEqual(actual_file_name, expected_file_name)

  def test_add_update(self):
    expected_df = _EXPECTED_DF_AFTER_UPDATE

    extensions = extensions_lib.Extensions(_GOOGLE_ADS_RESPONSE)
    extensions.add_update(update='Translated')
    actual_df = extensions.df()

    pd.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False
    )

  def test_columns(self):
    expected_columns = [
        'Action',
        'Customer ID',
        'Campaign',
        'Ad group',
        'Asset type',
        'Status',
        'Structured snippet header',
        'Structured snippet values',
        'Original structured snippet values',
        'Callout text',
        'Original callout text',
        'Sitelink description 1',
        'Original sitelink description 1',
        'Sitelink description 2',
        'Original sitelink description 2',
        'Sitelink link text',
        'Original sitelink link text',
        'Updates applied',
    ]

    extensions = extensions_lib.Extensions(_GOOGLE_ADS_RESPONSE)
    actual_columns = extensions.columns()

    self.assertEqual(actual_columns, expected_columns)

  def test_size(self):
    expected_size = 7

    extensions = extensions_lib.Extensions(_GOOGLE_ADS_RESPONSE)
    actual_size = extensions.size()

    self.assertEqual(actual_size, expected_size)

  def test_add_campaign_and_ad_group_suffixes(self):
    expected_df = _EXPECTED_DF_AFTER_CAMPAIGN_AND_AD_GROUP_UPDATE

    extensions = extensions_lib.Extensions(_GOOGLE_ADS_RESPONSE)
    extensions.add_suffix(suffix='(es)')
    actual_df = extensions.df()

    pd.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False, check_dtype=False
    )

  def test_get_translation_frame(self):
    expected_df = pd.DataFrame({
        'source_term': [
            'Google;Pixel;Android',
            'This is a Description 1',
            'This is a Description 2',
            'This is a link text',
            'Buy my product now',
            'Open Calendar',
            'Calendar open',
            'Calendar',
        ],
        'target_terms': [
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ],
        'dataframe_locations': [
            [
                (0, 'Structured snippet values'),
                (3, 'Structured snippet values'),
            ],
            [(1, 'Sitelink description 1'), (4, 'Sitelink description 1')],
            [(1, 'Sitelink description 2'), (4, 'Sitelink description 2')],
            [(1, 'Sitelink link text'), (4, 'Sitelink link text')],
            [(2, 'Callout text'), (6, 'Callout text')],
            [(5, 'Sitelink description 1')],
            [(5, 'Sitelink description 2')],
            [(5, 'Sitelink link text')],
        ],
        'char_limit': [
            92,
            35,
            35,
            25,
            25,
            35,
            35,
            25,
        ],
    })

    extensions = extensions_lib.Extensions(_GOOGLE_ADS_RESPONSE)
    actual_df = extensions.get_translation_frame().df()

    pd.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False
    )

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
      self, update_ad_group_and_campaign_names, expected_df
  ):
    extensions = extensions_lib.Extensions(_GOOGLE_ADS_RESPONSE)
    translation_frame = extensions.get_translation_frame()

    translation_frame.add_translations(
        start_index=0,
        target_language_code='de',
        translations=[
            'Google;Pixel;Android',
            'Dies ist eine Beschreibung 1',
            'Dies ist eine Beschreibung 2',
            'Dies ist ein Linktext',
            'Kaufen Sie jetzt mein Produkt',
            'Kalender öffnen',
            'Kalender geöffnet',
            'Kalender',
        ],
    )

    extensions.apply_translations(
        target_language='de',
        translation_frame=translation_frame,
        update_ad_group_and_campaign_names=update_ad_group_and_campaign_names,
    )
    actual_df = extensions.df()

    pd.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False
    )

  def test_char_count(self):
    extensions = extensions_lib.Extensions(_GOOGLE_ADS_RESPONSE)

    expected_char_count = 222

    actual_char_count = extensions.char_count()

    self.assertEqual(actual_char_count, expected_char_count)


if __name__ == '__main__':
  absltest.main()

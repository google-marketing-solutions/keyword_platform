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
                    'finalUrls': ['https://www.google.com/gmail'],
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
        'fieldMask': 'fake_field_mask',
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
                    'finalUrls': ['https://www.google.com/gmail'],
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
                    'finalUrls': ['https://www.google.com/gmail'],
                    'sitelinkAsset': {
                        'linkText': 'Calendar',
                        'description1': 'Open Calendar',
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
        'fieldMask': 'fake_field_mask',
        'requestId': 'fake_request_id',
    }],
]

_EMPTY_GOOGLE_ADS_RESPONSE = [[{
    'results': [],
    'fieldMask': 'fake_field_mask',
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
    'Header': ['Brands', '', '', 'Brands', '', '', ''],
    'Snippet values': [
        'Google\nPixel\nAndroid',
        '',
        '',
        'Google\nPixel\nAndroid',
        '',
        '',
        '',
    ],
    'Original snippet values': [
        'Google\nPixel\nAndroid',
        '',
        '',
        'Google\nPixel\nAndroid',
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
    'Description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Original description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        '',
        '',
    ],
    'Original description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        '',
        '',
    ],
    'Link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Original link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Final URLs': [
        '',
        'https://www.google.com/gmail',
        '',
        '',
        'https://www.google.com/gmail',
        'https://www.google.com/gmail',
        '',
    ],
    'Updates applied': [[], [], [], [], [], [], []],
})

_EXPECTED_CSV_DATA = (
    'Action,Customer ID,Campaign,Ad group,Asset type,Status,Header,Snippet'
    ' values,Original snippet values,Callout text,Original callout'
    ' text,Description 1,Original description 1,Description 2,Original'
    ' description 2,Link text,Original link text,Final URLs,Updates'
    ' applied\nAdd,Enter customer ID,Campaign 1,Ad group'
    ' 1,STRUCTURED_SNIPPET,ENABLED,Brands,"Google\nPixel\nAndroid","Google\nPixel\nAndroid",,,,,,,,,,[]\nAdd,Enter'
    ' customer ID,Campaign 1,Ad group 1,SITELINK,ENABLED,,,,,,This is a'
    ' Description 1,This is a Description 1,This is a Description 2,This is a'
    ' Description 2,This is a link text,This is a link'
    ' text,https://www.google.com/gmail,[]\nAdd,Enter customer ID,Campaign 1,Ad'
    ' group 1,CALLOUT,ENABLED,,,,Buy my product now,Buy my product'
    ' now,,,,,,,,[]\nAdd,Enter customer ID,Campaign'
    ' 1,,STRUCTURED_SNIPPET,ENABLED,Brands,"Google\nPixel\nAndroid","Google\nPixel\nAndroid",,,,,,,,,,[]\nAdd,Enter'
    ' customer ID,Campaign 1,,SITELINK,ENABLED,,,,,,This is a Description'
    ' 1,This is a Description 1,This is a Description 2,This is a Description'
    ' 2,This is a link text,This is a link'
    ' text,https://www.google.com/gmail,[]\nAdd,Enter customer ID,Campaign'
    ' 1,,SITELINK,ENABLED,,,,,,Open Calendar,Open Calendar,,,'
    'Calendar,Calendar,https://www.google.com/gmail,[]\nAdd,Enter'
    ' customer ID,Campaign 1,,CALLOUT,ENABLED,,,,Buy my product now,Buy my'
    ' product now,,,,,,,,[]\n'
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
    'Header': ['Brands', '', '', 'Brands', '', '', ''],
    'Snippet values': [
        'Google\nPixel\nAndroid',
        '',
        '',
        'Google\nPixel\nAndroid',
        '',
        '',
        '',
    ],
    'Original snippet values': [
        'Google\nPixel\nAndroid',
        '',
        '',
        'Google\nPixel\nAndroid',
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
    'Description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Original description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        '',
        '',
    ],
    'Original description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        '',
        '',
    ],
    'Link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Original link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Final URLs': [
        '',
        'https://www.google.com/gmail',
        '',
        '',
        'https://www.google.com/gmail',
        'https://www.google.com/gmail',
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
    'Header': ['Brands', '', '', 'Brands', '', '', ''],
    'Snippet values': [
        'Google\nPixel\nAndroid',
        '',
        '',
        'Google\nPixel\nAndroid',
        '',
        '',
        '',
    ],
    'Original snippet values': [
        'Google\nPixel\nAndroid',
        '',
        '',
        'Google\nPixel\nAndroid',
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
    'Description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Original description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        '',
        '',
    ],
    'Original description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        '',
        '',
    ],
    'Link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Original link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Final URLs': [
        '',
        'https://www.google.com/gmail',
        '',
        '',
        'https://www.google.com/gmail',
        'https://www.google.com/gmail',
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
        'Header': pd.Series([], dtype='object'),
        'Snippet values': pd.Series([], dtype='object'),
        'Original snippet values': pd.Series([], dtype='object'),
        'Callout text': pd.Series([], dtype='object'),
        'Original callout text': pd.Series([], dtype='object'),
        'Description 1': pd.Series([], dtype='object'),
        'Original description 1': pd.Series([], dtype='object'),
        'Description 2': pd.Series([], dtype='object'),
        'Original description 2': pd.Series([], dtype='object'),
        'Link text': pd.Series([], dtype='object'),
        'Original link text': pd.Series([], dtype='object'),
        'Final URLs': pd.Series([], dtype='object'),
        'Updates applied': pd.Series([], dtype='object'),
    },
)

_EXPECTED_CSV_DATA_EMPTY = (
    'Action,Customer ID,Campaign,Ad group,Asset type,Status,Header,Snippet'
    ' values,Original snippet values,Callout text,Original callout'
    ' text,Description 1,Original description 1,Description 2,Original'
    ' description 2,Link text,Original link text,Final URLs,Updates applied\n'
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
    'Header': ['Brands', '', '', 'Brands', '', '', ''],
    'Snippet values': [
        'Google\nPixel\nAndroid',
        '',
        '',
        'Google\nPixel\nAndroid',
        '',
        '',
        '',
    ],
    'Original snippet values': [
        'Google\nPixel\nAndroid',
        '',
        '',
        'Google\nPixel\nAndroid',
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
    'Description 1': [
        '',
        'Dies ist eine Beschreibung 1',
        '',
        '',
        'Dies ist eine Beschreibung 1',
        'Kalender öffnen',
        '',
    ],
    'Original description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Description 2': [
        '',
        'Dies ist eine Beschreibung 2',
        '',
        '',
        'Dies ist eine Beschreibung 2',
        '',
        '',
    ],
    'Original description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        '',
        '',
    ],
    'Link text': [
        '',
        'Dies ist ein Linktext',
        '',
        '',
        'Dies ist ein Linktext',
        'Kalender',
        '',
    ],
    'Original link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Final URLs': [
        '',
        'https://www.google.com/gmail',
        '',
        '',
        'https://www.google.com/gmail',
        'https://www.google.com/gmail',
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
    'Header': ['Brands', '', '', 'Brands', '', '', ''],
    'Snippet values': [
        'Google\nPixel\nAndroid',
        '',
        '',
        'Google\nPixel\nAndroid',
        '',
        '',
        '',
    ],
    'Original snippet values': [
        'Google\nPixel\nAndroid',
        '',
        '',
        'Google\nPixel\nAndroid',
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
    'Description 1': [
        '',
        'Dies ist eine Beschreibung 1',
        '',
        '',
        'Dies ist eine Beschreibung 1',
        'Kalender öffnen',
        '',
    ],
    'Original description 1': [
        '',
        'This is a Description 1',
        '',
        '',
        'This is a Description 1',
        'Open Calendar',
        '',
    ],
    'Description 2': [
        '',
        'Dies ist eine Beschreibung 2',
        '',
        '',
        'Dies ist eine Beschreibung 2',
        '',
        '',
    ],
    'Original description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        '',
        '',
    ],
    'Link text': [
        '',
        'Dies ist ein Linktext',
        '',
        '',
        'Dies ist ein Linktext',
        'Kalender',
        '',
    ],
    'Original link text': [
        '',
        'This is a link text',
        '',
        '',
        'This is a link text',
        'Calendar',
        '',
    ],
    'Final URLs': [
        '',
        'https://www.google.com/gmail',
        '',
        '',
        'https://www.google.com/gmail',
        'https://www.google.com/gmail',
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
        'Header',
        'Snippet values',
        'Original snippet values',
        'Callout text',
        'Original callout text',
        'Description 1',
        'Original description 1',
        'Description 2',
        'Original description 2',
        'Link text',
        'Original link text',
        'Final URLs',
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
            'Google\nPixel\nAndroid',
            'This is a Description 1',
            'This is a Description 2',
            'This is a link text',
            'Buy my product now',
            'Open Calendar',
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
        ],
        'dataframe_locations': [
            [
                (0, 'Snippet values'),
                (3, 'Snippet values'),
            ],
            [(1, 'Description 1'), (4, 'Description 1')],
            [(1, 'Description 2'), (4, 'Description 2')],
            [(1, 'Link text'), (4, 'Link text')],
            [(2, 'Callout text'), (6, 'Callout text')],
            [(5, 'Description 1')],
            [(5, 'Link text')],
        ],
        'char_limit': [
            92,
            35,
            35,
            25,
            25,
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
            'Google\nPixel\nAndroid',
            'Dies ist eine Beschreibung 1',
            'Dies ist eine Beschreibung 2',
            'Dies ist ein Linktext',
            'Kaufen Sie jetzt mein Produkt',
            'Kalender öffnen',
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

    expected_char_count = 210

    actual_char_count = extensions.char_count()

    self.assertEqual(actual_char_count, expected_char_count)


if __name__ == '__main__':
  absltest.main()

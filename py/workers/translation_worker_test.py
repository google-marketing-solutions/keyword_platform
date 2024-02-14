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

"""Tests for the TranslationWorker class.
"""

from unittest import mock

import pandas as pd
import requests

from absl.testing import absltest
from common import api_utils
from common import cloud_translation_client as cloud_translation_client_lib
from data_models import ad_groups as ad_groups_lib
from data_models import ads as ads_lib
from data_models import campaigns as campaigns_lib
from data_models import extensions as extensions_lib
from data_models import google_ads_objects as google_ads_objects_lib
from data_models import keywords as keywords_lib
from data_models import settings as settings_lib
from workers import translation_worker as translation_worker_lib
from workers import worker_result


_KEYWORDS_GOOGLE_ADS_API_RESPONSE = [[{
    'results': [
        {
            'customer': {'resourceName': 'customers/123', 'id': '123'},
            'campaign': {
                'resourceName': 'customers/123/campaigns/456',
                'advertisingChannelType': 'SEARCH',
                'biddingStrategyType': 'TARGET_SPEND',
                'name': 'Gmail Test Campaign',
            },
            'adGroup': {
                'resourceName': 'customers/123/adGroups/789',
                'name': 'Ad group 1',
            },
            'adGroupCriterion': {
                'resourceName': 'customers/123/adGroupCriteria/789~1112',
                'keyword': {'matchType': 'BROAD', 'text': 'e mail'},
            },
            'keywordView': {
                'resourceName': 'customers/123/keywordViews/789~1112'
            },
        },
        {
            'customer': {'resourceName': 'customers/123', 'id': '123'},
            'campaign': {
                'resourceName': 'customers/123/campaigns/456',
                'advertisingChannelType': 'SEARCH',
                'biddingStrategyType': 'TARGET_SPEND',
                'name': 'Gmail Test Campaign',
            },
            'adGroup': {
                'resourceName': 'customers/123/adGroups/789',
                'name': 'Ad group 1',
            },
            'adGroupCriterion': {
                'resourceName': 'customers/123/adGroupCriteria/789~1314',
                'keyword': {'matchType': 'BROAD', 'text': 'fast'},
            },
            'keywordView': {
                'resourceName': 'customers/123/keywordViews/789~1314'
            },
        },
    ],
    'fieldMask': 'fake_field_mask',
    'requestId': 'fake_req_id',
}]]

_ADS_DATA_GOOGLE_ADS_API_RESPONSE = [[{
    'results': [
        {
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
                        'headlines': [
                            {
                                'text': 'Email Login',
                                'assetPerformanceLabel': 'PENDING',
                                'policySummaryInfo': {
                                    'reviewStatus': 'REVIEWED',
                                    'approvalStatus': 'APPROVED',
                                },
                            },
                            {
                                'text': 'Online Email',
                                'assetPerformanceLabel': 'PENDING',
                                'policySummaryInfo': {
                                    'reviewStatus': 'REVIEWED',
                                    'approvalStatus': 'APPROVED',
                                },
                            },
                            {
                                'text': 'Sign in',
                                'assetPerformanceLabel': 'PENDING',
                                'policySummaryInfo': {
                                    'reviewStatus': 'REVIEWED',
                                    'approvalStatus': 'APPROVED',
                                },
                            },
                        ],
                        'descriptions': [
                            {
                                'text': (
                                    'Email thats intuitive, efficient, and'
                                    ' useful'
                                ),
                                'assetPerformanceLabel': 'PENDING',
                                'policySummaryInfo': {
                                    'reviewStatus': 'REVIEWED',
                                    'approvalStatus': 'APPROVED',
                                },
                            },
                            {
                                'text': (
                                    '15 GB of storage, less spam, and mobile'
                                    ' access'
                                ),
                                'assetPerformanceLabel': 'PENDING',
                                'policySummaryInfo': {
                                    'reviewStatus': 'REVIEWED',
                                    'approvalStatus': 'APPROVED',
                                },
                            },
                        ],
                    },
                    'resourceName': 'customers/123/ads/1011',
                    'finalUrls': ['https://mail.google.com/'],
                },
            },
        },
        {
            'customer': {'resourceName': 'customers/123', 'id': '123'},
            'campaign': {
                'resourceName': 'customers/123/campaigns/1213',
                'name': 'Analytics Test Campaign',
            },
            'adGroup': {
                'resourceName': 'customers/123/adGroups/1415',
                'name': 'Ad group 1',
            },
            'adGroupAd': {
                'resourceName': 'customers/123/adGroupAds/1415~1617',
                'ad': {
                    'responsiveSearchAd': {
                        'headlines': [
                            {
                                'text': 'Official Website',
                                'assetPerformanceLabel': 'PENDING',
                                'policySummaryInfo': {
                                    'reviewStatus': 'REVIEWED',
                                    'approvalStatus': 'APPROVED',
                                },
                            },
                            {
                                'text': 'Official Site',
                                'assetPerformanceLabel': 'PENDING',
                                'policySummaryInfo': {
                                    'reviewStatus': 'REVIEWED',
                                    'approvalStatus': 'APPROVED',
                                },
                            },
                            {
                                'text': 'High Quality Products',
                                'assetPerformanceLabel': 'PENDING',
                                'policySummaryInfo': {
                                    'reviewStatus': 'REVIEWED',
                                    'approvalStatus': 'APPROVED',
                                },
                            },
                        ],
                        'descriptions': [
                            {
                                'text': 'Google Analytics',
                                'assetPerformanceLabel': 'PENDING',
                                'policySummaryInfo': {
                                    'reviewStatus': 'REVIEWED',
                                    'approvalStatus': 'APPROVED',
                                },
                            },
                            {
                                'text': 'Try Analytics today!',
                                'assetPerformanceLabel': 'PENDING',
                                'policySummaryInfo': {
                                    'reviewStatus': 'REVIEWED',
                                    'approvalStatus': 'APPROVED',
                                },
                            },
                        ],
                    },
                    'resourceName': 'customers/123/ads/1617',
                    'finalUrls': ['http://analytics.google.com'],
                },
            },
        },
    ],
    'fieldMask': 'fake_field_mask',
    'requestId': 'fake_request_id',
}]]


_CAMPAIGNS_GOOGLE_ADS_API_RESPONSE = [
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
        'fieldMask': 'fake_field_mask',
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
        'fieldMask': 'fake_field_mask',
        'requestId': 'fake_req_id',
    }],
]

_AD_GROUPS_GOOGLE_ADS_RESPONSE = [
    [{
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
        'fieldMask': 'fake_field_mask',
        'requestId': 'fake_request_id',
    }],
    [{
        'results': [
            {
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
                            'headlines': [
                                {
                                    'text': 'Email Login',
                                    'assetPerformanceLabels': 'PENDING',
                                    'policySummaryInfo': {
                                        'reviewStatus': 'REVIEWED',
                                        'approvalStatus': 'APPROVED',
                                    },
                                },
                                {
                                    'text': 'Online Email',
                                    'assetPerformanceLabels': 'PENDING',
                                    'policySummaryInfo': {
                                        'reviewStatus': 'REVIEWED',
                                        'approvalStatus': 'APPROVED',
                                    },
                                },
                                {
                                    'text': 'Sign in',
                                    'assetPerformanceLabels': 'PENDING',
                                    'policySummaryInfo': {
                                        'reviewStatus': 'REVIEWED',
                                        'approvalStatus': 'APPROVED',
                                    },
                                },
                            ],
                            'descriptions': [
                                {
                                    'text': (
                                        'Email that’s intuitive, efficient, and'
                                        ' useful'
                                    ),
                                    'assetPerformanceLabels': 'PENDING',
                                    'policySummaryInfo': {
                                        'reviewStatus': 'REVIEWED',
                                        'approvalStatus': 'APPROVED',
                                    },
                                },
                                {
                                    'text': (
                                        '15 GB of storage, less spam, and'
                                        ' mobile access'
                                    ),
                                    'assetPerformanceLabels': 'PENDING',
                                    'policySummaryInfo': {
                                        'reviewStatus': 'REVIEWED',
                                        'approvalStatus': 'APPROVED',
                                    },
                                },
                            ],
                        },
                        'resourceName': 'customers/123/ads/1011',
                        'finalUrls': ['https://mail.google.com/'],
                    },
                },
            },
            {
                'customer': {'resourceName': 'customers/123', 'id': '123'},
                'campaign': {
                    'resourceName': 'customers/123/campaigns/1213',
                    'name': 'Analytics Test Campaign',
                },
                'adGroup': {
                    'resourceName': 'customers/123/adGroups/1415',
                    'name': 'Ad group 1',
                },
                'adGroupAd': {
                    'resourceName': 'customers/123/adGroupAds/1415~1617',
                    'ad': {
                        'responsiveSearchAd': {
                            'headlines': [
                                {
                                    'text': 'Official Website',
                                    'assetPerformanceLabels': 'PENDING',
                                    'policySummaryInfo': {
                                        'reviewStatus': 'REVIEWED',
                                        'approvalStatus': 'APPROVED',
                                    },
                                },
                                {
                                    'text': 'Official Site',
                                    'assetPerformanceLabels': 'PENDING',
                                    'policySummaryInfo': {
                                        'reviewStatus': 'REVIEWED',
                                        'approvalStatus': 'APPROVED',
                                    },
                                },
                                {
                                    'text': 'High Quality Products',
                                    'assetPerformanceLabels': 'PENDING',
                                    'policySummaryInfo': {
                                        'reviewStatus': 'REVIEWED',
                                        'approvalStatus': 'APPROVED',
                                    },
                                },
                            ],
                            'descriptions': [
                                {
                                    'text': 'Google Analytics',
                                    'assetPerformanceLabels': 'PENDING',
                                    'policySummaryInfo': {
                                        'reviewStatus': 'REVIEWED',
                                        'approvalStatus': 'APPROVED',
                                    },
                                },
                                {
                                    'text': 'Try Analytics today!',
                                    'assetPerformanceLabels': 'PENDING',
                                    'policySummaryInfo': {
                                        'reviewStatus': 'REVIEWED',
                                        'approvalStatus': 'APPROVED',
                                    },
                                },
                            ],
                        },
                        'resourceName': 'customers/123/ads/1617',
                        'finalUrls': ['http://analytics.google.com'],
                    },
                },
            },
        ],
        'fieldMask': 'fake_field_mask',
        'requestId': 'fake_request_id',
    }],
]

_EXTENSIONS_GOOGLE_ADS_API_RESPONSE = [
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
        'fieldMask': 'fake_field_mask',
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
        'fieldMask': 'fake_field_mask',
        'requestId': 'fake_request_id',
    }],
]

_EXPECTED_EXTENSIONS_DF = pd.DataFrame({
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
        'Google\nPíxel\nAndroid',
        '',
        '',
        'Google\nPíxel\nAndroid',
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
        'Comprar mi producto ahora',
        '',
        '',
        '',
        'Comprar mi producto ahora',
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
        'Esta es una descripción 1',
        '',
        '',
        'Esta es una descripción 1',
        'Calendario abierto',
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
        'Esta es una descripción 2',
        '',
        '',
        'Esta es una descripción 2',
        'Calendario abierto',
        '',
    ],
    'Original description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        'Calendar open',
        '',
    ],
    'Link text': [
        '',
        'Este es un texto de enlace',
        '',
        '',
        'Este es un texto de enlace',
        'Calendario',
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

_EXPECTED_EXTENSIONS_DF_WHEN_TRANSLATION_SKIPPED = pd.DataFrame({
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
        'Calendar open',
        '',
    ],
    'Original description 2': [
        '',
        'This is a Description 2',
        '',
        '',
        'This is a Description 2',
        'Calendar open',
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

_EXPECTED_KEYWORDS_DF = pd.DataFrame(
    {
        'Action': ['Add', 'Add'],
        'Customer ID': [
            'Enter customer ID',
            'Enter customer ID',
        ],
        'Campaign': [
            'Gmail Test Campaign (es)',
            'Gmail Test Campaign (es)',
        ],
        'Ad group': ['Ad group 1 (es)', 'Ad group 1 (es)'],
        'Keyword': [
            'correo electrónico',
            'rápido',
        ],
        'Original Keyword': [
            'e mail',
            'fast',
        ],
        'Match Type': ['BROAD', 'BROAD'],
        'Keyword status': ['Paused', 'Paused'],
        'Labels': [
            'Keyword Translator',
            'Keyword Translator',
        ],
        'Updates applied': [[], []],
    },
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
        'Labels': ['Keyword Translator', 'Keyword Translator'],
        'Updates applied': [[], []],
    },
)

_EXPECTED_ADS_DF_WHEN_TRANSLATION_SKIPPED = pd.DataFrame(
    {
        'Action': ['Add', 'Add'],
        'Customer ID': ['Enter customer ID', 'Enter customer ID'],
        'Ad status': ['Paused', 'Paused'],
        'Campaign': [
            'Gmail Test Campaign',
            'Analytics Test Campaign',
        ],
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
        'Labels': ['Keyword Translator', 'Keyword Translator'],
        'Updates applied': [[], []],
    },
)

_EXPECTED_CAMPAIGNS_DF = pd.DataFrame(
    {
        'Action': ['Add', 'Add', 'Add'],
        'Campaign status': ['Paused', 'Paused', 'Paused'],
        'Customer ID': [
            'Enter customer ID',
            'Enter customer ID',
            'Enter customer ID',
        ],
        'Campaign': [
            'Test Campaign 0 (es)',
            'Test Campaign 1 (es)',
            'Test Campaign 2 (es)',
        ],
        'Campaign type': ['Search', 'Search', 'Search'],
        'Bid strategy type': [
            'Target spend',
            'Target spend',
            'Maximize conversions',
        ],
        'Budget': ['1.00', '1.00', '1.00'],
        'Labels': [
            'Keyword Translator',
            'Keyword Translator',
            'Keyword Translator',
        ],
        'Updates applied': [[], [], []],
    },
)

_EXPECTED_AD_GROUPS_DF = pd.DataFrame(
    {
        'Action': ['Add', 'Add', 'Add'],
        'Customer ID': [
            'Enter customer ID',
            'Enter customer ID',
            'Enter customer ID',
        ],
        'Campaign': [
            'Gmail Test Campaign (es)',
            'Gmail Test Campaign (es)',
            'Analytics Test Campaign (es)',
        ],
        'Ad group': ['Ad group 1 (es)', 'Ad group 1 (es)', 'Ad group 1 (es)'],
        'Status': ['Paused', 'Paused', 'Paused'],
        'Labels': [
            'Keyword Translator',
            'Keyword Translator',
            'Keyword Translator',
        ],
        'Updates applied': [[], [], []],
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
    gcp_region = 'fake_gcp_region'
    api_version = 3

    cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=credentials,
            gcp_project_name=gcp_project_name,
            gcp_region=gcp_region,
            api_version=api_version,
        )
    )

    mock_send_api_request.side_effect = [
        {
            'translations': [
                {'translatedText': 'correo electrónico'},
                {'translatedText': 'rápido'},
            ]
        },
        {
            'translations': [
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
            ]
        },
        {
            'translations': [
                {'translatedText': 'Google\nPíxel\nAndroid'},
                {'translatedText': 'Esta es una descripción 1'},
                {'translatedText': 'Esta es una descripción 2'},
                {'translatedText': 'Este es un texto de enlace'},
                {'translatedText': 'Comprar mi producto ahora'},
                {'translatedText': 'Calendario abierto'},
                {'translatedText': 'Calendario abierto'},
                {'translatedText': 'Calendario'},
            ]
        },
    ]

    mock_refresh_access_token.return_value = 'fake_access_token'

    # Arranges settings
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        translate_ads=True,
        translate_keywords=True,
        translate_extensions=True,
    )

    # Arranges google ads objects
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        ads=ads_lib.Ads(_ADS_DATA_GOOGLE_ADS_API_RESPONSE),
        keywords=keywords_lib.Keywords(_KEYWORDS_GOOGLE_ADS_API_RESPONSE),
        campaigns=campaigns_lib.Campaigns(_CAMPAIGNS_GOOGLE_ADS_API_RESPONSE),
        ad_groups=ad_groups_lib.AdGroups(_AD_GROUPS_GOOGLE_ADS_RESPONSE),
        extensions=extensions_lib.Extensions(
            _EXTENSIONS_GOOGLE_ADS_API_RESPONSE
        ),
    )

    # Arranges translation worker
    translation_worker = translation_worker_lib.TranslationWorker(
        cloud_translation_client=cloud_translation_client, vertex_client=None
    )

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

    # Asserts extensions translated
    actual_extensions_df = google_ads_objects.extensions.df()

    pd.testing.assert_frame_equal(
        actual_extensions_df, _EXPECTED_EXTENSIONS_DF, check_index_type=False
    )

    # Assert that suffixes were added to campaign and ad group names
    actual_campaigns_df = google_ads_objects.campaigns.df()

    pd.testing.assert_frame_equal(
        actual_campaigns_df, _EXPECTED_CAMPAIGNS_DF, check_index_type=False)

    actual_ad_groups_df = google_ads_objects.ad_groups.df()

    pd.testing.assert_frame_equal(
        actual_ad_groups_df, _EXPECTED_AD_GROUPS_DF, check_index_type=False)

  def test_execute_empty_objects_returns_failure(self):
    # Arranges mock translation API
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    gcp_region = 'fake_gcp_region'
    api_version = 3

    cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=credentials,
            gcp_project_name=gcp_project_name,
            gcp_region=gcp_region,
            api_version=api_version,
        )
    )

    # Arranges settings
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
    )

    # Arranges google ads objects
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects()

    # Arranges translation worker
    translation_worker = translation_worker_lib.TranslationWorker(
        cloud_translation_client=cloud_translation_client, vertex_client=None
    )

    # Act
    result = translation_worker.execute(
        settings=settings, google_ads_objects=google_ads_objects)

    # Asserts result
    self.assertEqual(worker_result.Status.FAILURE, result.status)

  @mock.patch.object(api_utils, 'refresh_access_token', autospec=True)
  @mock.patch.object(api_utils, 'send_api_request', autospec=True)
  def test_execute_sets_warning_msg_when_exception_cause(
      self, mock_send_api_request, mock_refresh_access_token
  ):
    # Arranges mock translation API
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    gcp_region = 'fake_gcp_region'
    api_version = 3

    cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=credentials,
            gcp_project_name=gcp_project_name,
            gcp_region=gcp_region,
            api_version=api_version,
        )
    )

    mock_send_api_request.side_effect = [
        {
            'translations': [
                {'translatedText': 'correo electrónico'},
                {'translatedText': 'rápido'},
            ]
        },
        requests.exceptions.HTTPError(),
    ]

    mock_refresh_access_token.return_value = 'fake_access_token'

    # Arranges settings
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
    )

    # Arranges google ads objects
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        ads=ads_lib.Ads(_ADS_DATA_GOOGLE_ADS_API_RESPONSE),
        keywords=keywords_lib.Keywords(_KEYWORDS_GOOGLE_ADS_API_RESPONSE),
        campaigns=campaigns_lib.Campaigns(_CAMPAIGNS_GOOGLE_ADS_API_RESPONSE),
        ad_groups=ad_groups_lib.AdGroups(_AD_GROUPS_GOOGLE_ADS_RESPONSE),
        extensions=extensions_lib.Extensions(
            _EXTENSIONS_GOOGLE_ADS_API_RESPONSE
        ),
    )

    # Arranges translation worker
    translation_worker = translation_worker_lib.TranslationWorker(
        cloud_translation_client=cloud_translation_client, vertex_client=None
    )

    expected_warning_msg = (
        'Encountered an error during ad translation. Check the output files '
        ' before uploading. A developer can check logs for more details.'
    )

    # Act
    result = translation_worker.execute(
        settings=settings, google_ads_objects=google_ads_objects
    )

    # Asserts result
    self.assertEqual(expected_warning_msg, result.warning_msg)

  @mock.patch.object(api_utils, 'refresh_access_token', autospec=True)
  @mock.patch.object(api_utils, 'send_api_request', autospec=True)
  def test_execute_does_not_translate_ads_when_translate_ads_is_false(
      self, mock_send_api_request, mock_refresh_access_token
  ):
    # Arranges mock translation API
    credentials = {
        'client_id': 'fake_client_id',
        'client_secret': 'fake_client_secret',
        'refresh_token': 'fake_refresh_token',
    }
    gcp_project_name = 'fake_gcp_project'
    gcp_region = 'fake_gcp_region'
    api_version = 3

    cloud_translation_client = (
        cloud_translation_client_lib.CloudTranslationClient(
            credentials=credentials,
            gcp_project_name=gcp_project_name,
            gcp_region=gcp_region,
            api_version=api_version,
        )
    )

    mock_send_api_request.side_effect = [{
        'translations': [
            {'translatedText': 'correo electrónico'},
            {'translatedText': 'rápido'},
        ]
    }]

    mock_refresh_access_token.return_value = 'fake_access_token'

    # Arranges settings
    settings = settings_lib.Settings(
        source_language_code='en',
        target_language_codes=['es'],
        translate_ads=False,
        translate_extensions=False,
    )

    # Arranges google ads objects
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        ads=ads_lib.Ads(_ADS_DATA_GOOGLE_ADS_API_RESPONSE),
        keywords=keywords_lib.Keywords(_KEYWORDS_GOOGLE_ADS_API_RESPONSE),
        campaigns=campaigns_lib.Campaigns(_CAMPAIGNS_GOOGLE_ADS_API_RESPONSE),
        ad_groups=ad_groups_lib.AdGroups(_AD_GROUPS_GOOGLE_ADS_RESPONSE),
        extensions=extensions_lib.Extensions(
            _EXTENSIONS_GOOGLE_ADS_API_RESPONSE
        ),
    )

    # Arranges translation worker
    translation_worker = translation_worker_lib.TranslationWorker(
        cloud_translation_client=cloud_translation_client, vertex_client=None
    )

    # Act
    translation_worker.execute(
        settings=settings, google_ads_objects=google_ads_objects
    )

    # Asserts ads not translated
    actual_ads_df = google_ads_objects.ads.df()

    pd.testing.assert_frame_equal(
        actual_ads_df, _EXPECTED_ADS_DF_WHEN_TRANSLATION_SKIPPED,
        check_index_type=False)

    # Asserts extensions not translated

    actual_extensions_df = google_ads_objects.extensions.df()

    pd.testing.assert_frame_equal(
        actual_extensions_df,
        _EXPECTED_EXTENSIONS_DF_WHEN_TRANSLATION_SKIPPED,
        check_index_type=False,
    )

if __name__ == '__main__':
  absltest.main()

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

"""Tests for google_ads_client."""

from typing import Any

import requests
import requests_mock

from common import google_ads_client
from absl.testing import absltest
from absl.testing import parameterized

_FAKE_VALID_CREDENTIALS = {
    'developer_token': 'developer_token',
    'client_id': 'client_id',
    'client_secret': 'client_secret',
    'refresh_token': 'refresh_token',
    'login_customer_id': 'login_customer_id',
}

_FAKE_ACCESS_TOKEN = 'access_token'
_FAKE_INVALID_CREDENTIALS = {
    'developer_token': 'developer_token',
    'client_id': 'client_id',
    'client_secret': 'client_secret',
    'refresh_token': 'refresh_token',
}

_FAKE_RESPONSE = [
    {
        'results': [
            {
                'customer': {
                    'resourceName': 'customers/1234567890',
                    'id': '1234567890',
                }
            }
        ]
    }
]

_FAKE_REFRESH_ACCESS_TOKEN_RESPONSE = {
    'access_token': _FAKE_ACCESS_TOKEN,
    'expires_in': 3920,
    'scope': 'https://www.googleapis.com/auth/drive.metadata.readonly',
    'token_type': 'Bearer',
}

_FAKE_HEADERS = {
    'authorization': f'Bearer {_FAKE_ACCESS_TOKEN}',
    'developer-token': 'developer_token',
    'login-customer-id': 'login_customer_id',
}

_FAKE_CUSTOMER_ID = '1234567890'
_FAKE_CAMPAIGN_IDS = [1]

_TEST_SEARCH_STREAM_URL = 'https://googleads.googleapis.com/v13/customers/1234567890/googleAds:searchStream'
_TEST_OAUTH2_TOKEN_URL = 'https://www.googleapis.com/oauth2/v3/token'


def _request_record_asdict(request: Any) -> dict[str, Any]:
  request_dict = dict(method=request.method, url=request.url)
  if request.text:
    request_dict.update(dict(json=request.json()))
  if request.stream:
    request_dict.update(dict(stream=request.stream))
  return request_dict


def _expected_request_from_query(query: str) -> dict[str, Any]:
  return dict(
      method='POST',
      url=_TEST_SEARCH_STREAM_URL,
      json={'query': ' '.join(query.split())},
  )


class GoogleAdsClientTest(parameterized.TestCase):

  def setUp(self):
    super().setUp()
    self.client = google_ads_client.GoogleAdsClient(_FAKE_VALID_CREDENTIALS)
    self.client.access_token = _FAKE_ACCESS_TOKEN

  @requests_mock.Mocker()
  def test_get_accounts(self, mock_requests):
    mock_response = _FAKE_RESPONSE
    mock_requests.post(
        requests_mock.ANY, json=mock_response, headers=_FAKE_HEADERS
    )
    query = """
        SELECT
          customer_client.descriptive_name,
          customer_client.id
        FROM
          customer_client
        WHERE
          customer_client.manager = False
          AND customer_client.status = 'ENABLED'
        """
    expected_request = _expected_request_from_query(query)
    self.client.get_accounts(_FAKE_CUSTOMER_ID)

    self.assertEqual(
        _request_record_asdict(mock_requests.last_request),
        expected_request,
    )

  @requests_mock.Mocker()
  def test_get_campaigns(self, mock_requests):
    mock_response = _FAKE_RESPONSE
    mock_requests.post(
        requests_mock.ANY, json=mock_response, headers=_FAKE_HEADERS
    )
    query = """
        SELECT
          campaign.name,
          campaign.id,
          campaign.advertising_channel_type,
          campaign.bidding_strategy_type
        FROM
          campaign
        WHERE
          campaign.status = 'ENABLED'
          AND campaign.advertising_channel_type = 'SEARCH'
        """
    expected_request = _expected_request_from_query(query)
    self.client.get_campaigns_for_account(_FAKE_CUSTOMER_ID)

    self.assertEqual(
        _request_record_asdict(mock_requests.last_request),
        expected_request,
    )

  @parameterized.named_parameters(
      {
          'testcase_name': 'keywords_data_for_campaigns',
          'params': {
              'customer_id': _FAKE_CUSTOMER_ID,
              'campaign_ids': _FAKE_CAMPAIGN_IDS,
              'kw_statuses': ['PAUSED'],
          },
          'expected_query': """
              SELECT
                customer.id,
                campaign.name,
                campaign.advertising_channel_type,
                campaign.bidding_strategy_type,
                ad_group.name,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type
            FROM keyword_view
            WHERE
                campaign.status in (
                    'ENABLED')
                AND ad_group.status in (
                    'ENABLED')
                AND ad_group_criterion.status in (
                    'PAUSED')
                AND campaign.id in ('1')
              """,
      },
      {
          'testcase_name': (
              'keywords_data_for_campaigns_called_without_campaigns'
          ),
          'params': {
              'customer_id': _FAKE_CUSTOMER_ID,
          },
          'expected_query': """
              SELECT
                customer.id,
                campaign.name,
                campaign.advertising_channel_type,
                campaign.bidding_strategy_type,
                ad_group.name,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type
              FROM keyword_view
              WHERE
                campaign.status in (
                    'ENABLED')
                AND ad_group.status in (
                    'ENABLED')
                AND ad_group_criterion.status in (
                    'ENABLED')
              """,
      },
  )
  @requests_mock.Mocker()
  def test_get_keywords_data_for_campaigns(
      self, mock_requests, expected_query, params
  ):
    mock_response = _FAKE_RESPONSE
    mock_requests.post(
        requests_mock.ANY, json=mock_response, headers=_FAKE_HEADERS
    )
    expected_request = _expected_request_from_query(expected_query)
    self.client.get_keywords_data_for_campaigns(**params)

    self.assertEqual(
        _request_record_asdict(mock_requests.last_request),
        expected_request,
    )

  @parameterized.named_parameters(
      {
          'testcase_name': 'ads_data_for_campaigns',
          'params': {
              'customer_id': _FAKE_CUSTOMER_ID,
              'campaign_ids': _FAKE_CAMPAIGN_IDS,
          },
          'expected_query': """
              SELECT
                customer.id,
                campaign.name,
                ad_group.name,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.final_urls
              FROM ad_group_ad
              WHERE
                ad_group_ad.ad.type = RESPONSIVE_SEARCH_AD
                AND campaign.status in (
                    'ENABLED')
                AND ad_group.status in (
                    'ENABLED')
                AND ad_group_ad.status in (
                    'ENABLED')
                AND campaign.id in ('1')
              """,
      },
      {
          'testcase_name': 'ads_data_for_campaigns_called_wo_campaigns',
          'params': {
              'customer_id': _FAKE_CUSTOMER_ID,
              'ad_statuses': ['PAUSED'],
          },
          'expected_query': """
              SELECT
                customer.id,
                campaign.name,
                ad_group.name,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.final_urls
              FROM ad_group_ad
              WHERE
                ad_group_ad.ad.type = RESPONSIVE_SEARCH_AD
                AND campaign.status in (
                    'ENABLED')
                AND ad_group.status in (
                    'ENABLED')
                AND ad_group_ad.status in (
                    'PAUSED')
              """,
      },
  )
  @requests_mock.Mocker()
  def test_get_ads_data_for_campaigns(
      self, mock_requests, expected_query, params
  ):
    mock_response = _FAKE_RESPONSE
    mock_requests.post(
        requests_mock.ANY, json=mock_response, headers=_FAKE_HEADERS
    )
    expected_request = _expected_request_from_query(expected_query)
    self.client.get_ads_data_for_campaigns(**params)

    self.assertEqual(
        _request_record_asdict(mock_requests.last_request),
        expected_request,
    )

  @requests_mock.Mocker()
  def test_get_active_keywords_for_account(self, mock_requests):
    mock_response = _FAKE_RESPONSE
    mock_requests.post(
        requests_mock.ANY, json=mock_response, headers=_FAKE_HEADERS
    )
    query = """
        SELECT
          ad_group_criterion.keyword.text
        FROM ad_group_criterion
        WHERE
          campaign.status = 'ENABLED'
          AND ad_group.status = 'ENABLED'
          AND ad_group_criterion.type = 'KEYWORD'
        """
    expected_request = _expected_request_from_query(query)
    self.client.get_active_keywords_for_account(_FAKE_CUSTOMER_ID)

    self.assertEqual(
        _request_record_asdict(mock_requests.last_request),
        expected_request,
    )

  def test_invalid_credentials(self):
    with self.assertRaises(AttributeError):
      google_ads_client.GoogleAdsClient(_FAKE_INVALID_CREDENTIALS)

  @requests_mock.Mocker()
  def test_access_token_refreshed_if_not_supplied(self, mock_requests):
    self.client.access_token = None
    mock_requests.post(
        _TEST_SEARCH_STREAM_URL,
        json=_FAKE_RESPONSE,
    )
    token_request = mock_requests.post(
        _TEST_OAUTH2_TOKEN_URL,
        json=_FAKE_REFRESH_ACCESS_TOKEN_RESPONSE,
    )

    self.client.get_accounts(_FAKE_CUSTOMER_ID)

    params = {
        'grant_type': 'refresh_token',
        'client_id': _FAKE_INVALID_CREDENTIALS['client_id'],
        'client_secret': _FAKE_INVALID_CREDENTIALS['client_secret'],
        'refresh_token': _FAKE_INVALID_CREDENTIALS['refresh_token'],
    }
    expected_url = f'{_TEST_OAUTH2_TOKEN_URL}?'
    for item in params:
      expected_url += f'{item}={params[item]}&'
    expected_url = expected_url.rstrip('&')

    expected_request = dict(
        method='POST',
        url=expected_url,
    )

    self.assertEqual(token_request.call_count, 1)
    self.assertEqual(
        _request_record_asdict(token_request.last_request),
        expected_request,
    )

  @requests_mock.Mocker()
  def test_not_success_http_code_in_response_raises_error(self, mock_requests):
    mock_requests.register_uri(
        'POST',
        requests_mock.ANY,
        status_code=400,
        json={'error': 'Bad Request'},
    )

    with self.assertRaises(requests.exceptions.HTTPError):
      self.client.get_accounts(_FAKE_CUSTOMER_ID)

  @requests_mock.Mocker()
  def test_get_extensions_for_campaigns(self, mock_requests):
    mock_response = _FAKE_RESPONSE
    mock_requests.post(
        requests_mock.ANY, json=mock_response, headers=_FAKE_HEADERS
    )
    query_ad_group = """
        SELECT
            campaign.name,
            asset.type,
            asset.structured_snippet_asset.header,
            asset.structured_snippet_asset.values,
            asset.callout_asset.callout_text,
            asset.sitelink_asset.description1,
            asset.sitelink_asset.description2,
            asset.sitelink_asset.link_text,
            ad_group_asset.status,
            ad_group.name
        FROM
          ad_group_asset
        WHERE
          ad_group_asset.field_type IN (
              'STRUCTURED_SNIPPET', 'SITELINK', 'CALLOUT')
        """
    query_campaign = """
        SELECT
            campaign.name,
            asset.type,
            asset.structured_snippet_asset.header,
            asset.structured_snippet_asset.values,
            asset.callout_asset.callout_text,
            asset.sitelink_asset.description1,
            asset.sitelink_asset.description2,
            asset.sitelink_asset.link_text,
            campaign_asset.status
        FROM
          campaign_asset
        WHERE
          campaign_asset.field_type IN (
              'STRUCTURED_SNIPPET', 'SITELINK', 'CALLOUT')
        """
    expected_request_ad_group = _expected_request_from_query(query_ad_group)
    expected_request_campaign = _expected_request_from_query(query_campaign)
    self.client.get_extensions_for_campaigns(_FAKE_CUSTOMER_ID)

    self.assertEqual(
        _request_record_asdict(mock_requests.request_history[0]),
        expected_request_ad_group,
    )
    self.assertEqual(
        _request_record_asdict(mock_requests.request_history[1]),
        expected_request_campaign,
    )


if __name__ == '__main__':
  absltest.main()

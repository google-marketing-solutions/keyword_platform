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

"""The Google Ads client."""

from typing import Any, Literal, Optional, Union
from common import api_utils

GOOGLE_ADS_API_BASE_URL = 'https://googleads.googleapis.com'

SEARCH_URL = (
    GOOGLE_ADS_API_BASE_URL
    + '/{api_version}/customers/{customer_id}/googleAds:searchStream'
)

_API_VERSION = '15'

_CREDENTIAL_REQUIRED_KEYS = (
    'developer_token',
    'client_id',
    'client_secret',
    'refresh_token',
    'login_customer_id',
)


class GoogleAdsClient:
  """A client for getting Google Ads data via the Google Ads REST API.

  The credentials need to be provided as a dictionary see details below:

  Sample usage:
    credentials = {
      'developer_token': <developer_token>,
      'client_id': <client_id>,
      'client_secret': <client_secret>,
      'refresh_token': <refresh_token>,
      'login_customer_id': <login_customer_id>,
    }
    customer_id = '1234567890'
    google_ads_client = GoogleAdsClient(credentials)
    response = google_ads_client.get_keywords_data_for_campaigns(customer_id)

  Attributes:
    api_version: The Google Ads API Version.
    credentials: The Google Ads oAuth2.0 credentials.
    access_token: The Google Ads API access token.
  """

  def __init__(
      self, credentials: dict[str, str], api_version: str = _API_VERSION
  ) -> None:
    """Instantiates the Google Ads client.

    Args:
      credentials: The Google Ads credentials as dict.
      api_version: The Google Ads API Version.
    """
    self.api_version = f'v{api_version}'
    self.credentials = credentials
    # The access_token be lazily loaded and cached when the API is called to
    # ensure token is fresh and won't be retrieved repeatedly.
    self.access_token = None
    api_utils.validate_credentials(self.credentials, _CREDENTIAL_REQUIRED_KEYS)

  def _get_http_header(self) -> dict[str, str]:
    """Get the Authorization HTTP header.

    Returns:
      The authorization HTTP header.
    """
    if not self.access_token:
      self.access_token = api_utils.refresh_access_token(self.credentials)
    return {
        'authorization': f'Bearer {self.access_token}',
        'developer-token': self.credentials['developer_token'],
        'login-customer-id': str(self.credentials['login_customer_id']),
    }

  def get_accounts(self, mcc_id: str) -> list[Any]:
    """Gets the all accessible accounts under the MCC.

    Args:
      mcc_id: The Google Ads MCC id.

    Returns:
      The API response object containing a list of account descriptive names and
      ids. .
    """
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
    payload = {'query': ' '.join(query.split())}
    url = SEARCH_URL.format(api_version=self.api_version, customer_id=mcc_id)
    return api_utils.send_api_request(url, payload, self._get_http_header())

  def get_campaigns_for_account(
      self,
      customer_id: str,
      campaign_ids: Optional[list[Union[int, str]]] = None,
  ) -> list[Any]:
    """Gets the all accessible campaigns under the accounts.

    Args:
      customer_id: The Google Ads account id.
      campaign_ids: A list of Google Ads campaign ids.

    Returns:
      The API response object containing a list of campaign ids and names.
    """
    query = """
        SELECT
          campaign.name,
          campaign.id,
          campaign.advertising_channel_type,
          campaign.bidding_strategy_type
        FROM
          campaign
        WHERE
          campaign.status IN ('ENABLED', 'PAUSED')
          AND campaign.advertising_channel_type = 'SEARCH'
        """
    if campaign_ids:
      campaign_ids_str = ', '.join([f"'{elem}'" for elem in campaign_ids])
      query += f' AND campaign.id in ({campaign_ids_str})'
    payload = {'query': ' '.join(query.split())}
    url = SEARCH_URL.format(
        api_version=self.api_version, customer_id=customer_id
    )
    return api_utils.send_api_request(url, payload, self._get_http_header())

  def get_keywords_data_for_campaigns(
      self,
      customer_id: str,
      campaign_ids: Optional[list[Union[int, str]]] = None,
      kw_statuses: Optional[list[str]] = None,
      campaign_statuses: Optional[list[str]] = None,
      ad_group_statuses: Optional[list[str]] = None,
  ) -> list[Any]:
    """Used to get keywords including customer, campaign and ad group info.

    Args:
      customer_id: The Google Ads customer id.
      campaign_ids: A list of Google Ads campaign ids.
      kw_statuses: A list of Google Ads keyword statuses.
      campaign_statuses: A list of Google Ads campaign statuses.
      ad_group_statuses: A list of Google Ads ad group statuses.

    Returns:
      The API response object.
    """
    kw_statuses = kw_statuses or ['ENABLED']
    campaign_statuses = campaign_statuses or ['ENABLED', 'PAUSED']
    ad_group_statuses = ad_group_statuses or ['ENABLED']
    query = f"""
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
              {', '.join([f"'{elem}'" for elem in campaign_statuses])})
          AND ad_group.status in (
              {', '.join([f"'{elem}'" for elem in ad_group_statuses])})
          AND ad_group_criterion.status in (
              {', '.join([f"'{elem}'" for elem in kw_statuses])})
        """
    if campaign_ids:
      campaign_ids_str = ', '.join([f"'{elem}'" for elem in campaign_ids])
      query += f'AND campaign.id in ({campaign_ids_str})'
    payload = {'query': ' '.join(query.split())}
    url = SEARCH_URL.format(
        api_version=self.api_version, customer_id=customer_id
    )
    return api_utils.send_api_request(url, payload, self._get_http_header())

  def get_ads_data_for_campaigns(
      self,
      customer_id: str,
      campaign_ids: Optional[list[Union[int, str]]] = None,
      campaign_statuses: Optional[list[str]] = None,
      ad_group_statuses: Optional[list[str]] = None,
      ad_statuses: Optional[list[str]] = None,
  ) -> list[Any]:
    """Used to get keywords including customer, campaign and ad group info.

    Args:
      customer_id: The Google Ads customer id.
      campaign_ids: A list of Google Ads campaign ids.
      campaign_statuses: A list of Google Ads campaign statuses.
      ad_group_statuses: A list of Google Ads ad group statuses.
      ad_statuses: A list of Google Ads ad statuses.

    Returns:
      The API response object.
    """
    campaign_statuses = campaign_statuses or ['ENABLED', 'PAUSED']
    ad_group_statuses = ad_group_statuses or ['ENABLED']
    ad_statuses = ad_statuses or ['ENABLED']
    query = f"""
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
              {", ".join([f"'{elem}'" for elem in campaign_statuses])})
          AND ad_group.status in (
              {", ".join([f"'{elem}'" for elem in ad_group_statuses])})
          AND ad_group_ad.status in (
              {", ".join([f"'{elem}'" for elem in ad_statuses])})
        """
    if campaign_ids:
      campaign_ids_str = ', '.join([f"'{elem}'" for elem in campaign_ids])
      query += f'AND campaign.id in ({campaign_ids_str})'
    payload = {'query': ' '.join(query.split())}
    url = SEARCH_URL.format(
        api_version=self.api_version, customer_id=customer_id
    )
    return api_utils.send_api_request(url, payload, self._get_http_header())

  def get_active_keywords_for_account(self, customer_id: str) -> list[Any]:
    """Used to get keywords for campaigns for deduplication.

    Args:
      customer_id: The Google Ads account id.

    Returns:
      The API response object.
    """
    query = """
        SELECT
          ad_group_criterion.keyword.text
        FROM ad_group_criterion
        WHERE
          campaign.status IN ('ENABLED', 'PAUSED')
          AND ad_group.status = 'ENABLED'
          AND ad_group_criterion.type = 'KEYWORD'
        """
    payload = {'query': ' '.join(query.split())}
    url = SEARCH_URL.format(
        api_version=self.api_version, customer_id=customer_id
    )
    return api_utils.send_api_request(url, payload, self._get_http_header())

  def get_extensions_for_campaigns(
      self,
      customer_id: str,
      campaign_ids: Optional[list[Union[int, str]]] = None,
  ) -> list[Any]:
    """Gets extension assets for campaigns and ad groups.

    Gets existing structured snippets, callouts and sitelink extensions.

    Args:
      customer_id: The Google Ads customer id.
      campaign_ids: A list of Google Ads campaign ids.

    Returns:
      The API response object containing a list of extensions.
    """
    results = []
    for level in ['ad_group', 'campaign']:
      results.extend(
          self._get_extensions_for_campaigns_by_level(
              customer_id, level, campaign_ids
          )
      )
    return results

  def _get_extensions_for_campaigns_by_level(
      self,
      customer_id: str,
      level: Literal['ad_group', 'campaign'],
      campaign_ids: Optional[list[Union[int, str]]] = None,
  ) -> list[Any]:
    """Gets extension assets for ad groups or campaigns.

    Gets existing structured snippets, callouts and sitelink extensions.

    Args:
      customer_id: The Google Ads account id.
      level: The level to get extensions for - ad_group or campaign.
      campaign_ids: A list of Google Ads campaign ids.

    Returns:
      The API response object containing a list of extensions.
    """
    ad_group_name_col = ', ad_group.name' if level == 'ad_group' else ''
    campaign_col = (
        'ad_group.campaign' if level == 'ad_group' else 'campaign.resource_name'
    )
    query = f"""
        SELECT
            campaign.name,
            {campaign_col},
            asset.type,
            asset.structured_snippet_asset.header,
            asset.structured_snippet_asset.values,
            asset.callout_asset.callout_text,
            asset.sitelink_asset.description1,
            asset.sitelink_asset.description2,
            asset.sitelink_asset.link_text,
            asset.final_urls,
            {level}_asset.status{ad_group_name_col}
        FROM
          {level}_asset
        WHERE
          {level}_asset.field_type IN (
              'STRUCTURED_SNIPPET', 'SITELINK', 'CALLOUT')
        """
    if campaign_ids:
      campaign_ids_str = ', '.join(
          [
              f"'customers/{customer_id}/campaigns/{elem}'"
              for elem in campaign_ids
          ]
      )
      query += f' AND {campaign_col} IN ({campaign_ids_str})'
    payload = {'query': ' '.join(query.split())}
    url = SEARCH_URL.format(
        api_version=self.api_version, customer_id=customer_id
    )
    return api_utils.send_api_request(url, payload, self._get_http_header())

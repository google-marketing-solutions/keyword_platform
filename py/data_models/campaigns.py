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

"""Defines the Campaign data model class.

See class docstring for more details.
"""
import time
from typing import Any
from absl import logging
import pandas as pd

ACTION = 'Action'
CAMPAIGN_STATUS = 'Campaign status'
CUSTOMER_ID = 'Customer ID'
CAMPAIGN = 'Campaign'
CAMPAIGN_TYPE = 'Campaign type'
BID_STRATEGY_TYPE = 'Bid strategy type'
LABEL = 'Labels'
UPDATES_APPLIED = 'Updates applied'
BUDGET = 'Budget'

_COLS = [
    ACTION,
    CAMPAIGN_STATUS,
    CUSTOMER_ID,
    CAMPAIGN,  # Campaign name
    CAMPAIGN_TYPE,
    BID_STRATEGY_TYPE,
    BUDGET,
    LABEL,
    UPDATES_APPLIED,  # Updates applied to this DataFrame / Row.
]

_DEFAULT_ACTION = 'Add'
_DEFAULT_STATUS = 'Paused'
_DEFAULT_CUSTOMER_ID = 'Enter customer ID'
_DEFAULT_LABEL = 'Keyword Translator'
_DEFAULT_BUDGET = '1.00'


class Campaigns:
  """A class to represent data for a customer's Google Ads campaigns.

  The columns should match the columns specified in a Google Ads Editor "Create
  New Campaign" template.
  See:
  https://support.google.com/google-ads/answer/10702525?hl=en#zippy=%2Ccampaigns

  Example usage:

  # Initializes campaigns DataFrame from Google Ads API response.
  get_campaign_data_response = google_ads_api_client.get_campaign_data(...)
  campaigns = campaigns_lib.Campaigns(get_campaigns_response)

  # Iterates around the data using df() method.
  for index, row in campaigns.df().iterrows():
    print(row)

  # Passes into GoogleAdsObjects class for transformation.
  google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(campaigns...)

  translator_response = keyword_translator(google_ads_objects)

  campaigns = translator_response.get_campaigns()

  # Records an update to the campaign data. For example, record that translation
  # was applied to 'campaign 1'.
  campaigns.add_update(update='translated', campaigns='campaign 1')

  # Writes campaign data to CSV.
  campaigns.csv_data()
  """

  def __init__(self, response_jsons: list[list[Any]]) -> None:
    """Initializes the Campaigns object.

    Creates a DataFrame containing Campaign data from a Google Ads API
    searchStream response.

    See class docstring for more details.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request. The requests should contain the following fields:
        campaign.name
        campaign.advertising_channel_type
        cmapaign.bidding_strategy_type
    """
    self._df = self._build_campaign_df(response_jsons=response_jsons)
    logging.info('Initialized Campaigns DataFrame with length %d.', self.size())
    self._campaigns_list = self._build_campaigns_list(
        response_jsons=response_jsons
    )

  def _build_campaign_df(self, response_jsons: list[Any]) -> pd.DataFrame:
    """Builds a DataFrame containing Campaign data from Google Ads API JSON.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request.

    Returns:
      A DataFrame containing Campaign data.
    """
    campaigns = []
    for response_json in response_jsons:
      for batch in response_json:
        for result in batch['results']:
          campaigns.append({
              ACTION: _DEFAULT_ACTION,
              CAMPAIGN_STATUS: _DEFAULT_STATUS,
              CUSTOMER_ID: _DEFAULT_CUSTOMER_ID,
              CAMPAIGN: result['campaign']['name'],
              CAMPAIGN_TYPE: (
                  result['campaign']['advertisingChannelType']
                  .capitalize()
                  .replace('_', ' ')
              ),
              BID_STRATEGY_TYPE: (
                  result['campaign']['biddingStrategyType']
                  .capitalize()
                  .replace('_', ' ')
              ),
              BUDGET: _DEFAULT_BUDGET,
              LABEL: _DEFAULT_LABEL,
              UPDATES_APPLIED: [],
          })

    return pd.DataFrame(campaigns, columns=_COLS)

  def _build_campaigns_list(
      self, response_jsons: list[Any]
  ) -> list[dict[str, str]]:
    """Builds a list of Campaign data from Google Ads API JSON.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request.

    Returns:
      A list of dicts with campaign id and name.
    """
    campaigns = []
    for response_json in response_jsons:
      for batch in response_json:
        for result in batch['results']:
          campaigns.append({
              'id': result['campaign']['id'],
              'name': result['campaign']['name'],
          })

    return campaigns

  def df(self) -> pd.DataFrame:
    """Returns the DataFrame containing Campaign data."""
    return self._df

  def campaigns_list(self) -> list[dict[str, str]]:
    return self._campaigns_list

  def csv_data(self) -> str:
    """Returns the DataFrame as CSV."""
    return self._df.to_csv(index=False) or str(_COLS)

  def file_name(self) -> str:
    """Returns the file name."""
    time_str = time.strftime('%Y%m%d-%H%M%S')
    return f'campaigns_{time_str}'

  def add_update(self, update: str) -> None:
    """Marks the row as having been updated by a processor.

    Args:
      update: The name of the update to add. E.g. "translated".
    """
    for index in range(self.size()):
      self._df.loc[index, UPDATES_APPLIED].append(update)
    logging.info('Applied update to Campaign DataFrame: %s.', update)

  def columns(self) -> list[str]:
    """Returns the Campaign columns."""
    return _COLS

  def size(self) -> int:
    """Returns the number of Campaign rows."""
    return len(self._df)

  def campaign_names(self) -> list[str]:
    """Returns a list of unique Campaign names."""
    return list(self._df[CAMPAIGN].unique())

  def add_suffix(self, suffix: str) -> None:
    """Adds a new suffix to the campaign name.

    For example, you could add '(es)' to the campaign name to label it as the
    campaignthat was translated to Spanish.

    Args:
      suffix: The suffix to add to the campaign.
    """
    for index in range(self.size()):
      self._df.loc[index, CAMPAIGN] += f' {suffix}'

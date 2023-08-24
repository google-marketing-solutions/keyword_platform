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

"""Defines the Ad Groups data model class.

See class docstring for more details.
"""

import time
from typing import Any
from absl import logging
import pandas as pd

ACTION = 'Action'
CUSTOMER_ID = 'Customer ID'
CAMPAIGN = 'Campaign'
AD_GROUP = 'Ad group'
STATUS = 'Status'
LABEL = 'Labels'
UPDATES_APPLIED = 'Updates applied'

_COLS = [
    ACTION,
    CUSTOMER_ID,
    CAMPAIGN,  # Campaign name
    AD_GROUP,  # Ad group name
    STATUS,
    LABEL,
    UPDATES_APPLIED,  # Updates applied to this DataFrame / Row.
]

_DEFAULT_ACTION = 'Add'
_DEFAULT_STATUS = 'Paused'
_DEFAULT_CUSTOMER_ID = 'Enter customer ID'
_DEFAULT_LABEL = 'Keyword Translator'


class AdGroups:
  """A class to represent data for a customer's Google Ads Ad Groups.

  The columns should match the columns specified in a Google Ads Editor "Create
  Ad Groups" template.
  See:
  https://support.google.com/google-ads/answer/10702525?hl=en#zippy=%2Ccampaigns%2Cad-groups

  Example usage:

  # Initializes DataFrame from Google Ads API response.
  get_ad_groups_response = google_ads_api_client.get_ad_groups(...)
  ad_groups = ad_groups_lib.AdGroups(get_ad_groups_response)

  # Iterates around the data using df() method.
  for index, row in ad_groups.df().iterrows():
    print(row)

  # Passes into GoogleAdsObjects class for transformation.
  google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(ad_groups...)

  translator_response = keyword_translator(google_ads_objects)

  ad_groups = translator_response.get_ad_groups()

  # Records an update to the campaign data. For example, record that translation
  # was applied.
  ad_groups.add_update(update='translated')
  """

  def __init__(self, response_jsons: list[Any]) -> None:
    """Initializes the Ad Groups object.

    Creates a DataFrame containing Ad Group data from a Google Ads API
    searchStream response.

    See class docstring for more details.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request. The request should contain the following fields:
        campaign.name,
        ad_group.name,
    """
    self._df = self._build_ad_group_df(response_jsons=response_jsons)
    logging.info('Initialized Ad Groups DataFrame with length %d.', self.size())

  def _build_ad_group_df(self, response_jsons: list[Any]) -> pd.DataFrame:
    """Builds a DataFrame containing Ad Group data from Google Ads API JSON.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request.

    Returns:
      A DataFrame containing Ad Group data.
    """
    ad_groups = []
    for response_json in response_jsons:
      for batch in response_json:
        for result in batch['results']:
          ad_groups.append(
              {
                  ACTION: _DEFAULT_ACTION,
                  CUSTOMER_ID: _DEFAULT_CUSTOMER_ID,
                  CAMPAIGN: result['campaign']['name'],
                  AD_GROUP: result['adGroup']['name'],
                  STATUS: _DEFAULT_STATUS,
                  LABEL: _DEFAULT_LABEL,
                  UPDATES_APPLIED: [],
              })

    return pd.DataFrame(ad_groups, columns=_COLS)

  def df(self) -> pd.DataFrame:
    """Returns the DataFrame containing Ad Group data."""
    return self._df

  def csv_data(self) -> str:
    """Returns the DataFrame as CSV."""
    return self._df.to_csv(index=False) or str(_COLS)

  def csv_file_name(self) -> str:
    """Returns the CSV file name."""
    time_str = time.strftime('%Y%m%d-%H%M%S')
    return f'ad_groups_{time_str}.csv'

  def add_update(self, update: str) -> None:
    """Marks the row as having been updated by a processor.

    Args:
      update: The name of the update to add. E.g. "translated".
    """
    for index in range(self.size()):
      self._df.loc[index, UPDATES_APPLIED].append(update)
    logging.info('Applied update to Ads Group DataFrame: %s.', update)

  def columns(self) -> list[str]:
    """Returns the Ad Groups columns."""
    return _COLS

  def size(self) -> int:
    """Returns the number of Ad Group rows."""
    return len(self._df)

  def ad_group_names(self) -> list[str]:
    """Returns a list of unique Ad Group names."""
    return list(self._df[AD_GROUP].unique())

  def add_suffix(self, suffix: str) -> None:
    """Adds a new suffix to the campaign and ad group name.

    For example, you could add '(es)' to the ad group name to label it as the
    ad group that was translated to Spanish.

    Args:
      suffix: The suffix to add to the ad group and campaign
    """
    for index in range(self.size()):
      self._df.loc[index, AD_GROUP] += f' {suffix}'
      self._df.loc[index, CAMPAIGN] += f' {suffix}'

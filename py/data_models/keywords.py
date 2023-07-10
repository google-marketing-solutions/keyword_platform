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

"""Defines the Keywords data model class.

See class docstring for more details.
"""
import collections
import time
from typing import Any

from absl import logging
import pandas as pd

from py.data_models import translation_frame as translation_frame_lib

ACTION = 'Action'
CUSTOMER_ID = 'Customer ID'
CAMPAIGN = 'Campaign'
AD_GROUP = 'Ad group'
KEYWORD = 'Keyword'
ORIGINAL_KEYWORD = 'Original Keyword'
MATCH_TYPE = 'Match Type'
KEYWORD_STATUS = 'Keyword status'
UPDATES_APPLIED = 'Updates applied'

_COLS = [
    ACTION,
    CUSTOMER_ID,
    CAMPAIGN,  # Campaign name
    AD_GROUP,
    KEYWORD,
    ORIGINAL_KEYWORD,
    MATCH_TYPE,
    KEYWORD_STATUS,
    UPDATES_APPLIED,  # Updates applied to this DataFrame / Row.
]

_DEFAULT_ACTION = 'Add'
_DEFAULT_STATUS = 'Paused'
_DEFAULT_CUSTOMER_ID = 'Enter customer ID'


class Keywords:
  """A class to represent data for a customer's Google Ads keywords.

  The columns should match the columns specified in a Google Ads Editor "Add
  Keywords" template.
  See:
  https://support.google.com/google-ads/answer/10702525?hl=en#zippy=%2Ccampaigns%2Ckeywords

  Example usage:

  # Initializes keywords DataFrame from Google Ads API response.
  get_keywords_response = ads_api_client.get_keywords_data_for_campaigns(...)
  keywords = keywords_lib.Keywords(get_keywords_response)

  # Iterates around the data using df() method.
  for index, row in keywords.df().iterrows():
    print(row)

  # Passes into GoogleAdsObjects class for transformation.
  google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(keywords...)

  translator_response = keyword_translator(google_ads_objects)

  # Records an update to the campaign data. For example, record that translation
  # was applied to 'keywords'.
  keywords.add_update(update='translated')

  # Adds some language suffix to ad group name.
  keywords.add_ad_group_suffix('es')
  """

  def __init__(self, response_jsons: list[Any]) -> None:
    """Initializes the Keywords object.

    Creates a DataFrame containing Keywords data from a Google Ads API
    searchStream response.

    See class docstring for more details.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request. The request should contain the following query
        fields
        campaign.name
        ad_group.name
        ad_group_criterion.keyword.text,
        ad_group_criterion.keyword.match_type
    """
    self._df = self._build_keywords_df(response_jsons=response_jsons)
    logging.info('Initialized Keywords DataFrame with length %d.', self.size())

  def _build_keywords_df(self, response_jsons: list[Any]) -> pd.DataFrame:
    """Builds a DataFrame containing Keyword data from Google Ads API JSON.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request.

    Returns:
      A DataFrame containing Keyword data.
    """
    keywords = []
    for response_json in response_jsons:
      for batch in response_json:
        for result in batch['results']:
          keywords.append(
              {
                  ACTION: _DEFAULT_ACTION,
                  CUSTOMER_ID: _DEFAULT_CUSTOMER_ID,
                  CAMPAIGN: result['campaign']['name'],
                  AD_GROUP: result['adGroup']['name'],
                  KEYWORD: result['adGroupCriterion']['keyword']['text'],
                  ORIGINAL_KEYWORD: result[
                      'adGroupCriterion']['keyword']['text'],
                  MATCH_TYPE: result[
                      'adGroupCriterion']['keyword']['matchType'],
                  KEYWORD_STATUS: _DEFAULT_STATUS,
                  UPDATES_APPLIED: [],
              })

    return pd.DataFrame(keywords, columns=_COLS)

  def df(self) -> pd.DataFrame:
    """Returns the DataFrame containing Keyword data."""
    return self._df

  def csv_data(self) -> str:
    """Returns the DataFrame as CSV."""
    return self._df.to_csv(index=False) or str(_COLS)

  def csv_file_name(self) -> str:
    """Returns the CSV file name."""
    time_str = time.strftime('%Y%m%d-%H%M%S')
    return f'keywords_{time_str}.csv'

  def add_update(self, update: str) -> None:
    """Marks the row as having been updated by a processor.

    Args:
      update: The name of the update to add. E.g. "translated".
    """
    for index in range(self.size()):
      self._df.loc[index, UPDATES_APPLIED].append(update)
    logging.info('Applied update to Keyword DataFrame: %s.', update)

  def columns(self) -> list[str]:
    """Returns the Keyword columns."""
    return _COLS

  def size(self) -> int:
    """Returns the number of Keyword rows."""
    return len(self._df)

  def set_keyword(self, row: int, new_keyword: str) -> None:
    """Updates the keyword in the selected row.

    Args:
      row: The row to update the keyword for.
      new_keyword: The new keyword to set.
    """
    self._df.at[row, KEYWORD] = new_keyword

  def add_ad_group_suffix(self, suffix: str) -> None:
    """Adds a new suffix to the ad group name.

    For example, you could add '(es)' to the ad group name to label it as the
    ad group that was translated to Spanish.

    Args:
      suffix: The suffix to add to the ad group.
    """
    for index in range(self.size()):
      self._df.loc[index, AD_GROUP] += f' {suffix}'

  def get_translation_frame(self) -> translation_frame_lib.TranslationFrame:
    """Returns this Keywords object as a TranslationFrame.

    Returns:
      A TranslationFrame containing Keywords data.
    """
    terms_by_rows = collections.defaultdict(list)

    for index, row in self._df.iterrows():
      terms_by_rows[row[KEYWORD]].append((index, KEYWORD))

    return translation_frame_lib.TranslationFrame(terms_by_rows=terms_by_rows)

  def apply_translations(
      self,
      target_language: str,
      translation_frame: translation_frame_lib.TranslationFrame,
      update_ad_group_and_campaign_names: bool = False) -> None:
    """Applies keyword translations to this Keywords object.

    Args:
      target_language: The target translation language.
      translation_frame: A TranslationFrame object containing translation data.
      update_ad_group_and_campaign_names: (Optional) Add the target language as
        a suffix to the ad group and campaign names.
    """
    for _, row in translation_frame.df().iterrows():
      target_row_and_columns = row[translation_frame_lib.DATAFRAME_LOCATIONS]
      target_term = row[translation_frame_lib.TARGET_TERMS][target_language]

      for target_row, target_column in target_row_and_columns:
        self._df.loc[target_row, target_column] = target_term

        if update_ad_group_and_campaign_names:
          self._df.loc[target_row, CAMPAIGN] += f' ({target_language})'
          self._df.loc[target_row, AD_GROUP] += f' ({target_language})'

    logging.info('Finished applying translations to keywords.')

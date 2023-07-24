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

"""Defines the Ads data model class.

See class docstring for more details.
"""

import collections
import sys
import time
from typing import Any

from absl import logging
import pandas as pd

from ..data_models import translation_frame as translation_frame_lib

ACTION = 'Action'
CUSTOMER_ID = 'Customer ID'
AD_STATUS = 'Ad status'
CAMPAIGN = 'Campaign'
AD_GROUP = 'Ad group'
AD_TYPE = 'Ad type'
HEADLINE_1 = 'Headline 1'
ORIGINAL_HEADLINE_1 = 'Original Headline 1'
HEADLINE_2 = 'Headline 2'
ORIGINAL_HEADLINE_2 = 'Original Headline 2'
HEADLINE_3 = 'Headline 3'
ORIGINAL_HEADLINE_3 = 'Original Headline 3'
HEADLINE_4 = 'Headline 4'
ORIGINAL_HEADLINE_4 = 'Original Headline 4'
HEADLINE_5 = 'Headline 5'
ORIGINAL_HEADLINE_5 = 'Original Headline 5'
HEADLINE_6 = 'Headline 6'
ORIGINAL_HEADLINE_6 = 'Original Headline 6'
HEADLINE_7 = 'Headline 7'
ORIGINAL_HEADLINE_7 = 'Original Headline 7'
HEADLINE_8 = 'Headline 8'
ORIGINAL_HEADLINE_8 = 'Original Headline 8'
HEADLINE_9 = 'Headline 9'
ORIGINAL_HEADLINE_9 = 'Original Headline 9'
HEADLINE_10 = 'Headline 10'
ORIGINAL_HEADLINE_10 = 'Original Headline 10'
HEADLINE_11 = 'Headline 11'
ORIGINAL_HEADLINE_11 = 'Original Headline 11'
HEADLINE_12 = 'Headline 12'
ORIGINAL_HEADLINE_12 = 'Original Headline 12'
HEADLINE_13 = 'Headline 13'
ORIGINAL_HEADLINE_13 = 'Original Headline 13'
HEADLINE_14 = 'Headline 14'
ORIGINAL_HEADLINE_14 = 'Original Headline 14'
HEADLINE_15 = 'Headline 15'
ORIGINAL_HEADLINE_15 = 'Original Headline 15'
DESCRIPTION_1 = 'Description 1'
ORIGINAL_DESCRIPTION_1 = 'Original Description 1'
DESCRIPTION_2 = 'Description 2'
ORIGINAL_DESCRIPTION_2 = 'Original Description 2'
DESCRIPTION_3 = 'Description 3'
ORIGINAL_DESCRIPTION_3 = 'Original Description 3'
DESCRIPTION_4 = 'Description 4'
ORIGINAL_DESCRIPTION_4 = 'Original Description 4'
FINAL_URL = 'Final URL'
LABEL = 'Label'
UPDATES_APPLIED = 'Updates applied'

_COLS = [
    ACTION,
    CUSTOMER_ID,
    AD_STATUS,
    CAMPAIGN,  # Campaign name
    AD_GROUP,  # Ad group name
    AD_TYPE,
    HEADLINE_1,
    ORIGINAL_HEADLINE_1,
    HEADLINE_2,
    ORIGINAL_HEADLINE_2,
    HEADLINE_3,
    ORIGINAL_HEADLINE_3,
    HEADLINE_4,
    ORIGINAL_HEADLINE_4,
    HEADLINE_5,
    ORIGINAL_HEADLINE_5,
    HEADLINE_6,
    ORIGINAL_HEADLINE_6,
    HEADLINE_7,
    ORIGINAL_HEADLINE_7,
    HEADLINE_8,
    ORIGINAL_HEADLINE_8,
    HEADLINE_9,
    ORIGINAL_HEADLINE_9,
    HEADLINE_10,
    ORIGINAL_HEADLINE_10,
    HEADLINE_11,
    ORIGINAL_HEADLINE_11,
    HEADLINE_12,
    ORIGINAL_HEADLINE_12,
    HEADLINE_13,
    ORIGINAL_HEADLINE_13,
    HEADLINE_14,
    ORIGINAL_HEADLINE_14,
    HEADLINE_15,
    ORIGINAL_HEADLINE_15,
    DESCRIPTION_1,
    ORIGINAL_DESCRIPTION_1,
    DESCRIPTION_2,
    ORIGINAL_DESCRIPTION_2,
    DESCRIPTION_3,
    ORIGINAL_DESCRIPTION_3,
    DESCRIPTION_4,
    ORIGINAL_DESCRIPTION_4,
    FINAL_URL,
    LABEL,
    UPDATES_APPLIED,  # Updates applied to this DataFrame / Row.
]

_DEFAULT_ACTION = 'Add'
_DEFAULT_CUSTOMER_ID = 'Enter customer ID'
_DEFAULT_STATUS = 'Paused'
_DEFAULT_AD_TYPE = 'Responsive search ad'
_DEFAULT_LABEL = 'Keyword Translator'

_NUM_HEADLINES = 15
_NUM_DESCRIPTIONS = 4


class Ads:
  """A class to represent data for a customer's Google Ads Ad Groups.

  The columns should match the columns specified in a Google Ads Editor "Create
  Response Search Ads" template.
  See:
  https://support.google.com/google-ads/answer/10702525?hl=en#zippy=%2Cads

  Example usage:

  # Initializes DataFrame from Google Ads API response.
  get_ads_response = google_ads_api_client.get_ads(...)
  ads = ads_lib.Ads(get_ads_response)

  # Iterates around the data using df() method.
  for index, row in ads.df().iterrows():
    print(row)

  # Passes into GoogleAdsObjects class for transformation.
  google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(ads...)

  translator_response = keyword_translator(google_ads_objects)

  ads = translator_response.get_ads()

  # Records an update to the campaign data. For example, record that translation
  # was applied.
  ads.add_update(update='translated')
  """

  def __init__(self, response_jsons: list[Any]) -> None:
    """Initializes the Ad object.

    Creates a DataFrame containing Ad data from a Google Ads API
    searchStream response.

    See class docstring for more details.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request. The request should contain the following fields:
        campaign.name,
        ad_group.name,
        ad_group_ad.ad.responsive_search_ad.headlines,
        ad_group_ad.ad.responsive_search_ad.headlines,
        ad_group_ad.ad.responsive_search_ad.descriptions,
        ad_group_ad.ad.final_urls
    """
    self._df = self._build_ads_df(response_jsons=response_jsons)
    logging.info('Initialized Ads DataFrame with length %d.', self.size())

  def _build_ads_df(self, response_jsons: list[Any]) -> pd.DataFrame:
    """Builds a DataFrame containing Ads data from Google Ads API JSON.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request.

    Returns:
      A DataFrame containing Ads data.
    """
    ads = []
    for response_json in response_jsons:
      for batch in response_json:
        for result in batch['results']:
          ad = {
              ACTION: _DEFAULT_ACTION,
              CUSTOMER_ID: _DEFAULT_CUSTOMER_ID,
              AD_STATUS: _DEFAULT_STATUS,
              AD_TYPE: _DEFAULT_AD_TYPE,
              CAMPAIGN: result['campaign']['name'],
              AD_GROUP: result['adGroup']['name'],
          }

          # Adds headlines.
          headlines = result[
              'adGroupAd'].get('ad', {}).get(
                  'responsiveSearchAd', {}).get('headlines', [])
          for headline_index in range(0, _NUM_HEADLINES):
            headline = getattr(
                sys.modules[__name__], f'HEADLINE_{headline_index+1}')
            original_headline = getattr(
                sys.modules[__name__], f'ORIGINAL_HEADLINE_{headline_index+1}'
            )
            if headline_index < len(headlines):
              ad[headline] = headlines[headline_index]['text'].strip()
              ad[original_headline] = headlines[headline_index]['text'].strip()
            else:
              ad[headline] = ''
              ad[original_headline] = ''
            headline_index += 1

          # Adds descriptions
          descriptions = (
              result['adGroupAd']
              .get('ad', {})
              .get('responsiveSearchAd', {})
              .get('descriptions', [])
          )
          for description_index in range(0, _NUM_DESCRIPTIONS):
            description = getattr(
                sys.modules[__name__], f'DESCRIPTION_{description_index+1}'
            )
            original_description = getattr(
                sys.modules[__name__],
                f'ORIGINAL_DESCRIPTION_{description_index+1}',
            )
            if description_index < len(descriptions):
              ad[description] = descriptions[description_index]['text'].strip()
              ad[original_description] = descriptions[description_index][
                  'text'
              ].strip()
            else:
              ad[description] = ''
              ad[original_description] = ''
            description_index += 1

          ad[FINAL_URL] = (
              result['adGroupAd'].get('ad', {}).get('finalUrls', [''])[0]
          )
          ad[LABEL] = _DEFAULT_LABEL
          ad[UPDATES_APPLIED] = []

          ads.append(ad)

    return pd.DataFrame(ads, columns=_COLS)

  def df(self) -> pd.DataFrame:
    """Returns the DataFrame containing Ads data."""
    return self._df

  def csv_data(self) -> str:
    """Returns the DataFrame as CSV."""
    return self._df.to_csv(index=False) or str(_COLS)

  def csv_file_name(self) -> str:
    """Returns the CSV file name."""
    time_str = time.strftime('%Y%m%d-%H%M%S')
    return f'ads_{time_str}.csv'

  def add_update(self, update: str) -> None:
    """Marks the row as having been updated by a processor.

    Args:
      update: The name of the update to add. E.g. "translated".
    """
    for index in range(self.size()):
      self._df.loc[index, UPDATES_APPLIED].append(update)
    logging.info('Applied update to Ads DataFrame: %s.', update)

  def columns(self) -> list[str]:
    """Returns the Ad Groups columns."""
    return _COLS

  def size(self) -> int:
    """Returns the number of Ad rows."""
    return len(self._df)

  def add_campaign_and_ad_group_suffixes(self, suffix: str) -> None:
    """Adds a new suffix to the campaign and ad group names.

    For example, you could add '(es)' to the label them as the
    campaign / ad groups that were translated to Spanish.

    Args:
      suffix: The suffix to add to the ad group.
    """
    for index in range(self.size()):
      self._df.loc[index, CAMPAIGN] += f' {suffix}'
      self._df.loc[index, AD_GROUP] += f' {suffix}'

  def get_translation_frame(self) -> translation_frame_lib.TranslationFrame:
    """Returns ad headlines and descriptions as a TranslationFrame.

    Returns:
      A TranslationFrame containing headlines and descriptions.
    """
    terms_by_rows = collections.defaultdict(list)

    for index, row in self._df.iterrows():
      # Adds headlines for translation
      for headline_index in range(0, _NUM_HEADLINES):
        headline_field = getattr(
            sys.modules[__name__], f'HEADLINE_{headline_index+1}')

        headline = row[headline_field]

        if not headline.strip():
          continue

        terms_by_rows[headline].append((index, headline_field))

      # Adds descriptions for translation
      for description_index in range(0, _NUM_DESCRIPTIONS):
        description_field = getattr(
            sys.modules[__name__], f'DESCRIPTION_{description_index+1}')

        description = row[description_field]

        if not description.strip():
          continue

        terms_by_rows[description].append((index, description_field))

    return translation_frame_lib.TranslationFrame(terms_by_rows=terms_by_rows)

  def apply_translations(
      self,
      target_language: str,
      translation_frame: translation_frame_lib.TranslationFrame,
      update_ad_group_and_campaign_names: bool = False) -> None:
    """Applies keyword translations to the ads' headlines and descriptions.

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
          # TODO(): Improve efficiency of campaign/ad_group updates.
          suffix_str = f' ({target_language})'
          if not self._df.loc[target_row, CAMPAIGN].endswith(suffix_str):
            self._df.loc[target_row, CAMPAIGN] += suffix_str
          if not self._df.loc[target_row, AD_GROUP].endswith(suffix_str):
            self._df.loc[target_row, AD_GROUP] += suffix_str

    logging.info('Finished applying translations to ads.')

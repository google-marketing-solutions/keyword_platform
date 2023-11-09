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

"""Defines the Extensions data model class.

See class docstring for more details.
"""

import collections
import sys
import time
from typing import Any

from absl import logging
import pandas as pd

from data_models import translation_frame as translation_frame_lib
from data_models import translation_metadata

ACTION = 'Action'
CUSTOMER_ID = 'Customer ID'
CAMPAIGN = 'Campaign'
AD_GROUP = 'Ad group'
STATUS = 'Status'
TYPE = 'Asset type'
STRUCTURED_SNIPPET_HEADER = 'Header'
STRUCTURED_SNIPPET_VALUES = 'Snippet values'
ORIGINAL_STRUCTURED_SNIPPET_VALUES = 'Original snippet values'
CALLOUT_TEXT = 'Callout text'
ORIGINAL_CALLOUT_TEXT = 'Original callout text'
SITELINK_DESCRIPTION_1 = 'Description 1'
ORIGINAL_SITELINK_DESCRIPTION_1 = 'Original description 1'
SITELINK_DESCRIPTION_2 = 'Description 2'
ORIGINAL_SITELINK_DESCRIPTION_2 = 'Original description 2'
SITELINK_LINK_TEXT = 'Link text'
ORIGINAL_SITELINK_LINK_TEXT = 'Original link text'
SITELINK_FINAL_URLS = 'Final URLs'
UPDATES_APPLIED = 'Updates applied'

_COLS = [
    ACTION,
    CUSTOMER_ID,
    CAMPAIGN,  # Campaign name
    AD_GROUP,  # Ad group name
    TYPE,
    STATUS,
    STRUCTURED_SNIPPET_HEADER,
    STRUCTURED_SNIPPET_VALUES,
    ORIGINAL_STRUCTURED_SNIPPET_VALUES,
    CALLOUT_TEXT,
    ORIGINAL_CALLOUT_TEXT,
    SITELINK_DESCRIPTION_1,
    ORIGINAL_SITELINK_DESCRIPTION_1,
    SITELINK_DESCRIPTION_2,
    ORIGINAL_SITELINK_DESCRIPTION_2,
    SITELINK_LINK_TEXT,
    ORIGINAL_SITELINK_LINK_TEXT,
    SITELINK_FINAL_URLS,
    UPDATES_APPLIED,  # Updates applied to this DataFrame / Row.
]

_DEFAULT_ACTION = 'Add'
_DEFAULT_CUSTOMER_ID = 'Enter customer ID'

_NUM_SITELINK_DESCRIPTIONS = 2

_SITELINK_TEXT_CHAR_LIMIT = 25
_SITELINK_DESCRIPTION_CHAR_LIMIT = 35
_CALLOUT_TEXT_CHAR_LIMIT = 25
_STRUCTURED_SNIPPET_VALUE_CHAR_LIMIT = 30


class Extensions:
  """A class to represent data for a customer's Google Ads Extensions.

  Example usage:

  # Initializes DataFrame from Google Ads API response.
  get_extensions_response = google_ads_api_client.get_extensions_for_campaigns(
      ...)
  extensions = ad_groups_lib.Extensions(get_extensions_response)

  # Iterates around the data using df() method.
  for index, row in extensions.df().iterrows():
    print(row)

  # Passes into GoogleAdsObjects class for transformation.
  google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(extensions...)

  translator_response = keyword_translator(google_ads_objects)

  extensions = translator_response.get_extensions()

  # Records an update to the campaign data. For example, record that translation
  # was applied.
  extensions.add_update(update='translated')
  """

  def __init__(self, response_jsons: list[Any]) -> None:
    """Initializes the Extensions object.

    Creates a DataFrame containing Extensions data from a Google Ads API
    searchStream response.

    See class docstring for more details.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request.
    """
    self._df = self._build_extensions_df(response_jsons=response_jsons)
    logging.info(
        'Initialized Extensions DataFrame with length %d.', self.size()
    )

  def _build_extensions_df(self, response_jsons: list[Any]) -> pd.DataFrame:
    """Builds a DataFrame containing Extensions data from Google Ads API JSON.

    Args:
      response_jsons: A list of JSON responses from a Google Ads API
        searchStream request.

    Returns:
      A DataFrame containing Extensions data.
    """
    assets = []
    for response_json in response_jsons:
      for batch in response_json:
        for result in batch['results']:
          extension = {
              ACTION: _DEFAULT_ACTION,
              CUSTOMER_ID: _DEFAULT_CUSTOMER_ID,
              CAMPAIGN: result['campaign']['name'],
              TYPE: result['asset']['type'],
              UPDATES_APPLIED: [],
          }
          extension[STATUS] = (
              result['adGroupAsset']['status']
              if result.get('adGroupAsset')
              else result['campaignAsset']['status']
          )
          extension[AD_GROUP] = (
              result['adGroup']['name'] if result.get('adGroup') else ''
          )
          extension[STRUCTURED_SNIPPET_HEADER] = (
              result['asset']['structuredSnippetAsset']['header']
              if result['asset'].get('structuredSnippetAsset')
              else ''
          )
          structured_snippet_values = (
              '\n'.join(result['asset']['structuredSnippetAsset']['values'])
              if result['asset'].get('structuredSnippetAsset')
              else ''
          )
          extension[STRUCTURED_SNIPPET_VALUES] = structured_snippet_values
          extension[ORIGINAL_STRUCTURED_SNIPPET_VALUES] = (
              structured_snippet_values
          )
          callout_text = (
              result['asset']['calloutAsset']['calloutText']
              if result['asset'].get('calloutAsset')
              else ''
          )
          extension[CALLOUT_TEXT] = callout_text
          extension[ORIGINAL_CALLOUT_TEXT] = callout_text
          sitelink_description_1 = (
              result['asset']['sitelinkAsset']['description1']
              if result['asset'].get('sitelinkAsset')
              else ''
          )
          sitelink_description_2 = (
              result['asset']['sitelinkAsset']['description2']
              if result['asset'].get('sitelinkAsset')
              else ''
          )
          extension[SITELINK_DESCRIPTION_1] = sitelink_description_1
          extension[ORIGINAL_SITELINK_DESCRIPTION_1] = sitelink_description_1
          extension[SITELINK_DESCRIPTION_2] = sitelink_description_2
          extension[ORIGINAL_SITELINK_DESCRIPTION_2] = sitelink_description_2
          sitelink_link_text = (
              result['asset']['sitelinkAsset']['linkText']
              if result['asset'].get('sitelinkAsset')
              else ''
          )
          extension[SITELINK_LINK_TEXT] = sitelink_link_text
          extension[ORIGINAL_SITELINK_LINK_TEXT] = sitelink_link_text
          final_urls = (
              ' '.join(result['asset']['finalUrls'])
              if result['asset'].get('sitelinkAsset')
              else ''
          )
          extension[SITELINK_FINAL_URLS] = final_urls
          assets.append(extension)

    return pd.DataFrame(assets, columns=_COLS)

  def get_translation_frame(self) -> translation_frame_lib.TranslationFrame:
    """Returns extensions as a TranslationFrame.

    Returns:
      A TranslationFrame containing extensions.
    """
    terms_with_metadata = collections.defaultdict(
        translation_metadata.TranslationMetadata
    )

    for index, row in self._df.iterrows():
      # Adds descriptions for translation
      for description_index in range(0, _NUM_SITELINK_DESCRIPTIONS):
        description_field = getattr(
            sys.modules[__name__], f'SITELINK_DESCRIPTION_{description_index+1}'
        )

        description = row[description_field]

        if not description.strip():
          continue

        terms_with_metadata[description].dataframe_rows_and_cols.append(
            (index, description_field)
        )
        terms_with_metadata[description].char_limit = (
            _SITELINK_DESCRIPTION_CHAR_LIMIT
        )
      if row[SITELINK_LINK_TEXT].strip():
        terms_with_metadata[
            row[SITELINK_LINK_TEXT]
        ].dataframe_rows_and_cols.append((index, SITELINK_LINK_TEXT))
        terms_with_metadata[row[SITELINK_LINK_TEXT]].char_limit = (
            _SITELINK_TEXT_CHAR_LIMIT
        )
      if row[CALLOUT_TEXT].strip():
        terms_with_metadata[row[CALLOUT_TEXT]].dataframe_rows_and_cols.append(
            (index, CALLOUT_TEXT)
        )
        terms_with_metadata[row[CALLOUT_TEXT]].char_limit = (
            _CALLOUT_TEXT_CHAR_LIMIT
        )
      if row[STRUCTURED_SNIPPET_VALUES].strip():
        terms_with_metadata[
            row[STRUCTURED_SNIPPET_VALUES]
        ].dataframe_rows_and_cols.append((index, STRUCTURED_SNIPPET_VALUES))
        # TODO b/309277157: This is a workaround where we translate all
        # structured snippet values at the same time. Since the char limit is
        # for each value but there may be more than one value, we multiply the
        # char limit with the number of values. Since they are semi-colon
        # separated we add those to the char limit.
        terms_with_metadata[row[STRUCTURED_SNIPPET_VALUES]].char_limit = (
            _STRUCTURED_SNIPPET_VALUE_CHAR_LIMIT
            * len(row[STRUCTURED_SNIPPET_VALUES].split('\n'))
            + len(row[STRUCTURED_SNIPPET_VALUES].split('\n'))
            - 1
        )

    return translation_frame_lib.TranslationFrame(
        terms_with_metadata=terms_with_metadata
    )

  def df(self) -> pd.DataFrame:
    """Returns the DataFrame containing extensions data."""
    return self._df

  def csv_data(self) -> str:
    """Returns the DataFrame as CSV."""
    return self._df.to_csv(index=False)

  def file_name(self) -> str:
    """Returns the file name."""
    time_str = time.strftime('%Y%m%d-%H%M%S')
    return f'extensions_{time_str}'

  def add_update(self, update: str) -> None:
    """Marks the row as having been updated by a processor.

    Args:
      update: The name of the update to add. E.g. "translated".
    """
    for index in range(self.size()):
      self._df.loc[index, UPDATES_APPLIED].append(update)
    logging.info('Applied update to Extensions DataFrame: %s.', update)

  def columns(self) -> list[str]:
    """Returns the Extension columns."""
    return _COLS

  def size(self) -> int:
    """Returns the number of Extension rows."""
    return len(self._df)

  def char_count(self) -> int:
    """Returns a count of chars in elibile extensions."""
    count = 0

    for _, row in self.df().iterrows():
      count += self._count_col_chars(
          row, 'Description', _NUM_SITELINK_DESCRIPTIONS
      )
      count += (
          len(row[CALLOUT_TEXT])
          + len(row[STRUCTURED_SNIPPET_VALUES])
          + len(row[SITELINK_LINK_TEXT])
      )

    logging.info('Char count for extensions chars: %d.', count)

    return count

  def _count_col_chars(
      self, row: pd.Series, col_name: str, num_cols: int
  ) -> int:
    """Helper function to count chars in related columns."""
    count = 0

    for col_index in range(1, num_cols + 1):
      txt = row[f'{col_name} {col_index}']
      if txt:
        count += len(txt.replace(' ', ''))

    return count

  def add_suffix(self, suffix: str) -> None:
    """Adds a new suffix to the campaign and ad group name.

    For example, you could add '(es)' to the ad group name to label it as the
    ad group that was translated to Spanish.

    Args:
      suffix: The suffix to add to the ad group and campaign
    """
    for index in range(self.size()):
      self._df.loc[index, AD_GROUP] += (
          f' {suffix}' if self._df.loc[index, AD_GROUP] else ''
      )
      self._df.loc[index, CAMPAIGN] += f' {suffix}'

  def apply_translations(
      self,
      target_language: str,
      translation_frame: translation_frame_lib.TranslationFrame,
      update_ad_group_and_campaign_names: bool = False,
  ) -> None:
    """Applies keyword translations to the extensions.

    Args:
      target_language: The target translation language.
      translation_frame: A TranslationFrame object containing translation data.
      update_ad_group_and_campaign_names: (Optional) Add the target language as
        a suffix to the ad group and campaign names.
    """
    for _, row in translation_frame.df().iterrows():
      target_row_and_columns = row[translation_frame_lib.DATAFRAME_LOCATIONS]
      target_term = row[translation_frame_lib.TARGET_TERMS].get(
          target_language, ''
      )

      for target_row, target_column in target_row_and_columns:
        self._df.loc[target_row, target_column] = target_term

        if update_ad_group_and_campaign_names:
          # TODO(): Improve efficiency of campaign/ad_group updates.
          suffix_str = f' ({target_language})'
          if (
              not self._df.loc[target_row, CAMPAIGN].endswith(suffix_str)
              and self._df.loc[target_row, CAMPAIGN]
          ):
            self._df.loc[target_row, CAMPAIGN] += suffix_str
          if (
              not self._df.loc[target_row, AD_GROUP].endswith(suffix_str)
              and self._df.loc[target_row, AD_GROUP]
          ):
            self._df.loc[target_row, AD_GROUP] += suffix_str

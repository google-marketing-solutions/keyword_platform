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

"""Defines the Google Ads objects class."""
import dataclasses
import io
import time
import pandas as pd
from data_models import ad_groups as ad_groups_lib
from data_models import ads as ads_lib
from data_models import campaigns as campaigns_lib
from data_models import extensions as extensions_lib
from data_models import keywords as keywords_lib


@dataclasses.dataclass
class GoogleAdsObjects:
  """A class for storing a collection Google Ads objects."""

  ads: ads_lib.Ads|None = None
  ad_groups: ad_groups_lib.AdGroups|None = None
  campaigns: campaigns_lib.Campaigns|None = None
  keywords: keywords_lib.Keywords|None = None
  extensions: extensions_lib.Extensions | None = None

  def get_multiple_dataframes(self) -> dict[str, pd.DataFrame]:
    """Returns a dict of file name and data for the Google Ads objects."""
    data = dict()
    if self.ads:
      data[self.ads.file_name()] = self.ads.df()
    if self.ad_groups:
      data[self.ad_groups.file_name()] = self.ad_groups.df()
    if self.campaigns:
      data[self.campaigns.file_name()] = self.campaigns.df()
    if self.keywords:
      data[self.keywords.file_name()] = self.keywords.df()
    if self.extensions:
      data[self.extensions.file_name()] = self.extensions.df()
    return data

  def get_combined_dataframe(self) -> dict[str, pd.DataFrame]:
    """Combines all objects into a single dictionary."""
    df_data = []
    if self.ads:
      df_data.append(self.ads.df())
    if self.ad_groups:
      df_data.append(self.ad_groups.df())
    if self.campaigns:
      df_data.append(self.campaigns.df())
    if self.keywords:
      df_data.append(self.keywords.df())
    if self.extensions:
      df_data.append(self.extensions.df())
    combined_data = dict()
    if df_data:
      filename = self._generate_combined_file_name()
      combined_data[filename] = pd.concat(df_data, ignore_index=True)
    return combined_data

  def _generate_combined_file_name(self) -> str:
    """Returns the combined file name without extension."""
    time_str = time.strftime('%Y%m%d-%H%M%S')
    return f'combined_{time_str}'

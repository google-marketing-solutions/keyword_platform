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

"""Defines the Google Ads objects class."""
import dataclasses
import io
import time
import pandas as pd
from data_models import ad_groups as ad_groups_lib
from data_models import ads as ads_lib
from data_models import campaigns as campaigns_lib
from data_models import keywords as keywords_lib


@dataclasses.dataclass
class GoogleAdsObjects:
  """A class for storing a collection Google Ads objects."""

  ads: ads_lib.Ads|None = None
  ad_groups: ad_groups_lib.AdGroups|None = None
  campaigns: campaigns_lib.Campaigns|None = None
  keywords: keywords_lib.Keywords|None = None

  def get_multiple_csv_data(self) -> dict[str, str]:
    """Returns a dict of csv file name and data for the Google Ads objects."""
    csv_data = dict()
    if self.ads:
      csv_data[self.ads.csv_file_name()] = self.ads.csv_data()
    if self.ad_groups:
      csv_data[self.ad_groups.csv_file_name()] = self.ad_groups.csv_data()
    if self.campaigns:
      csv_data[self.campaigns.csv_file_name()] = self.campaigns.csv_data()
    if self.keywords:
      csv_data[self.keywords.csv_file_name()] = self.keywords.csv_data()
    return csv_data

  def get_combined_csv_data(self) -> dict[str, str]:
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
    combined_csv_data = dict()
    if df_data:
      filename = self._generate_combined_csv_file_name()
      combined_csv_data[filename] = pd.concat(df_data).to_csv(index=False)
    return combined_csv_data

  def _generate_combined_csv_file_name(self) -> str:
    """Returns the combined CSV file name."""
    time_str = time.strftime('%Y%m%d-%H%M%S')
    return f'combined_{time_str}.csv'

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

"""Defines the TranslationMetadata class."""

import dataclasses


@dataclasses.dataclass
class TranslationMetadata:
  """A class to store metadata about a translation string."""
  # A list DataFrame list of rows where this translation string appears.
  dataframe_rows_and_cols: list[
      tuple[int, str]] = dataclasses.field(default_factory=list)
  char_limit: int = 0
  keyword_insertion_keys: dict[str, str] = dataclasses.field(
      default_factory=dict
  )

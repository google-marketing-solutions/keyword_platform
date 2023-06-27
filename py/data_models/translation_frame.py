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

"""Defines the TranslationFrame data model class.

See class docstring for more details.
"""

from typing import TypeAlias
from absl import logging
import pandas as pd

_DataFrameRowsAndColumns: TypeAlias = list[tuple[int, str]]

SOURCE_TERM = 'source_term'
TARGET_TERMS = 'target_terms'
DATAFRAME_LOCATIONS = 'dataframe_locations'

_COLS = [
    SOURCE_TERM,
    TARGET_TERMS,
    DATAFRAME_LOCATIONS,
]


class TranslationFrame:
  """A class to store source terms and their translations.

  This model can be used to store the a list of source terms to be translated,
  their translations in different languages, and the DataFrame rows where the
  term first appeared (for patching translations quickly).

  It makes it easier to send translation requests in batch, and avoids
  sending duplicate terms for translation.

  Example usage:

  Keywords DF:

     Campaign   | Keyword | Original keyword
     ---------------------------------------
  0  Campaign 1 | email   | email
  1  Campaign 1 | fast    | fast
  2  Campaign 2 | email   | email
     ...

  translation_frame = keywords.get_translation_frame()

  print(translation_frame)

  source_term | target_terms    | dataframe_locations
  ------------------------------------------------------------------
  email       | {}              | [(0, 'Keyword'), (2, 'Keyword')]
  fast        | {}              | [(1, 'Keyword')]
  ...

  > Send translation_frame to Translate API

  source_term | target_terms             | dataframe_locations
  ------------------------------------------------------------------
  email       | {es: correo electrónico} | [(0, 'Keyword'), (2, 'Keyword')]
  fast        | {es: rápida}             | [(1, 'Keyword')]
  ...

  > Update rows in Keywords DF with translation_frame

     Campaign   | Keyword              | Original keyword
     -----------------------------------------
  0  Campaign 1 | correo electrónico   | email
  1  Campaign 1 | rápida               | fast
  2  Campaign 2 | correo electrónico   | email
     ...

  """

  def __init__(
      self, terms_by_rows: dict[str, _DataFrameRowsAndColumns]) -> None:
    """Initiatializes the TranslationFrame class.

    Args:
      terms_by_rows: A list of terms and a rows/columns in the source DataFrame
        where they appear.
    """
    terms = []
    for term, rows in terms_by_rows.items():
      terms.append({
          SOURCE_TERM: term,
          TARGET_TERMS: {},
          DATAFRAME_LOCATIONS: rows,
      })

    self._df = pd.DataFrame(terms, columns=_COLS)
    logging.info('Initialized translation frame of size %d', self.size())

  def add_translations(
      self,
      start_index: int,
      target_language_code: str,
      translations: list[str]) -> None:
    """Adds translations to the translation frame.

    Args:
      start_index: The row to start adding translations from.
      target_language_code: The language code for the translations to add.
      translations: A list of translations, per row.
    """
    for row, translation in enumerate(translations):
      self._df.loc[row+start_index, TARGET_TERMS][
          target_language_code] = translation

  def df(self) -> pd.DataFrame:
    """Returns the DataFrame containing translation data."""
    return self._df

  def size(self) -> int:
    """Returns the number of rows."""
    return len(self._df)

  def get_terms(self, start_row: int, end_row: int) -> list[str]:
    """Returns source terms from start_row to end_row, inclusive.

    Args:
      start_row: The start row in the DataFrame.
      end_row: The end row in the DataFrame.

    Returns:
      The source terms between start_row and end_row, inclusive.
    """
    return list(self.df().loc[start_row:end_row, SOURCE_TERM])

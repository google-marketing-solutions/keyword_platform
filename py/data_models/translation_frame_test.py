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

"""Tests for the TranslationFrame data model class."""

import pandas as pd

from absl.testing import absltest
from absl.testing import parameterized
from data_models import translation_frame as translation_frame_lib
from data_models import translation_metadata


_EXPECTED_DF = pd.DataFrame(
    {
        'source_term': [
            'email',
            'fast',
            'Open {Keyword:today} and {keyword: tomorrow}',
        ],
        'target_terms': [{}, {}, {}],
        'dataframe_locations': [
            [(0, 'Keyword'), (2, 'Keyword')],
            [(1, 'Keyword')],
            [(2, 'Headline 1')],
        ],
        'char_limit': [30, 30, 45],
    },
)

_EXPECTED_DF_AFTER_TRANSLATION = pd.DataFrame(
    {
        'source_term': [
            'email',
            'fast',
            'Open {Keyword:today} and {keyword: tomorrow}',
        ],
        'target_terms': [
            {'es': 'correo electrónico'},
            {'es': 'rápida'},
            {'es': 'Abra {Keyword:hoy} y {keyword: mañana}'},
        ],
        'dataframe_locations': [
            [(0, 'Keyword'), (2, 'Keyword')],
            [(1, 'Keyword')],
            [(2, 'Headline 1')],
        ],
        'char_limit': [30, 30, 45],
    },
)


class TranslationFrameTest(parameterized.TestCase):

  def test_df(self):
    input_data = {
        'email': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Keyword'), (2, 'Keyword')],
            char_limit=30,
        ),
        'fast': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')], char_limit=30
        ),
        'Open {Keyword:today} and {keyword: tomorrow}': (
            translation_metadata.TranslationMetadata(
                dataframe_rows_and_cols=[(2, 'Headline 1')], char_limit=45
            )
        ),
    }
    expected_df = _EXPECTED_DF

    translation_frame = translation_frame_lib.TranslationFrame(input_data)

    actual_df = translation_frame.df()

    pd.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  def test_size(self):
    input_data = {
        'email': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Keyword'), (2, 'Keyword')],
            char_limit=30,
        ),
        'fast': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')], char_limit=30
        ),
        'Open {Keyword:today} and {keyword: tomorrow}': (
            translation_metadata.TranslationMetadata(
                dataframe_rows_and_cols=[(2, 'Headline 1')], char_limit=45
            )
        ),
    }
    expected_size = 3

    translation_frame = translation_frame_lib.TranslationFrame(input_data)
    actual_size = translation_frame.size()

    self.assertEqual(actual_size, expected_size)

  def test_add_translation(self):
    input_data = {
        'email': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Keyword'), (2, 'Keyword')],
            char_limit=30,
        ),
        'fast': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')], char_limit=30
        ),
        'Open {Keyword:today} and {keyword: tomorrow}': (
            translation_metadata.TranslationMetadata(
                dataframe_rows_and_cols=[(2, 'Headline 1')], char_limit=45
            )
        ),
    }
    expected_df = _EXPECTED_DF_AFTER_TRANSLATION

    translation_frame = translation_frame_lib.TranslationFrame(input_data)
    translation_frame.add_translations(
        start_index=0,
        target_language_code='es',
        translations=[
            'correo electrónico',
            'rápida',
            'Abra {Keyword:hoy} y {keyword: mañana}',
        ],
    )

    actual_df = translation_frame.df()

    pd.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False
    )

  def test_get_term_batch(self):
    # TODO(): Figure out best approach for testing ad text that
    # includes keyword insertion tag after fixing issue where keyword insertion
    # in text contains numeric key.
    input_data = {
        'email': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(0, 'Keyword'), (2, 'Keyword')],
            char_limit=30,
        ),
        'fast': translation_metadata.TranslationMetadata(
            dataframe_rows_and_cols=[(1, 'Keyword')], char_limit=30
        ),
        'Open {Keyword:today} and {keyword: tomorrow}': (
            translation_metadata.TranslationMetadata(
                dataframe_rows_and_cols=[(2, 'Headline 1')], char_limit=45
            )
        ),
    }

    expected_terms = [
        'email',
        'fast',
        'Open {Keyword:today} and {keyword: tomorrow}',
    ]
    expected_next_row = 3

    translation_frame = translation_frame_lib.TranslationFrame(input_data)
    actual_terms, actual_next_row = translation_frame.get_term_batch(0, 53)

    self.assertEqual(actual_terms, expected_terms)
    self.assertEqual(actual_next_row, expected_next_row)


if __name__ == '__main__':
  absltest.main()

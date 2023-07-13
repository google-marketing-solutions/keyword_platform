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

"""Tests for the TranslationFrame data model class."""

import pandas as pd
from py.data_models import translation_frame as translation_frame_lib
from absl.testing import absltest
from absl.testing import parameterized


_EXPECTED_DF = pd.DataFrame(
    {'source_term': ['email', 'fast'],
     'target_terms': [{}, {}],
     'dataframe_locations': [
         [(0, 'Keyword'), (2, 'Keyword')], [(1, 'Keyword')]],
     },
)

_EXPECTED_DF_AFTER_TRANSLATION = pd.DataFrame(
    {'source_term': ['email', 'fast'],
     'target_terms': [{'es': 'correo electrónico'}, {'es': 'rápida'}],
     'dataframe_locations': [
         [(0, 'Keyword'), (2, 'Keyword')], [(1, 'Keyword')]],
     },
)


class TranslationFrameTest(parameterized.TestCase):

  def test_df(self):
    input_data = {
        'email': [(0, 'Keyword'), (2, 'Keyword')],
        'fast': [(1, 'Keyword')],
    }
    expected_df = _EXPECTED_DF

    translation_frame = translation_frame_lib.TranslationFrame(input_data)

    actual_df = translation_frame.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  def test_size(self):
    input_data = {
        'email': [(0, 'Keyword'), (2, 'Keyword')],
        'fast': [(1, 'Keyword')],
    }
    expected_size = 2

    translation_frame = translation_frame_lib.TranslationFrame(input_data)
    actual_size = translation_frame.size()

    self.assertEqual(actual_size, expected_size)

  def test_add_translation(self):
    input_data = {
        'email': [(0, 'Keyword'), (2, 'Keyword')],
        'fast': [(1, 'Keyword')],
    }
    expected_df = _EXPECTED_DF_AFTER_TRANSLATION

    translation_frame = translation_frame_lib.TranslationFrame(input_data)
    translation_frame.add_translations(
        start_index=0,
        target_language_code='es',
        translations=['correo electrónico', 'rápida'])

    actual_df = translation_frame.df()

    pd.util.testing.assert_frame_equal(
        actual_df, expected_df, check_index_type=False)

  def test_get_term_batch(self):
    input_data = {
        'email': [(0, 'Keyword'), (2, 'Keyword')],
        'fast': [(1, 'Keyword')],
        'efficient': [(2, 'Keyword')],
    }

    expected_terms = ['email', 'fast']
    expected_next_row = 2

    translation_frame = translation_frame_lib.TranslationFrame(input_data)
    actual_terms, actual_next_row = translation_frame.get_term_batch(0, 10)

    self.assertEqual(actual_terms, expected_terms)
    self.assertEqual(actual_next_row, expected_next_row)


if __name__ == '__main__':
  absltest.main()

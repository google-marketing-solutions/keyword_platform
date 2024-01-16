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

"""Tests for google_ads_objects."""
import time
from unittest import mock

import numpy as np
import pandas as pd

from absl.testing import absltest
from data_models import google_ads_objects as google_ads_objects_lib

_FAKE_DATA = 'fake_data'

_FAKE_DF_1 = pd.DataFrame(data=[_FAKE_DATA], columns=['fake_header_1'])

_FAKE_DF_2 = pd.DataFrame(data=[_FAKE_DATA], columns=['fake_header_2'])

_FAKE_FILE_NAME = 'fake_file_name'

_EXPECTED_DATA = {
    _FAKE_FILE_NAME: _FAKE_DF_1,
    _FAKE_FILE_NAME: _FAKE_DF_1,
    _FAKE_FILE_NAME: _FAKE_DF_1,
    _FAKE_FILE_NAME: _FAKE_DF_1,
}

_EXPECTED_DATA_MISSING_OBJECT = {
    _FAKE_FILE_NAME: _FAKE_DF_1,
    _FAKE_FILE_NAME: _FAKE_DF_1,
    _FAKE_FILE_NAME: _FAKE_DF_1,
}


class GoogleAdsObjectsTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.mock_google_ads_object = mock.MagicMock()
    self.mock_google_ads_object.file_name.return_value = _FAKE_FILE_NAME

  def test_get_multiple_dataframes_all_objects_present(self):
    self.mock_google_ads_object.df.return_value = _FAKE_DF_1
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        self.mock_google_ads_object,
        self.mock_google_ads_object,
        self.mock_google_ads_object,
        self.mock_google_ads_object,
    )
    data = google_ads_objects.get_multiple_dataframes()

    self.assertEqual(self.mock_google_ads_object.df.call_count, 4)
    self.assertEqual(True, data == _EXPECTED_DATA)

  def test_get_multiple_dataframes_missing_object(self):
    self.mock_google_ads_object.df.return_value = _FAKE_DF_1
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        self.mock_google_ads_object,
        self.mock_google_ads_object,
        self.mock_google_ads_object,
    )
    data = google_ads_objects.get_multiple_dataframes()

    self.assertEqual(self.mock_google_ads_object.df.call_count, 3)

    for entry in data:
      pd.testing.assert_frame_equal(
          data[entry],
          _EXPECTED_DATA_MISSING_OBJECT[entry],
          check_index_type=False,
      )

  def test_get_multiple_dataframes_empty(self):
    self.mock_google_ads_object.df.return_value = _FAKE_DF_1
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects()
    data = google_ads_objects.get_multiple_dataframes()

    self.mock_google_ads_object.df.assert_not_called()
    self.assertEqual(data, {})

  @mock.patch.object(time, 'strftime', autospec=True, return_value='fake_time')
  def test_get_combined_dataframe_all_objects_present(self, mock_time):
    del mock_time
    self.mock_google_ads_object.df.side_effect = [
        _FAKE_DF_1,
        _FAKE_DF_1,
        _FAKE_DF_1,
        _FAKE_DF_1,
    ]

    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        self.mock_google_ads_object,
        self.mock_google_ads_object,
        self.mock_google_ads_object,
        self.mock_google_ads_object,
    )
    expected_file_name = 'combined_fake_time'
    expected_result = pd.DataFrame(
        data=['fake_data', 'fake_data', 'fake_data', 'fake_data'],
        columns=['fake_header_1'],
    )

    combined_data = google_ads_objects.get_combined_dataframe()

    self.assertEqual(self.mock_google_ads_object.df.call_count, 4)
    pd.testing.assert_frame_equal(
        combined_data[expected_file_name],
        expected_result,
        check_index_type=False,
    )

  @mock.patch.object(time, 'strftime', autospec=True, return_value='fake_time')
  def test_get_combined_dataframe_missing_object(self, mock_time):
    del mock_time
    self.mock_google_ads_object.df.side_effect = [_FAKE_DF_1, _FAKE_DF_2]
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        self.mock_google_ads_object,
        self.mock_google_ads_object,
    )
    expected_file_name = 'combined_fake_time'
    expected_result = pd.DataFrame(
        data=[['fake_data', np.nan], [np.nan, 'fake_data']],
        columns=['fake_header_1', 'fake_header_2'],
    )
    combined_data = google_ads_objects.get_combined_dataframe()

    self.assertEqual(self.mock_google_ads_object.df.call_count, 2)
    pd.testing.assert_frame_equal(
        combined_data[expected_file_name],
        expected_result,
        check_index_type=False,
    )

  @mock.patch.object(time, 'strftime', autospec=True, return_value='fake_time')
  def test_get_combined_dataframe_empty(self, mock_time):
    del mock_time
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects()
    combined_data = google_ads_objects.get_combined_dataframe()

    self.mock_google_ads_object.df.assert_not_called()
    self.assertEqual(combined_data, {})


if __name__ == '__main__':
  absltest.main()

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

"""Tests for google_ads_objects."""

from unittest import mock

from data_models import google_ads_objects as google_ads_objects_lib
from absl.testing import absltest


_FAKE_CSV_DATA = 'fake_csv_data'

_FAKE_CSV_FILE_NAME = 'fake_csv_file_name'

_EXPECTED_CSV_DATA = {
    _FAKE_CSV_FILE_NAME: _FAKE_CSV_DATA,
    _FAKE_CSV_FILE_NAME: _FAKE_CSV_DATA,
    _FAKE_CSV_FILE_NAME: _FAKE_CSV_DATA,
    _FAKE_CSV_FILE_NAME: _FAKE_CSV_DATA,
}

_EXPECTED_CSV_DATA_MISSING_OBJECT = {
    _FAKE_CSV_FILE_NAME: _FAKE_CSV_DATA,
    _FAKE_CSV_FILE_NAME: _FAKE_CSV_DATA,
    _FAKE_CSV_FILE_NAME: _FAKE_CSV_DATA,
}


class GoogleAdsObjectsTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.mock_google_ads_object = mock.MagicMock()
    self.mock_google_ads_object.csv_file_name.return_value = _FAKE_CSV_FILE_NAME
    self.mock_google_ads_object.csv_data.return_value = _FAKE_CSV_DATA

  def test_get_csv_data_all_objects_present(self):
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        self.mock_google_ads_object,
        self.mock_google_ads_object,
        self.mock_google_ads_object,
        self.mock_google_ads_object,
    )
    csv_data = google_ads_objects.get_csv_data()

    self.assertEqual(self.mock_google_ads_object.csv_data.call_count, 4)
    self.assertEqual(csv_data, _EXPECTED_CSV_DATA)

  def test_get_csv_data_missing_object(self):
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        self.mock_google_ads_object,
        self.mock_google_ads_object,
        self.mock_google_ads_object,
    )
    csv_data = google_ads_objects.get_csv_data()

    self.assertEqual(self.mock_google_ads_object.csv_data.call_count, 3)
    self.assertEqual(csv_data, _EXPECTED_CSV_DATA_MISSING_OBJECT)

  def test_get_csv_data_empty(self):
    google_ads_objects = google_ads_objects_lib.GoogleAdsObjects()
    csv_data = google_ads_objects.get_csv_data()

    self.mock_google_ads_object.csv_data.assert_not_called()
    self.assertEqual(csv_data, {})


if __name__ == '__main__':
  absltest.main()

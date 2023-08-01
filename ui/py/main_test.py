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

"""Tests for main."""

from unittest import mock

import flask

from absl.testing import absltest
from keyword_platform.ui.py import main


class MainTest(absltest.TestCase):

  @mock.patch.object(flask, 'send_from_directory', autospec=True)
  def test_index(self, mock_send_from_directory):
    mock_index_page = mock.MagicMock()

    mock_send_from_directory.return_value = mock_index_page

    expected_index_page = mock_index_page
    actual_index_page = main.index()

    self.assertEqual(expected_index_page, actual_index_page)

  @mock.patch.object(flask, 'send_from_directory', autospec=True)
  def test_favicon(self, mock_send_from_directory):
    mock_favicon = mock.MagicMock()

    mock_send_from_directory.return_value = mock_favicon

    expected_favicon = mock_favicon
    actual_favicon = main.favicon()

    self.assertEqual(expected_favicon, actual_favicon)


if __name__ == "__main__":
  absltest.main()

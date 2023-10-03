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

"""Tests for utils."""

import time
from unittest import mock

from absl.testing import absltest
from common import utils


class TestClass:

  def __init__(self):
    print('Initializing')

  @utils.exponential_backoff_retry(
      base_delay=1, back_off_factor=2, max_retries=3
  )
  def test_method(self):
    return 'Success'

  @utils.exponential_backoff_retry(
      base_delay=1, back_off_factor=2, max_retries=3
  )
  def test_method_raises_exception(self):
    raise Exception('Test Exception')

  @utils.exponential_backoff_retry(
      base_delay=1, back_off_factor=2, max_retries=3, exceptions=[TypeError]
  )
  def test_method_raises_out_of_scope_exception(self):
    raise FileNotFoundError('Out of Scope Exception')


class UtilsTest(absltest.TestCase):

  def setUp(self):
    super().setUp()

  def test_retry_succeeds(self):
    result = TestClass().test_method()
    self.assertEqual(result, 'Success')

  @mock.patch.object(time, 'sleep', autospec=True)
  def test_retry_exceeds_limit(self, sleep_mock):
    with self.assertRaises(utils.MaxRetriesExceededError):
      TestClass().test_method_raises_exception()

    sleep_mock.assert_has_calls([
        mock.call(2),
        mock.call(4),
    ])

  def test_raises_out_of_scope_exception(self):
    with self.assertRaises(FileNotFoundError):
      TestClass().test_method_raises_out_of_scope_exception()

  def test_raises_out_of_scope_exception_logs(self):
    with self.assertLogs(level='ERROR') as log_mock:
      try:
        TestClass().test_method_raises_out_of_scope_exception()
      except FileNotFoundError:
        pass

      self.assertEqual(
          log_mock.output,
          ['ERROR:absl:FileNotFoundError not within exception to retry.'],
      )


if __name__ == '__main__':
  absltest.main()

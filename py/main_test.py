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


from absl.testing import absltest
import execution_runner
import main
from data_models import accounts as accounts_lib
from workers import worker_result


class MainTest(absltest.TestCase):

  @mock.patch.object(main, '_setup_logging', autospec=True)
  @mock.patch.object(execution_runner, 'ExecutionRunner', autospec=True)
  def test_get_accessible_accounts(
      self, mock_execution_runner, mock_setup_logging):
    del mock_setup_logging  # Unused.

    mock_execution_runner.return_value.get_accounts.return_value = [
        accounts_lib.Account(id='1234567890', name='Account 1'),
        accounts_lib.Account(id='1112131415', name='[NO NAME SET]'),
    ]

    expected_status_code = 200

    expected_json = [
        {'id': '1234567890', 'name': 'Account 1'},
        {'id': '1112131415', 'name': '[NO NAME SET]'}]

    actual_response = main.app.test_client().get('/accessible_accounts')

    self.assertEqual(expected_status_code, actual_response.status_code)
    self.assertEqual(expected_json, actual_response.json)

  @mock.patch.object(main, '_setup_logging', autospec=True)
  @mock.patch.object(execution_runner, 'ExecutionRunner', autospec=True)
  def test_get_accessible_accounts_returns_error_on_exception(
      self, mock_execution_runner, mock_setup_logging):
    del mock_setup_logging  # Unused.

    mock_execution_runner.return_value.get_accounts.side_effect = Exception(
        'Something went wrong')

    expected_status_code = 500

    expected_data = ('The server encountered and error and could not complete '
                     'your request. Developers can check the logs for details.')

    actual_response = main.app.test_client().get('/accessible_accounts')

    self.assertEqual(expected_status_code, actual_response.status_code)
    self.assertEqual(expected_data, actual_response.text)

  @mock.patch.object(main, '_setup_logging', autospec=True)
  @mock.patch.object(execution_runner, 'ExecutionRunner', autospec=True)
  def test_get_campaigns(
      self, mock_execution_runner, mock_setup_logging):
    del mock_setup_logging  # Unused.

    mock_execution_runner.return_value.get_campaigns_for_selected_accounts.return_value = [
        {
            'id': '12345',
            'name': 'Campaign 1',
        },
        {
            'id': '56789',
            'name': 'Campaign 2',
        },
    ]

    expected_status_code = 200

    expected_json = [
        {'id': '12345', 'name': 'Campaign 1'},
        {'id': '56789', 'name': 'Campaign 2'}]

    actual_response = main.app.test_client().get(
        '/campaigns?selected_accounts=123,567')

    self.assertEqual(expected_status_code, actual_response.status_code)
    self.assertEqual(expected_json, actual_response.json)

  @mock.patch.object(main, '_setup_logging', autospec=True)
  @mock.patch.object(execution_runner, 'ExecutionRunner', autospec=True)
  def test_get_campaigns_returns_error_on_exception(
      self, mock_execution_runner, mock_setup_logging):
    del mock_setup_logging  # Unused.

    mock_execution_runner.return_value.get_campaigns_for_selected_accounts.side_effect = Exception(
        'Something went wrong')

    expected_status_code = 500

    expected_data = ('The server encountered and error and could not complete '
                     'your request. Developers can check the logs for details.')

    actual_response = main.app.test_client().get(
        '/campaigns?selected_accounts=123,567')

    self.assertEqual(expected_status_code, actual_response.status_code)
    self.assertEqual(expected_data, actual_response.text)

  @mock.patch.object(main, '_setup_logging', autospec=True)
  @mock.patch.object(execution_runner, 'ExecutionRunner', autospec=True)
  def test_run(
      self, mock_execution_runner, mock_setup_logging):
    del mock_setup_logging  # Unused.

    mock_execution_runner.return_value.run_workers.return_value = {
        'worker_results': {
            'translationWorker': worker_result.WorkerResult(
                status=worker_result.Status.SUCCESS,
                keywords_modified=100),
            },
        'asset_urls': ['file1', 'file2', 'file3'],
    }

    expected_status_code = 200

    expected_json = {
        'asset_urls': ['file1', 'file2', 'file3'],
        'worker_results': {
            'translationWorker': {
                'error_msg': '',
                'keywords_added': 0,
                'keywords_modified': 100,
                'status': 'SUCCESS',
                'warning_msg': '',
            }
        },
    }

    actual_response = main.app.test_client().get(
        (
            '/run?customer_ids=123,567&source_language_code=en&'
            'target_language_codes=de&campaigns=987654321&'
            'workers_to_run=translationWorker&'
            'multiple_templates=False&client_id=aaa.bbb'
        )
    )

    self.assertEqual(expected_status_code, actual_response.status_code)
    self.assertEqual(expected_json, actual_response.json)

  @mock.patch.object(main, '_setup_logging', autospec=True)
  @mock.patch.object(execution_runner, 'ExecutionRunner', autospec=True)
  def test_run_returns_error_on_exception(
      self, mock_execution_runner, mock_setup_logging):
    del mock_setup_logging  # Unused.

    mock_execution_runner.return_value.run_workers.side_effect = Exception(
        'Something went wrong')

    expected_status_code = 500

    expected_data = ('The server encountered and error and could not complete '
                     'your request. Developers can check the logs for details.')

    actual_response = main.app.test_client().get(
        ('/run?customer_ids=123,567&source_language_code=en&'
         'target_language_codes=de&campaigns=abc&'
         'workers_to_run=translationWorker&'
         'multiple_templates=False&client_id=aaa.bbb'))

    self.assertEqual(expected_status_code, actual_response.status_code)
    self.assertEqual(expected_data, actual_response.text)

  @mock.patch.object(main, '_setup_logging', autospec=True)
  @mock.patch.object(execution_runner, 'ExecutionRunner', autospec=True)
  def test_get_cost(
      self, mock_execution_runner, mock_setup_logging):
    del mock_setup_logging  # Unused.

    expected_cost_estimate_msg = (
        'Estimated cost: $0.30 USD. '
        '(12000 ad chars + 3000 keyword chars) * $0.000020/char.)')

    mock_execution_runner.return_value.get_cost_estimate.return_value = (
        expected_cost_estimate_msg)

    expected_status_code = 200

    actual_response = main.app.test_client().post('cost', data={
        'customer_ids': '123,567',
        'campaigns': '987654321',
    })

    self.assertEqual(expected_status_code, actual_response.status_code)
    self.assertEqual(expected_cost_estimate_msg, actual_response.text)

  @mock.patch.object(main, '_setup_logging', autospec=True)
  @mock.patch.object(execution_runner, 'ExecutionRunner', autospec=True)
  def test_cost_returns_error_on_exception(
      self, mock_execution_runner, mock_setup_logging
  ):
    del mock_setup_logging  # Unused.

    mock_execution_runner.return_value.get_cost_estimate.side_effect = (
        Exception('Something went wrong')
    )

    expected_status_code = 500

    expected_data = (
        'The server encountered and error and could not complete '
        'your request. Developers can check the logs for details.'
    )

    actual_response = main.app.test_client().post(
        'cost',
        data={
            'customer_ids': '123,567',
            'campaigns': '987654321',
        },
    )

    self.assertEqual(expected_status_code, actual_response.status_code)
    self.assertEqual(expected_data, actual_response.text)


if __name__ == '__main__':
  absltest.main()

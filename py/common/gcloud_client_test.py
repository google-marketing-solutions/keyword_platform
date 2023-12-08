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

"""Tests for gcloud_client."""

import os
import subprocess
from unittest import mock
from absl.testing import absltest
from common import gcloud_client as gcloud_client_lib


class GcloudClientTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.enter_context(
        mock.patch.dict(os.environ, {'GCP_PROJECT': 'fake_project'})
    )
    self.enter_context(
        mock.patch.dict(os.environ, {'GCP_REGION': 'fake_region'})
    )
    self.mock_process = self.enter_context(
        mock.patch.object(subprocess, 'Popen', autospec=True)
    )

  def test_init(self):
    with self.assertLogs(level='INFO') as logs:
      gcloud_client = gcloud_client_lib.GcloudClient()
      self.assertEqual(
          logs.output[0],
          'INFO:root:GCloud Client: Initialized in project fake_project and'
          ' region fake_region',
      )

      self.assertEqual(gcloud_client._project_id, 'fake_project')
      self.assertEqual(gcloud_client._region, 'fake_region')

  def test_run(self):
    self.mock_process.return_value.communicate.return_value = ('', '')
    gcloud_client = gcloud_client_lib.GcloudClient()
    cmd_str = (
        'run services describe fake_service'
        ' --format=value(status.latestCreatedRevisionName) --platform=managed'
    )
    expected_cmd = [
        'gcloud',
        'run',
        'services',
        'describe',
        'fake_service',
        '--format=value(status.latestCreatedRevisionName)',
        '--platform=managed',
        '--project=fake_project',
        '--region=fake_region',
    ]
    gcloud_client.run(cmd_str, True)

    self.mock_process.assert_called_once_with(
        expected_cmd, stdout=-1, stderr=-1, universal_newlines=True
    )

  def test_get_run_service_ref_name(self):
    self.mock_process.return_value.communicate.side_effect = [
        ('fake_revision\n', ''),
        ('fake_build\n', ''),
        ('fake_version\n', ''),
    ]
    expected_result = 'fake_version'
    actual_result = gcloud_client_lib.GcloudClient().get_run_service_ref_name(
        'fake_service'
    )

    self.assertEqual(expected_result, actual_result)
    self.mock_process.assert_has_calls([
        mock.call(
            [
                'gcloud',
                'run',
                'services',
                'describe',
                'fake_service',
                '--format=value(status.latestCreatedRevisionName)',
                '--platform=managed',
                '--project=fake_project',
                '--region=fake_region',
            ],
            stdout=-1,
            stderr=-1,
            universal_newlines=True,
        ),
        mock.call().communicate(),
        mock.call(
            [
                'gcloud',
                'run',
                'revisions',
                'describe',
                'fake_revision',
                '--format=value(labels.gcb-build-id)',
                '--project=fake_project',
                '--region=fake_region',
            ],
            stdout=-1,
            stderr=-1,
            universal_newlines=True,
        ),
        mock.call().communicate(),
        mock.call(
            [
                'gcloud',
                'builds',
                'describe',
                'fake_build',
                '--format=value(substitutions.REF_NAME)',
                '--project=fake_project',
            ],
            stdout=-1,
            stderr=-1,
            universal_newlines=True,
        ),
        mock.call().communicate(),
    ])

  def test_get_run_service_ref_name_has_errors(self):
    self.mock_process.return_value.communicate.side_effect = [
        ('fake_revision\n', ''),
        ('fake_build\n', ''),
        ('', 'fake_error\n'),
    ]

    with self.assertLogs(level='WARNING') as logs:
      expected_result = ''
      actual_result = gcloud_client_lib.GcloudClient().get_run_service_ref_name(
          'fake_service'
      )
      self.assertEqual(
          logs.output[0],
          'WARNING:root:GCloud Client: An error occured running command: gcloud'
          ' builds describe fake_build --format=value(substitutions.REF_NAME)'
          ' --project=fake_project: fake_error',
      )
      self.assertEqual(expected_result, actual_result)


if __name__ == '__main__':
  absltest.main()

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

import datetime
import os
import subprocess
from unittest import mock
from google.cloud.devtools import cloudbuild_v1
from absl.testing import absltest
from common import gcloud_client as gcloud_client_lib


_FAKE_CLOUDBUILD_SERVICE_RESPONSE = [
    cloudbuild_v1.Build(
        id='fake_build_id',
        substitutions={'REF_NAME': 'fake_version'},
        status=cloudbuild_v1.Build.Status.SUCCESS,
        finish_time=datetime.datetime(2023, 10, 19, 17, 15, 59, 684230),
        results={
            'images': [
                {'name': 'gcr.io/fake_project/keywordplatform-backend:latest'}
            ]
        },
    )
]

class GcloudClientTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.enter_context(
        mock.patch.dict(os.environ, {'GCP_PROJECT': 'fake_project'})
    )
    self.enter_context(
        mock.patch.dict(os.environ, {'GCP_REGION': 'fake_region'})
    )
    self.mock_cloudbuild_client = self.enter_context(
        mock.patch.object(cloudbuild_v1, 'CloudBuildClient', autospec=True)
    )
    self.mock_cloudbuild_client.return_value.list_builds.return_value = (
        _FAKE_CLOUDBUILD_SERVICE_RESPONSE
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

  def test_get_run_service_ref_name(self):
    actual_result = gcloud_client_lib.GcloudClient().get_run_service_ref_name(
        'backend'
    )
    self.mock_cloudbuild_client.return_value.list_builds.assert_called_once_with(
        project_id='fake_project'
    )
    self.assertEqual(actual_result, 'fake_version')


if __name__ == '__main__':
  absltest.main()

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

"""A client to interact with the gCloud SDK."""

import logging
import os
import subprocess

_LATEST_RUN_REVISION_CMD = (
    'run services describe {service}'
    ' --format=value(status.latestCreatedRevisionName) --platform=managed'
)
_REVISION_BUILD_ID_CMD = (
    'run revisions describe {revision} --format=value(labels.gcb-build-id)'
)
_BUILD_REF_NAME_CMD = (
    'builds describe {build} --format=value(substitutions.REF_NAME)'
)


class GcloudClient:
  """A client to interact with the gCloud SDK.

  Example Usage:
    gcloud_client = GcloudClient()
    backend_ref_name = gcloud_client.get_run_service_ref_name('backend')

  Attributes:
    project_id: The Google Cloud project ID.
    region: The Google Cloud Region, e.g. us-central1.
  """

  def __init__(self) -> None:
    """Initializes the client."""
    self._project_id = os.environ['GCP_PROJECT']
    self._region = os.environ['GCP_REGION']
    logging.info(
        'GCloud Client: Initialized in project %s and region %s',
        self._project_id,
        self._region,
    )

  def get_run_service_ref_name(self, service: str) -> str:
    """Returns the reference name of the build for the latest revision.

    In the case of keyword platofrm the eligible services are 'backend' or
    'frontend'. When deployed off the main branch the ref name defaults to the
    release version e.g. '2.1.0', when deployed off the dev branch the ref name
    defaults to 'dev'. The method will return an empty string if the passed
    service does not exist or any error occured.

    Args:
      service: The name of the Google Cloud Run service.
    """
    revision = self.run(
        cmd=_LATEST_RUN_REVISION_CMD.format(service=service),
        include_region=True,
    )
    build = self.run(
        cmd=_REVISION_BUILD_ID_CMD.format(revision=revision),
        include_region=True,
    )
    version = self.run(cmd=_BUILD_REF_NAME_CMD.format(build=build))
    return version

  def run(self, cmd: str, include_region=False) -> str:
    """Runs a gcloud command as subprocess.

    Args:
      cmd: The command to run.
      include_region: Whether or not to include the cloud region flag in the
        command.

    Returns:
      The output of the command.
    """
    cmd = f'gcloud {cmd} --project={self._project_id}'
    if include_region:
      cmd += f' --region={self._region}'
    process = subprocess.Popen(
        cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    out, err = process.communicate()

    if err:
      logging.warning(
          'GCloud Client: An error occured running command: %s: %s',
          cmd,
          err.strip(),
      )
      return ''
    logging.info('GCloud Client: Successfully ran command: %s', cmd)
    return out.strip()

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

"""A client to interact with the gCloud SDK."""

import logging
import os
from google.cloud.devtools import cloudbuild_v1


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
    self._cloud_build_client = cloudbuild_v1.CloudBuildClient()
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
    builds = self._cloud_build_client.list_builds(project_id=self._project_id)
    build_time = 0
    version = 'unknown'

    # TODO: b/314440399 - The code below is a workaround to get the lastest
    # successful build for a service based on the service name. Ideally we could
    # use run_v2 (from google-cloud-run), but this isn't available
    # in third_party, yet. Until it is this is the best we can do right now.
    for build in builds:
      if build.status == cloudbuild_v1.Build.Status.SUCCESS:
        if build_time < int(build.finish_time.strftime('%s')):
          images = [image for image in build.results.images]
          for image in images:
            if image.name and service in image.name:
              build_time = int(build.finish_time.strftime('%s'))
              version = build.substitutions.get('REF_NAME')
              break
    return version

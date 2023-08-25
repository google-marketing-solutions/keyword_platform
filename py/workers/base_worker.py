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

"""Base Google Ads Worker."""


import abc

from absl import logging

from common import cloud_translation_client as cloud_translation_client_lib
from common import vertex_client as vertex_client_lib
from data_models import google_ads_objects as google_ads_objects_lib
from data_models import settings as settings_lib
from workers import worker_result


class WorkerError(Exception):
  """Error thrown when a worker encounters an error during execution."""


class BaseWorker(abc.ABC):
  """Base class for a Google Ads workers.

  Example implementation:

    class TranslationWorker(base_worker.BaseWorker):

      def execute(
          settings: Settings,
          google_ads_objects: GoogleAdsObjects) -> WorkerResult:
        # ... translate keywords
        logging.info('Worker complete: %s', self.name)
        return WorkerResult(status=Status.SUCCESS,
                            keywords_modified=...)
  """

  def __init__(
      self,
      cloud_translation_client: cloud_translation_client_lib.CloudTranslationClient,
      vertex_client: vertex_client_lib.VertexClient | None,
  ) -> None:
    """Initializes the Google Ads worker.

    Args:
      cloud_translation_client: An instance of the GCP Cloud Translation API
        client.
      vertex_client: An instance of the Vertex API client.
    """
    self._cloud_translation_client = cloud_translation_client
    self._vertex_client = vertex_client
    logging.info('Initialized worker: %s.', self.name)

  @abc.abstractmethod
  def execute(
      self,
      settings: settings_lib.Settings,
      google_ads_objects: google_ads_objects_lib.GoogleAdsObjects
  ) -> worker_result.WorkerResult:
    """Executes the logic to transform the google ads objects.

    Args:
      settings: The user settings, passed in via the UI.
      google_ads_objects: The Google Ads objects to transform.

    Returns:
      A summary of results based on the work done by this worker.
    """

  @property
  def name(self) -> str:
    """The name of this worker class."""
    return self.__class__.__name__

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

"""Defines the StorageClient class."""
import logging
import google.auth
from google.auth import compute_engine
from google.auth.transport import requests
from google.cloud import exceptions
from google.cloud import storage
from py.data_models import google_ads_objects as google_ads_objects_lib


_DEFAULT_URL_EXPIRATION_SECONDS = 3600


class StorageClient:
  """A client upload GoogleAdsObjects to a Google Cloud Storage bucket as CSVs.

  Example usage:
    storage_client = StorageClient(bucket_name, google_ads_objects)
    download_urls = storage_client.export_google_ads_objects_to_gcs()
  """

  def __init__(
      self,
      bucket_name: str,
      google_ads_objects: google_ads_objects_lib.GoogleAdsObjects,
      url_expiration_seconds: int = _DEFAULT_URL_EXPIRATION_SECONDS,
  ):
    """Initializes the StorageClient.

    Args:
      bucket_name: The GCS bucket to storage CSV files to.
      google_ads_objects: An instance of the GoogleAdsObjects data class.
      url_expiration_seconds: The number of seconds until download links expire.
    """
    credentials, project = google.auth.default()
    self._storage_client = storage.Client(
        credentials=credentials, project=project
    )
    auth_request = requests.Request()
    self._signing_credentials = compute_engine.IDTokenCredentials(
        auth_request,
        '',
        service_account_email=credentials.service_account_email,
    )
    self._bucket = self._storage_client.bucket(bucket_name)
    self._google_ads_objects = google_ads_objects
    self._url_expiration_seconds = url_expiration_seconds

  def export_google_ads_objects_to_gcs(self) -> list[str]:
    """Writes Google Ads Objects to Cloud Strage and returns download URLs.

    Returns:
      A list URL strings to download the generated CSV files.
    """
    download_urls = []
    for name, csv_data in self._google_ads_objects.get_csv_data().items():
      download_url = self._write_dataframe_to_cloud_storage(name, csv_data)
      logging.info('Download URL: %s', download_url)
      download_urls.append(download_url)
    return download_urls

  def _write_dataframe_to_cloud_storage(
      self, file_name: str, csv_data: str
  ) -> str:
    """Writes a datframe to a cloud storage bucket and returns a download link.

    The dataframe contents are transformed to CSV before writing. The
    generated download link will be available for 1h.

    Args:
      file_name: The name of the file to be written.
      csv_data: The csv data to use for the operation.

    Returns:
      A URL string to download the generated CSV file.

    Raises:
      ClientError: If the dataframe data could not be written to GCS.
    """
    try:
      blob = self._bucket.blob(file_name)
      blob.upload_from_string(data=csv_data, content_type='text/csv')
      logging.info('Uploaded %s to bucket %s', file_name, self._bucket.name)
    except exceptions.ClientError as client_error:
      logging.exception(
          'Could not write CSV file: %s to GCS bucket %s',
          file_name,
          self._bucket.name,
      )
      raise client_error
    return blob.generate_signed_url(
        expiration=self._url_expiration_seconds,
        credentials=self._signing_credentials,
        version='v4',
    )

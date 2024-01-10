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

"""Defines the StorageClient class."""
import logging
import google.auth
from google.auth import compute_engine
from google.auth.transport import requests
from google.cloud import exceptions
from google.cloud import storage
import pandas as pd
from data_models import google_ads_objects as google_ads_objects_lib


_DEFAULT_URL_EXPIRATION_SECONDS = 3600
_STORAGE_FILE_TYPES = ['csv', 'xlsx']


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
      multiple_templates: bool = False,
  ):
    """Initializes the StorageClient.

    Args:
      bucket_name: The GCS bucket to storage CSV files to.
      google_ads_objects: An instance of the GoogleAdsObjects data class.
      url_expiration_seconds: The number of seconds until download links expire.
      multiple_templates: Whether or not to slit template CSVs into multiples.
    """
    credentials, project = google.auth.default()
    self._storage_client = storage.Client(
        credentials=credentials, project=project
    )
    auth_request = requests.Request()
    credentials.refresh(request=auth_request)
    self._signing_credentials = compute_engine.IDTokenCredentials(
        auth_request,
        '',
        service_account_email=credentials.service_account_email,
    )
    self._bucket_name = bucket_name
    self._bucket = self._storage_client.bucket(bucket_name)
    self._google_ads_objects = google_ads_objects
    self._url_expiration_seconds = url_expiration_seconds
    self._multiple_templates = multiple_templates

  def export_google_ads_objects_to_gcs(self) -> dict[str, list[str]]:
    """Writes Google Ads Objects to Cloud Strage and returns download URLs.

    Returns:
      A list URL strings to download the generated CSV files.
    """
    data_dict = (
        self._google_ads_objects.get_multiple_dataframes()
        if self._multiple_templates
        else self._google_ads_objects.get_combined_dataframe()
    )
    download_urls = dict()
    for file_type in _STORAGE_FILE_TYPES:
      download_urls[file_type] = []
      for name, data in data_dict.items():
        download_url = self._write_dataframe_to_cloud_storage(
            name, data, file_type
        )
        logging.info('Download URL: %s', download_url)
        download_urls[file_type].append(download_url)
    return download_urls

  def _write_dataframe_to_cloud_storage(
      self, file_name: str, df: pd.DataFrame, file_type: str
  ) -> str:
    """Writes a datframe to a cloud storage bucket and returns a download link.

    The dataframe contents are transformed to the passed file type before
    writing. The generated download links will be available for 1h.

    Args:
      file_name: The name of the file to be written.
      df: The dataframe data to use for the operation.
      file_type: The filetype to produce.

    Returns:
      A download URL string.

    Raises:
      ClientError: If the dataframe data could not be written to GCS.
    """
    try:
      file_name = f'{file_name}.{file_type}'
      blob = self._bucket.blob(file_name)
      if file_type == 'csv':
        data = df.to_csv(index=False, encoding='utf-8')
        blob.upload_from_string(data=data, content_type='text/csv')
      elif file_type == 'xlsx':
        blob.upload_from_string('')
        with pd.ExcelWriter(f'gs://{self._bucket_name}/{file_name}') as writer:
          df.to_excel(writer, sheet_name='Sheet1', index=False)
      logging.info('Uploaded %s to bucket %s', file_name, self._bucket.name)
      return blob.generate_signed_url(
          expiration=self._url_expiration_seconds,
          credentials=self._signing_credentials,
          version='v4',
      )
    except exceptions.ClientError:
      logging.exception(
          'Could not write file: %s to GCS bucket %s',
          file_name,
          self._bucket.name,
      )
      raise

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

"""Tests for storage_client."""

from unittest import mock

import google.auth
from google.cloud import exceptions
from google.cloud import storage

from absl.testing import absltest
from common import storage_client as storage_client_lib
from data_models import google_ads_objects as google_ads_objects_lib
from data_models import keywords as keywords_lib


_KEYWORDS_GOOGLE_ADS_API_RESPONSE = [[{
    'results': [
        {
            'customer': {'resourceName': 'customers/123', 'id': '123'},
            'campaign': {
                'resourceName': 'customers/123/campaigns/456',
                'advertisingChannelType': 'SEARCH',
                'biddingStrategyType': 'TARGET_SPEND',
                'name': 'Gmail Test Campaign',
            },
            'adGroup': {
                'resourceName': 'customers/123/adGroups/789',
                'name': 'Ad group 1',
            },
            'adGroupCriterion': {
                'resourceName': 'customers/123/adGroupCriteria/789~1112',
                'keyword': {'matchType': 'BROAD', 'text': 'e mail'},
            },
            'keywordView': {
                'resourceName': 'customers/123/keywordViews/789~1112'
            },
        },
        {
            'customer': {'resourceName': 'customers/123', 'id': '123'},
            'campaign': {
                'resourceName': 'customers/123/campaigns/456',
                'advertisingChannelType': 'SEARCH',
                'biddingStrategyType': 'TARGET_SPEND',
                'name': 'Gmail Test Campaign',
            },
            'adGroup': {
                'resourceName': 'customers/123/adGroups/789',
                'name': 'Ad group 1',
            },
            'adGroupCriterion': {
                'resourceName': 'customers/123/adGroupCriteria/789~1314',
                'keyword': {'matchType': 'BROAD', 'text': 'fast'},
            },
            'keywordView': {
                'resourceName': 'customers/123/keywordViews/789~1314'
            },
        },
    ],
    'fieldMask': (
        'customer.id,campaign.name,campaign.advertisingChannelType,'
        'campaign.biddingStrategyType,adGroup.name,'
        'adGroupCriterion.keyword.text,'
        'adGroupCriterion.keyword.matchType'
    ),
    'requestId': 'fake_req_id',
}]]

_FAKE_KEYWORDS_CSV = (
    'Action,Customer ID,Campaign,Ad group,Keyword,Original Keyword,Match'
    ' Type,Keyword status,Labels,Updates applied\nAdd,Enter customer ID,Gmail'
    ' Test Campaign,Ad group 1,e mail,e mail,BROAD,Paused,Keyword'
    ' Translator,[]\nAdd,Enter customer ID,Gmail Test Campaign,Ad group'
    ' 1,fast,fast,BROAD,Paused,Keyword Translator,[]\n'
)

_FAKE_BUCKET_NAME = 'fake_bucket_name'


class StorageClientTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.mock_credentials = mock.create_autospec(
        google.auth.credentials.Credentials
    )
    self.mock_credentials.service_account_email = 'fake_service_account_email'
    self.mock_auth = self.enter_context(
        mock.patch.object(
            google.auth,
            'default',
            autospec=True,
            return_value=(self.mock_credentials, ''),
        )
    )
    self.storage_client_mock = self.enter_context(
        mock.patch.object(storage, 'Client', autospec=True)
    )
    self.mock_bucket = mock.create_autospec(storage.Bucket)
    self.mock_blob = mock.create_autospec(storage.Blob)
    self.mock_bucket.return_value = self.mock_blob
    self.mock_bucket.blob.return_value = self.mock_blob
    self.mock_bucket.name = _FAKE_BUCKET_NAME
    self.mock_blob.generate_signed_url.return_value = 'http://keywords'
    self.storage_client_mock.return_value.bucket.return_value = self.mock_bucket
    self.google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        keywords=keywords_lib.Keywords(_KEYWORDS_GOOGLE_ADS_API_RESPONSE),
    )

  @mock.patch('pandas.DataFrame.to_excel', autospec=True)
  def test_export_google_ads_objects(self, mock_df_to_excel):
    del mock_df_to_excel
    expected_urls = {
        'csv': ['http://keywords'],
        'xlsx': ['http://keywords'],
    }
    with mock.patch('pandas.ExcelWriter', autospec=True):
      actual_urls = storage_client_lib.StorageClient(
          _FAKE_BUCKET_NAME, self.google_ads_objects
      ).export_google_ads_objects_to_gcs()

      self.mock_blob.upload_from_string.assert_has_calls([
          mock.call(data=_FAKE_KEYWORDS_CSV, content_type='text/csv'),
          mock.call(''),
      ])

      self.assertEqual(self.mock_blob.generate_signed_url.call_count, 2)
      self.assertEqual(actual_urls, expected_urls)

  @mock.patch('pandas.DataFrame.to_excel', autospec=True)
  def test_export_google_ads_objects_multiple_templates(self, mock_df_to_excel):
    del mock_df_to_excel
    mock_google_ads_objects = google_ads_objects_lib.GoogleAdsObjects(
        keywords=mock.MagicMock(), campaigns=mock.MagicMock()
    )
    expected_urls = {
        'csv': ['http://keywords', 'http://keywords'],
        'xlsx': ['http://keywords', 'http://keywords'],
    }
    with mock.patch('pandas.ExcelWriter', autospec=True):
      actual_urls = storage_client_lib.StorageClient(
          _FAKE_BUCKET_NAME, mock_google_ads_objects, multiple_templates=True
      ).export_google_ads_objects_to_gcs()

      self.mock_blob.upload_from_string.assert_has_calls([
          mock.call(data=mock.ANY, content_type='text/csv'),
          mock.call(data=mock.ANY, content_type='text/csv'),
          mock.call(''),
          mock.call(''),
      ])

      self.assertEqual(self.mock_blob.generate_signed_url.call_count, 4)
      self.assertEqual(actual_urls, expected_urls)

  def test_export_google_ads_object_raises_exception(self):
    self.mock_blob.upload_from_string.side_effect = exceptions.ClientError('')

    with self.assertRaises(exceptions.ClientError):
      storage_client_lib.StorageClient(
          _FAKE_BUCKET_NAME, self.google_ads_objects
      ).export_google_ads_objects_to_gcs()

  @mock.patch.object(google_ads_objects_lib, 'GoogleAdsObjects', autospec=True)
  def test_export_google_ads_objects_combined(self, mock_google_ads_objects):
    storage_client_lib.StorageClient(
        _FAKE_BUCKET_NAME, mock_google_ads_objects, multiple_templates=False
    ).export_google_ads_objects_to_gcs()

    mock_google_ads_objects.get_combined_dataframe.assert_called_once_with()


if __name__ == '__main__':
  absltest.main()

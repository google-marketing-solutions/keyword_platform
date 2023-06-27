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

"""Tests for storage_client."""

from unittest import mock

from google.cloud import exceptions
from google.cloud import storage

from py.common import storage_client as storage_client_lib
from py.data_models import google_ads_objects as google_ads_objects_lib
from py.data_models import keywords as keywords_lib
from absl.testing import absltest


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
    ' Type,Keyword status,Updates applied\nAdd,Enter customer ID,Gmail Test'
    ' Campaign,Ad group 1,e mail,e mail,BROAD,Paused,[]\nAdd,Enter customer'
    ' ID,Gmail Test Campaign,Ad group 1,fast,fast,BROAD,Paused,[]\n'
)

_FAKE_BUCKET_NAME = 'fake_bucket_name'


class StorageClientTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
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

  def test_export_google_ads_objects(self):
    expected_urls = [
        'http://keywords',
    ]

    actual_urls = storage_client_lib.StorageClient(
        _FAKE_BUCKET_NAME, self.google_ads_objects
    ).export_google_ads_objects_to_gcs()

    self.mock_blob.upload_from_string.assert_called_once_with(
        data=_FAKE_KEYWORDS_CSV, content_type='text/csv'
    )
    self.mock_blob.generate_signed_url.assert_called_once_with(
        expiration=3600, version='v4'
    )
    self.assertEqual(actual_urls, expected_urls)

  def test_export_google_ads_object_raises_exception(self):
    self.mock_blob.upload_from_string.side_effect = exceptions.ClientError('')

    with self.assertRaises(exceptions.ClientError):
      storage_client_lib.StorageClient(
          _FAKE_BUCKET_NAME, self.google_ads_objects
      ).export_google_ads_objects_to_gcs()


if __name__ == '__main__':
  absltest.main()

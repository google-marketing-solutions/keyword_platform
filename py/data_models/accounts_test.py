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

"""Tests for the Accounts data model class."""

from absl.testing import absltest
from absl.testing import parameterized
from data_models import accounts as accounts_lib

# TODO()
_GOOGLE_ADS_RESPONSE = [{
    'results': [
        {
            'customerClient': {
                'resourceName': (
                    'customers/8056520078/customerClients/5459155099'
                ),
                'descriptiveName': 'Account 1',
                'id': '5459155099',
            }
        },
        {
            'customerClient': {
                'resourceName': (
                    'customers/8056520078/customerClients/8647404629'
                ),
                'id': '8647404629',
            }
        },
    ],
    'fieldMask': 'customerClient.id,customerClient.descriptiveName',
    'requestId': 'fake_req_id',
}]

_EMPTY_GOOGLE_ADS_RESPONSE = [{
    'results': [],
    'fieldMask': 'customerClient.id,customerClient.descriptiveName',
    'requestId': 'fake_req_id',
}]

_EXPECTED_LIST = [
    accounts_lib.Account(
        id='5459155099', name='Account 1', display_name='[5459155099] Account 1'
    ),
    accounts_lib.Account(
        id='8647404629',
        name='[NO NAME SET]',
        display_name='[8647404629] [NO NAME SET]',
    ),
]


class AccountsTest(parameterized.TestCase):

  @parameterized.named_parameters(
      {
          'testcase_name': 'response_with_account_data',
          'google_ads_api_response': _GOOGLE_ADS_RESPONSE,
          'expected_list': _EXPECTED_LIST,
      },
      {
          'testcase_name': 'no_account_data',
          'google_ads_api_response': _EMPTY_GOOGLE_ADS_RESPONSE,
          'expected_list': [],
      },
  )
  def test_accounts_list(self, google_ads_api_response, expected_list):
    accounts = accounts_lib.Accounts(google_ads_api_response)
    actual_list = accounts.accounts_list

    self.assertEqual(actual_list, expected_list)
if __name__ == '__main__':
  absltest.main()

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

from unittest import mock

import google.generativeai as genai

from absl.testing import absltest
from common import palm_client as palm_client_lib

_MODEL = 'models/text-bison-001'


class PalmClientTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.enter_context(mock.patch.object(genai, 'configure', autospec=True))
    mock_response = mock.MagicMock()
    mock_response.result = (
        "['This texts needs to be shortened because it is too long.']"
    )
    self._mock_generate_text = self.enter_context(
        mock.patch.object(
            genai, 'generate_text', autospec=True, return_value=mock_response
        )
    )

  def test_shorten_text_to_char_limit(self):
    fake_text_list = [
        'This texts needs to be shortened because it is too long.',
    ]
    test_char_limit = 50
    expected_prompt = f"""
        For each of the following list elements, shorten the sentences to be
        under {test_char_limit} characters only if it is above {test_char_limit}
        characters, retain the given sentence otherwise:

          {fake_text_list}

        Return just a python list.
      """
    expected_result = [
        'This texts needs to be shortened because it is too long.'
    ]
    palm_client = palm_client_lib.PalmClient('api_key')

    actual_result = palm_client.shorten_text_to_char_limit(
        fake_text_list, 'en', 50
    )

    self._mock_generate_text.assert_called_once_with(
        model=_MODEL,
        prompt=expected_prompt,
        candidate_count=1,
        temperature=0,
    )
    self.assertEqual(actual_result, expected_result)

  def test_shorten_text_to_char_limit_logs_warning_unsupported_language(
      self,
  ):
    palm_client = palm_client_lib.PalmClient('api_key')

    with self.assertLogs() as logs:
      palm_client.shorten_text_to_char_limit(['some_text'], 'unsupported', 50)

    self.assertEqual(
        logs.output,
        [
            'WARNING:absl:Language unsupported not supported.'
            ' Returning original text list.'
        ],
    )


if __name__ == '__main__':
  absltest.main()

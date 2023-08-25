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

import os
from unittest import mock

import vertexai
from vertexai.language_models import TextGenerationModel

from absl.testing import absltest
from common import vertex_client as vertex_client_lib


class VertexClientTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    self.enter_context(mock.patch.object(vertexai, 'init', autospec=True))
    self.enter_context(
        mock.patch.object(
            os,
            'environ',
            autospec=True,
            side_effect=['fake_project', 'fake_region'],
        )
    )
    self.mock_model = self.enter_context(
        mock.patch.object(
            TextGenerationModel,
            'from_pretrained',
            autospec=True,
        )
    )
    mock_response = mock.MagicMock()
    mock_response.text = (
        "['This texts needs to be shortened because it is too long.']"
    )
    self.mock_model.return_value.predict.return_value = mock_response

  def test_shorten_text_to_char_limit(self):
    fake_text_list = [
        'This texts needs to be shortened because it is too long.',
    ]
    test_char_limit = 50
    expected_prompt = f"""
        Make each of the following sentences shorter

        Sentences:
          {fake_text_list}

        Do so until this Python function returns true:
          all(len(sentence) < {test_char_limit} for shortened_sentence in Sentences)

        Shortened sentences list:
      """
    expected_result = [
        'This texts needs to be shortened because it is too long.'
    ]
    vertex_client = vertex_client_lib.VertexClient()

    actual_result = vertex_client.shorten_text_to_char_limit(
        fake_text_list, 'en', 50
    )

    self.mock_model.return_value.predict.assert_has_calls([
        mock.call('Are you there?'),
        mock.call(expected_prompt, temperature=0, top_p=0.8, top_k=1),
    ])
    self.assertEqual(actual_result, expected_result)

  def test_shorten_text_to_char_limit_logs_warning_unsupported_language(
      self,
  ):
    vertex_client = vertex_client_lib.VertexClient()

    with self.assertLogs() as logs:
      vertex_client.shorten_text_to_char_limit(['some_text'], 'unsupported', 50)

    self.assertEqual(
        logs.output,
        [
            'WARNING:absl:Language unsupported not supported.'
            ' Returning original text list.'
        ],
    )

  def test_shorten_text_to_char_limit_in_batches(self):
    fake_text_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
    test_char_limit = 50
    test_language_code = 'en'

    vertex_client = vertex_client_lib.VertexClient()
    with mock.patch.object(
        vertex_client,
        '_shorten_text_to_char_limit',
        autospec=True,
    ) as mock_shorten_text_to_char_limit:
      vertex_client.shorten_text_to_char_limit(
          fake_text_list, test_language_code, test_char_limit
      )
      mock_shorten_text_to_char_limit.assert_has_calls([
          mock.call(
              fake_text_list[0:6],
              test_language_code,
              test_char_limit,
          ),
          mock.call(fake_text_list[6:11], test_language_code, test_char_limit),
      ])


if __name__ == '__main__':
  absltest.main()

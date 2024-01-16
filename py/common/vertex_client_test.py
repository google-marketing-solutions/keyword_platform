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

import os
import time
from unittest import mock

import google.api_core
import vertexai
from vertexai.language_models import TextGenerationModel

from absl.testing import absltest
from common import vertex_client as vertex_client_lib

_FAKE_TEXT = 'This texts needs to be shortened because it is too long.'

_TEST_CHAR_LIMIT = 30


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
    self.mock_response = mock.MagicMock()
    self.mock_response.text = 'This text needs to be shorter.'

  def test_shorten_text_to_char_limit(self):
    self.mock_model.return_value.predict.return_value = self.mock_response
    expected_prompt = f"""
          Make the following sentence simple and short:

          {_FAKE_TEXT}
        """
    expected_result = ['This text needs to be shorter.']
    vertex_client = vertex_client_lib.VertexClient()

    actual_result = vertex_client.shorten_text_to_char_limit(
        [_FAKE_TEXT], 'en', _TEST_CHAR_LIMIT
    )

    self.mock_model.return_value.predict.assert_has_calls([
        mock.call('Are you there?'),
        mock.call(
            expected_prompt,
            temperature=0.4,
            top_p=0.9,
            top_k=40,
            max_output_tokens=8,
        ),
    ])
    self.assertEqual(actual_result, expected_result)
    self.assertEqual(vertex_client.get_genai_characters_sent(), 133)


if __name__ == '__main__':
  absltest.main()

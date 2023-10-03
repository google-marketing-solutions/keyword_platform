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

"""Defines the VertexClient class.

See class doctring for more details.
"""
from concurrent import futures
import math
import os

from absl import logging
import google.api_core
import vertexai
from vertexai.language_models import TextGenerationModel, TextGenerationResponse

from common import utils


_MODEL = 'text-bison@001'

AVAILABLE_LANGUAGES = frozenset(['en'])

_PROMPT_MAP = {
    'en': 'Make the following sentence simple and short:',
    'de': 'Mache den folgenden Satz einfach und kurz:',
    'es': 'Haz la siguiente oración simple y corta.:',
    'ko': '다음 문장을 간단하고 짧게 만드세요.',
    'hi': 'निम्नलिखित वाक्य को सरल एवं संक्षिप्त बनायें:',
    'zh': '让下面的句子变得简单、简短：',
}


class VertexClient:
  """A client to make requests to the Vertex API.

  This requires an api_key from the Cloud Platform Console.

  Example usage:
    vertex_client = VertexClient()
    shortened_text = vertex_client.shorten_text_to_char_limit(
      ['Some long headline...'], 'en', 50)
  """

  def __init__(self) -> None:
    vertexai.init(
        project=os.environ['GCP_PROJECT'], location=os.environ['GCP_REGION']
    )
    self._client = TextGenerationModel.from_pretrained(_MODEL)
    # Making a call in __init__ to ensure initialization of VertexClient fails
    # if the GCP_PROJECT was not allowlisted to use Vertex LLMs.
    self._client.predict('Are you there?')
    self._genai_characters_sent = 0

  def shorten_text_to_char_limit(
      self, text_list: list[str], language_code: str, char_limit: int
  ) -> list[str]:
    """Shortens a list of strings under the provided character limit.

    To prevent sending too long of a string to the model, we split the list of
    strings to process into smaller chunks and process them in parallel.

    Args:
      text_list: A list of strings to shorten.
      language_code: The language of the text.
      char_limit: The character limit to shorten the text to.

    Returns:
      The a list of strings that are under the passed character limit. If the
      passed language code isn't supported the original text list is returned.
    """
    result = []
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
      generator = executor.map(
          lambda text: self._shorten_text_to_char_limit(
              text, language_code, char_limit
          ),
          text_list,
      )
    for item in generator:
      if isinstance(item, str):
        result.append(item)
    return result

  def get_genai_characters_sent(self) -> int:
    """Gets the number of characters sent to Vertex API in this instance."""
    return self._genai_characters_sent

  def _shorten_text_to_char_limit(
      self, text: str, language_code: str, char_limit: int
  ) -> str:
    """Shortens a text under the provided character limit.

    If a text list element is equal or under the character limit already, the
    original list element will be returned. The function prompts an LLM and
    descreases the maximum number of output tokens gradually until the output
    is under the desired character limit. More details on the model can be found
    here:
    https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/text

    Args:
      text: The text to shorten.
      language_code: The language of the text.
      char_limit: The character limit to shorten the text to.

    Returns:
      The a string that is under the passed character limit.
    """
    shortened_text = text
    # One token has approximately 4 characters. This can be used to determine
    # an output token number to start with.
    start_output_tokens = math.ceil(char_limit / 4)
    output_tokens = start_output_tokens
    try:
      while len(shortened_text) > char_limit:
        parameters = {
            'temperature': 0.4,
            'top_p': 0.9,
            'top_k': 40,
            'max_output_tokens': output_tokens,
        }
        shorten_prompt = f"""
          {_PROMPT_MAP[language_code]}

          {text}
        """
        response = self._send_prompt_with_backoff(shorten_prompt, **parameters)
        self._genai_characters_sent += len(shorten_prompt)
        shortened_text = response.text
        # Decrease the max number of output tokens by 1 for the next iteration.
        output_tokens += -1
      logging.info(
          'Shortened text: "%s" to "%s" after %d iterations',
          text,
          shortened_text,
          start_output_tokens - output_tokens,
      )
    # Catching broadly here to ensure the generator is never stopped
    # prematurely.
    except utils.MaxRetriesExceededError as err:
      logging.error('Failed to shorten text: %s, returning original text.', err)
    return shortened_text

  @utils.exponential_backoff_retry(
      base_delay=2,
      back_off_factor=2,
      exceptions=[google.api_core.exceptions.ResourceExhausted],
  )
  def _send_prompt_with_backoff(
      self, prompt: str, **parameters
  ) -> TextGenerationResponse:
    """Sends a prompt to the LLM."""
    return self._client.predict(prompt, **parameters)
